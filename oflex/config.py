import yaml, os, collections, flask

class QueryRenderer:
  "poor man's ORM"

  def __init__(self, dialect):
    self.dialect = dialect
    self.wildcard = '?' if self.dialect == 'sqlite' else '%s'

  def select(self, table, sel_cols, wherecol):
    return f"select {', '.join(sel_cols)} from {table} where {wherecol} = {self.wildcard}"

  def update(self, table, setcol, wherecol):
    return f"update {table} set {setcol} = {self.wildcard} where {wherecol} = {self.wildcard}"

  def insert(self, table, cols):
    return f"insert into {table} ({', '.join(cols)}) values ({', '.join([self.wildcard] * len(cols))})"

def default_send_verify(email, verification_code):
  print('verify', flask.url_for('oflex.blueprint.get_verify', email=email, verification_code=verification_code, _external=True))

RAW_CONFIG = dict(
  queries=None,
  # named fields namedtuple for select + insert returning
  query_fields=dict(
    get_user_email=collections.namedtuple('get_user_email', 'auth_method pass_hash pass_salt userid'),
    get_user_email_ver=collections.namedtuple('get_user_email_ver', 'auth_method pass_hash pass_salt userid verified'),
    get_user_sms=collections.namedtuple('get_user_sms', 'auth_method userid username'),
    get_username=collections.namedtuple('get_username', 'username'),
  ),
  session_expiry=86400 * 90,
  # maximum size of connection pool
  maxconn=4,
  db_dialect='postgres',
  use_redis=True,
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
  username_name='Username',
  username_comment='(public)',
  # require_verification means to have 'verified' and 'verification_code' fields for email login
  require_verification=False,
  send_verification_email=default_send_verify,
  login_hook=lambda kind, row: None,
  event_hook=lambda kind, userid: None,
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
  tmp = RAW_CONFIG.copy() # this isn't a deep copy -- why am I bothering? what's RAW_CONFIG -> CONFIG about?
  assert tmp['db_dialect'] in ('postgres', 'sqlite')
  render = QueryRenderer(tmp['db_dialect'])
  if tmp['require_verification']:
    # ugh: this is going to cause problems someday
    tmp['query_fields']['get_user_email'] = tmp['query_fields']['get_user_email_ver']
  tmp['queries'] = dict(
    create_user_email=render.insert('users', ('userid', 'username', 'auth_method', 'email', 'pass_hash', 'pass_salt')),
    create_user_email_ver=render.insert('users', ('userid', 'username', 'auth_method', 'email', 'pass_hash', 'pass_salt', 'verification_code')),
    create_user_sms=render.insert('users', ('userid', 'auth_method', 'sms')),
    update_username=render.update('users', 'username', 'userid'),
    get_verify=render.select('users', ('verification_code', 'verified', 'pass_hash', 'userid'), 'email'),
    # note: get_* select queries are using namedtuple fields. so much ugly indirection here, just use an ORM
    get_user_email=render.select('users', tmp['query_fields']['get_user_email']._fields, 'email'),
    get_user_sms=render.select('users', tmp['query_fields']['get_user_sms']._fields, 'sms'),
    get_username=render.select('users', tmp['query_fields']['get_username']._fields, 'userid'),
  )
  CONFIG.update(tmp)

def getenv(name):
  "get env var with indirection"
  return os.environ[CONFIG['env'][name]]
