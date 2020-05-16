import flask, contextlib, os, redis, jinja2, time, sqlite3
from .config import render_config, CONFIG, getenv

def fetch1_abort(cur, status=404):
  "helper to flask.abort if DB query is empty"
  row = cur.fetchone()
  if row is None:
    flask.abort(status)
  return row

@contextlib.contextmanager
def withcon():
  if CONFIG['db_dialect'] == 'sqlite':
    con = sqlite3.connect(getenv('automig_con'))
    yield con
    con.commit()
  else:
    pool = flask.current_app.pool
    con = pool.getconn()
    try:
      yield con
      con.commit()
    finally:
      pool.putconn(con)

def init():
  render_config()
  app = flask.current_app
  if CONFIG['db_dialect'] == 'postgres':
    # todo: register postgres uuid
    import psycopg2.pool # delayed so this isn't a hard dep
    app.pool = psycopg2.pool.ThreadedConnectionPool(0, CONFIG['maxconn'], getenv('automig_con'))
  elif CONFIG['db_dialect'] == 'sqlite':
    assert os.path.exists(getenv('automig_con'))
  else:
    raise ValueError('unk dialect', CONFIG['db_dialect'])
  if CONFIG['use_redis']:
    app.redis = redis.Redis(getenv('redis'))
  if CONFIG['support_sms']:
    import twilio.rest # delayed so this isn't a hard dep
    app.twilio = twilio.rest.Client(getenv('twilio_sid'), getenv('twilio_token'))
  app.jinja_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), 'templates')]),
  ])
