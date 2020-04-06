import flask, uuid, json, scrypt, psycopg2.extras, os
from . import pool
from .config import CONFIG

APP = flask.Blueprint(__name__, 'oflex')

@APP.route('/login')
def get_login():
  return flask.render_template('login.htm')

def set_session(userid):
  sessionid = str(uuid.uuid4())
  flask.current_app.redis.setex(
    f'session-{sessionid}',
    CONFIG['session_expiry'],
    json.dumps({'userid': str(userid)})
  )
  flask.session['sessionid'] = sessionid
  return sessionid

@APP.route('/login/email', methods=['POST'])
def post_login_email():
  "login with email"
  form = flask.request.form
  with pool.withcon() as con, con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
    cur.execute(CONFIG['get_user_email'], (form['email'],))
    row = cur.fetchone()
    if row is None:
      # todo: flash
      return flask.redirect(flask.url_for('oflex.blueprint.get_login'))
  assert row.auth_method == 'email'
  if row.pass_hash.tobytes() != scrypt.hash(form['password'].encode(), row.pass_salt.tobytes()):
    # todo: flash
    return flask.redirect(flask.url_for('oflex.blueprint.get_login'))
  set_session(row.userid)
  return flask.redirect(flask.url_for(CONFIG['login_home']))

@APP.route('/join')
def get_join():
  return flask.render_template('join.htm')

@APP.route('/join/email', methods=['POST'])
def post_join_email():
  "create account with email / password"
  form = flask.request.form
  if not form['password']:
    flask.abort(flask.Response("Blank password not allowed", status=400))
  assert '@' in form['email'] and len(form['email']) < CONFIG['max_email']
  pass_salt = os.urandom(64)
  pass_hash = scrypt.hash(form['password'].encode(), pass_salt)
  with pool.withcon() as con, con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
    # todo: rate limiting
    # todo: clearer error for duplicate email
    cur.execute(CONFIG['create_user_email'], (form['username'], form['email'], pass_hash, pass_salt))
    row = cur.fetchone()
    set_session(row.userid)
  return flask.redirect(flask.url_for(CONFIG['login_home']))

@APP.route('/logout', methods=['POST'])
def post_logout():
  flask.session.clear()
  return flask.redirect(flask.url_for('oflex.blueprint.get_login'))
