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
values ({' '.join([self.wildcard] * len(cols))})"""

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
  queries=dict(
    # todo: make the SQL queries use named parameters
    create_user_email="""insert into {tab[users]} ({col[username]}, {col[auth_method]}, {col[email]}, {col[pass_hash]}, {col[pass_salt]})
      values (%(username)s, 'email', %(email)s, %(pass_hash)s, %(pass_salt)s)
      returning {col[userid]}""",
    # note: this doesn't use username because it's 'login or create', username is a separate step
    create_user_sms="insert into {tab[users]} ({col[auth_method]}, {col[sms]}) values ('sms', %(sms)s) returning {col[userid]}",
    get_user_email="select {col[auth_method]}, {col[pass_hash]}, {col[pass_salt]}, {col[userid]} from {tab[users]} where {col[email]} = %(email)s",
    get_user_sms='select {col[auth_method]}, {col[userid]}, {col[username]} from {tab[users]} where {col[sms]} = %(sms)s',
    get_username='select {col[username]} from {tab[users]} where {col[userid]} = %(userid)s',
    update_username='update {tab[users]} set {col[username]} = %(username)s where {col[userid]} = %(userid)s',
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
  tmp['queries'] = {
    key: val.format_map(tmp)
    for key, val in tmp['queries'].items()
  }
  assert tmp['db_dialect'] in ('postgres', 'sqlite')
  CONFIG.update(tmp)

def getenv(name):
  "get env var with indirection"
  return os.environ[CONFIG['env'][name]]
