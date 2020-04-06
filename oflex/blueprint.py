import flask, uuid, json, scrypt, psycopg2.extras
from . import pool
from .config import CONFIG

APP = flask.Blueprint(__name__, 'oflex')

@APP.route('/login')
def get_login():
  return flask.render_template('login.htm')

@APP.route('/login/email', methods=['POST'])
def post_login():
  "login with email"
  form = flask.request.form
  with pool.withcon() as con, con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
    cur.execute(CONFIG['get_user_email'], (form['email'],))
    row = cur.fetchone()
    if row is None:
      # todo: flash
      return flask.redirect(flask.url_for('oflex.get_login'))
  assert row.auth_method == 'email'
  if row.pass_hash.tobytes() != scrypt.hash(form['password'].encode(), row.pass_salt.tobytes()):
    # todo: flash
    return flask.redirect(flask.url_for('oflex.get_login'))
  sessionid = str(uuid.uuid4())
  flask.current_app.redis.setex(
    f'session-{sessionid}',
    CONFIG['session_expiry'],
    json.dumps({'userid': str(row.userid)})
  )
  flask.session['sessionid'] = sessionid
  return flask.redirect(flask.url_for(CONFIG['login_home'])) # todo: home instead
