import yaml, os, collections

class QueryRenderer:
  "poor man's ORM"
  def __init__(self, col, tab, dialect):
    self.col = col
    self.tab = tab
    self.dialect = dialect

  @property
  def wildcard(self):
    # sqlite driver doesn't support named param substitution.
    return '?' if self.dialect == 'sqlite' else '%s'

  def select(self, table, sel_cols, wherecol):
    rendered_cols = ', '.join(self.col[col] for col in sel_cols)
    return f"""select {rendered_cols} from {self.tab[table]}
where {self.col[wherecol]} = {self.wildcard}"""

  def update(self, table, setcol, wherecol):
    return f"""update {self.tab[table]}
set {self.col[setcol]} = {self.wildcard}
where {self.col[wherecol]} = {self.wildcard}"""

  def insert(self, table, cols):
    return f"""insert into {self.tab[table]} ({', '.join(self.col[col] for col in cols)})
values ({', '.join([self.wildcard] * len(cols))})"""

RAW_CONFIG = dict(
  # tables
  tab=dict(users='users'),
  # columns
  col=dict(
    username='username',
    auth_method='auth_method',
    email='email',
    pass_hash='pass_hash',
    pass_salt='pass_salt',
    userid='userid',
    sms='sms',
  ),
  queries=None,
  # named fields namedtuple for select + insert returning
  query_fields=dict(
    get_user_email=collections.namedtuple('get_user_email', 'auth_method pass_hash pass_salt userid'),
    get_user_sms=collections.namedtuple('get_user_sms', 'auth_method userid username'),
    get_username=collections.namedtuple('get_username', 'username'),
  ),
  session_expiry=86400 * 90,
  # maximum size of connection pool
  maxconn=4,
  db_dialect='postgres',
  local_redis=False,
  env=dict(
    # name of environment variable that holds postgres connection string
    automig_con='AUTOMIG_CON',
    redis='REDIS_HOST',
    twilio_sid='TWILIO_SID',
    twilio_token='TWILIO_TOKEN',
    twilio_from='TWILIO_FROM',
  ),
  # route to visit after successful login
  login_home='home',
  # maxlen
  max_email=400,
  support_sms=True,
  appname='oflex',
  # username comment is editable so sites can give guidance about how this will be used
  username_comment='(public)',
)

# note: this is a dict rather than None so import refs work
CONFIG = {}

def load_config(path='oflex.yml'):
  "load config from file"
  # todo: deep merge instead of update
  RAW_CONFIG.update(yaml.load(open(path)))

def render_config():
  "render queries"
  global CONFIG
  tmp = RAW_CONFIG.copy() # careful -- this isn't a deep copy
  assert tmp['db_dialect'] in ('postgres', 'sqlite')
  render = QueryRenderer(tmp['col'], tmp['tab'], tmp['db_dialect'])
  tmp['queries'] = dict(
    create_user_email=render.insert('users', ('userid', 'username', 'auth_method', 'email', 'pass_hash', 'pass_salt')),
    create_user_sms=render.insert('users', ('userid', 'auth_method', 'sms')),
    update_username=render.update('users', 'username', 'userid'),
    # note: get_* select queries are using namedtuple fields. so much ugly indirection here, just use an ORM
    get_user_email=render.select('users', tmp['query_fields']['get_user_email']._fields, 'email'),
    get_user_sms=render.select('users', tmp['query_fields']['get_user_sms']._fields, 'sms'),
    get_username=render.select('users', tmp['query_fields']['get_username']._fields, 'userid'),
  )
  CONFIG.update(tmp)

def getenv(name):
  "get env var with indirection"
  return os.environ[CONFIG['env'][name]]
