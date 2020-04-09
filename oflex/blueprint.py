import flask, uuid, json, scrypt, psycopg2.extras, os, phonenumbers, random
from . import pool
from .config import CONFIG, getenv

APP = flask.Blueprint(__name__, 'oflex')

@APP.route('/login')
def get_login():
  return flask.render_template('login.htm', support_sms=CONFIG['support_sms'])

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
    cur.execute(
      CONFIG['queries']['get_user_email'],
      {'email': form['email']}
    )
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
  return flask.render_template('join.htm', support_sms=CONFIG['support_sms'])

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
    cur.execute(
      CONFIG['queries']['create_user_email'],
      {'username': form['username'], 'email': form['email'], 'pass_hash': pass_hash, 'pass_salt': pass_salt}
    )
    row = cur.fetchone()
    set_session(row.userid)
  return flask.redirect(flask.url_for(CONFIG['login_home']))

@APP.route('/logout', methods=['POST'])
def post_logout():
  flask.session.clear()
  return flask.redirect(flask.url_for('oflex.blueprint.get_login'))

@APP.route('/login/sms')
def get_login_sms():
  assert CONFIG['support_sms']
  return flask.render_template('sms.htm')

def send_sms_code(number):
  "aborts if there's a problem. doesn't hit twilio in FLASK_DEBUG mode"
  try: number = phonenumbers.parse(number, 'US')
  except Exception as err:
    flask.abort(flask.Response(f"Problem parsing phone number: {str(err)}", status=400))
  if not phonenumbers.is_valid_number(number):
    flask.abort(flask.Response("Invalid number", status=400))
  if number.country_code != 1:
    flask.abort(flask.Response("Non-US number -- we only support US phone numbers for now. Contact support to talk about other use-cases.", status=400))
  flask.session['sms'] = normal = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
  secret_code = '%06d' % int(random.random() * 1e6)
  if os.environ.get('FLASK_DEBUG') == '1':
    print('fake local twilio:', secret_code)
  else:
    # todo: rate limit
    flask.current_app.twilio.messages.create(
      body=f"Your {CONFIG['appname']} verification code is: {secret_code}.\n\nReply STOP to unsubscribe.",
      from_=getenv('twilio_from'),
      to=normal,
    )
  flask.current_app.redis.setex(f'sms-{normal}', 60 * 30, secret_code)

@APP.route('/login/sms', methods=['POST'])
def post_login_sms():
  assert CONFIG['support_sms']
  send_sms_code(flask.request.form['sms'])
  return flask.redirect(flask.url_for('oflex.blueprint.get_confirm'))

@APP.route('/login/sms/confirm')
def get_confirm():
  assert CONFIG['support_sms']
  return flask.render_template('confirm.htm')

@APP.route('/login/sms/confirm', methods=['POST'])
def post_confirm():
  assert CONFIG['support_sms']
  raise NotImplementedError
  normal = flask.session['sms']
  received_code = flask.request.json['code']
  key = f'sms-{normal}'
  correct_code = flask.current_app.redis.get(key)
  if received_code.encode() == correct_code:
    set_user_session(normal)
    flask.current_app.redis.delete(key)
    return flask.jsonify({'ok': True})
  else:
    return flask.jsonify({'ok': False, 'error': "Bad code. Try again or request another code"})
