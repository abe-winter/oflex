import flask, psycopg2.pool, psycopg2.extras, contextlib, os, redis, jinja2, twilio.rest
from .config import render_config, CONFIG, getenv

def fetch1_abort(cur, status=404):
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

def init():
  render_config()
  app = flask.current_app
  # todo: register postgres uuid
  app.pool = psycopg2.pool.ThreadedConnectionPool(0, CONFIG['maxconn'], getenv('pg'))
  app.redis = redis.Redis(getenv('redis'))
  if CONFIG['support_sms']:
    app.twilio = twilio.rest.Client(getenv('twilio_sid'), getenv('twilio_token'))
  app.jinja_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), 'templates')]),
  ])
