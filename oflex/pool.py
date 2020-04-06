import flask, psycopg2.pool, psycopg2.extras, contextlib, os, redis, jinja2
from .config import CONFIG

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
  app = flask.current_app
  # todo: register postgres uuid
  app.pool = psycopg2.pool.ThreadedConnectionPool(0, CONFIG['maxconn'], os.environ[CONFIG['env_pg_cx']])
  app.redis = redis.Redis(CONFIG['env_redis_cx'])
  app.jinja_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), 'templates')]),
  ])
