import yaml

CONFIG = dict(
  create_user_email="insert into users (username, auth_method, email, pass_hash, pass_salt) values (%s, 'email', %s, %s, %s) returning userid",
  create_user_sms="insert into users (username, auth_method, sms) values (%s, 'sms', %s) returning userid",
  get_user_email="select auth_method, pass_hash, pass_salt, userid from users where email = %s",
  session_expiry=86400 * 90,
  # maximum size of connection pool
  maxconn=4,
  # name of environment variable that holds postgres connection string
  env_pg_cx='AUTOMIG_CON',
  env_redis_cx='REDIS_HOST',
  # route to visit after successful login
  login_home='home',

)

def load_config(path='oflex.yml'):
  "load config from file"
  CONFIG.update(yaml.load(open(path)))
