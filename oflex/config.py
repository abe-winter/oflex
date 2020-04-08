import yaml, os

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
    create_user_sms="insert into {tab[users]} ({col[username]}, {col[auth_method]}, {col[sms]}) values (%(username)s, 'sms', %(sms)s) returning {col[userid]}",
    get_user_email="select {col[auth_method]}, {col[pass_hash]}, {col[pass_salt]}, {col[userid]} from {tab[users]} where {col[email]} = %(email)s",
  ),
  session_expiry=86400 * 90,
  # maximum size of connection pool
  maxconn=4,
  env=dict(
    # name of environment variable that holds postgres connection string
    pg='AUTOMIG_CON',
    redis='REDIS_HOST',
    twilio_sid='TWILIO_SID',
    twilio_token='TWILIO_TOKEN',
  ),
  # route to visit after successful login
  login_home='home',
  # maxlen
  max_email=400,
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
  CONFIG.update(tmp)

def getenv(name):
  "get env var with indirection"
  return os.environ(CONFIG['env'][name])
