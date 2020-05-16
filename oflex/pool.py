import flask, contextlib, os, redis, jinja2, time
from .config import render_config, CONFIG, getenv

def fetch1_abort(cur, status=404):
  "helper to flask.abort if DB query is empty"
  row = cur.fetchone()
  if row is None:
    flask.abort(status)
  return row

@contextlib.contextmanager
def withcon():
  pool = flask.current_app.pool
  con = pool.getconn()
  try:
    yield con
    con.commit()
  finally:
    pool.putconn(con)

class LocalRedis(dict):
  "barebones redis clone for in-mem"

  def setex(self, key, expiry_seconds, value):
    self[key] = (time.time() + expiry_seconds), value

  def get(self, key):
    row = self.get(key)
    if not row:
      return None
    expiry, value = row
    if expiry is not None and expiry >= time.time():
      del self[key]
      return None
    return value

  def delete(self, key):
    return self.pop(key, None)

def init():
  render_config()
  app = flask.current_app
  import psycopg2.pool # delayed so this isn't a hard dep
  # todo: register postgres uuid
  app.pool = psycopg2.pool.ThreadedConnectionPool(0, CONFIG['maxconn'], getenv('automig_con'))
  app.redis = LocalRedis() if CONFIG['local_redis'] else redis.Redis(getenv('redis'))
  if CONFIG['support_sms']:
    import twilio.rest # delayed so this isn't a hard dep
    app.twilio = twilio.rest.Client(getenv('twilio_sid'), getenv('twilio_token'))
  app.jinja_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), 'templates')]),
  ])
