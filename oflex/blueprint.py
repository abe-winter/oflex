import flask, uuid, json, scrypt, os, random, binascii
from datetime import datetime, timedelta
from . import pool, middleware
from .config import CONFIG, getenv

APP = flask.Blueprint(__name__, 'oflex')

@APP.route('/login')
def get_login():
  return flask.render_template('login.htm', support_sms=CONFIG['support_sms'])

def set_session(userid):
  flask.session['userid'] = userid
  flask.session['expires'] = datetime.now() + timedelta(days=90) # used in middleware
  flask.session.permanent = True # i.e. permanent_session_lifetime = 31 days default. user can probably override this, expiration isn't secure.

def tobytes(raw):
  "helper to return bytes whether bytes or memoryview (postgres / sqlite)"
  return raw if isinstance(raw, bytes) else raw.tobytes()

@APP.route('/login/email', methods=['POST'])
def post_login_email():
  "login with email"
  form = flask.request.form
  with pool.withcon() as con:
    cur = con.cursor()
    cur.execute(CONFIG['queries']['get_user_email'], (form['email'],))
    raw_row = cur.fetchone()
    if raw_row is None:
      flask.flash('Bad login info!')
      return flask.redirect(flask.url_for('oflex.blueprint.get_login'))
  row = CONFIG['query_fields']['get_user_email'](*raw_row)
  assert row.auth_method == 'email'
  if tobytes(row.pass_hash) != scrypt.hash(form['password'].encode(), tobytes(row.pass_salt)):
    flask.flash('Bad login info!')
    return flask.redirect(flask.url_for('oflex.blueprint.get_login'))
  if CONFIG['require_verification'] and not row.verified:
    flask.flash("That password is correct but your email hasn't been verified yet!")
    return flask.redirect(flask.url_for('oflex.blueprint.get_wait'))
  set_session(row.userid)
  return flask.redirect(flask.url_for(CONFIG['login_home']))

@APP.route('/wait')
def get_wait():
  return flask.render_template('wait_verify.htm')

@APP.route('/verify')
def get_verify():
  email = flask.request.args['email']
  verification_code = flask.request.args['verification_code']
  if not email or not verification_code:
    flask.abort(flask.Response("Missing query params in link", status=400))
  with pool.withcon() as con:
    cur = con.cursor()
    cur.execute('begin')
    cur.execute(CONFIG['queries']['get_verify'], (email,))
    row = cur.fetchone()
    unk_details = flask.Response("Unknown verification details", status=404)
    if not row:
      print('email not found', email)
      flask.abort(unk_details) # possible attack
    actual_code, verified, pass_hash = row
    if verified is not None and actual_code == verification_code:
      flask.abort(flask.Response("Already verified!", status=400))
    if verified is not None or actual_code != verification_code:
      print('code_mismatch', actual_code, verification_code)
      flask.abort(unk_details) # possible attack
    assert verified is None and actual_code == verification_code
    cur.execute('update users set verified = now() where email = %s', (email,))
    cur.execute('commit')
  if pass_hash is None:
    return flask.redirect(flask.url_for('oflex.blueprint.get_finish'))
  else:
    flask.flash('Verification successful! Now log in')
    return flask.redirect(flask.url_for('oflex.blueprint.get_login'))

@APP.route('/finish')
def get_finish():
  assert CONFIG['require_verification']
  return flask.render_template('finish.htm', email=flask.request.args['email'], verification_code=flask.request.args['verification_code'])

@APP.route('/finish', methods=['POST'])
def post_finish():
  print('form', flask.request.form)
  raise NotImplementedError

@APP.route('/join')
def get_join():
  return flask.render_template('join.htm', support_sms=CONFIG['support_sms'], username_comment=CONFIG['username_comment'], username_name=CONFIG['username_name'])

@APP.route('/join/email', methods=['POST'])
def post_join_email():
  "create account with email / password"
  form = flask.request.form
  if not form['password']:
    flask.abort(flask.Response("Blank password not allowed", status=400))
  assert '@' in form['email'] and len(form['email']) < CONFIG['max_email']
  pass_salt = os.urandom(64)
  pass_hash = scrypt.hash(form['password'].encode(), pass_salt)
  userid = str(uuid.uuid4())
  with pool.withcon() as con:
    cur = con.cursor()
    # todo: rate limiting
    # todo: clearer error for duplicate email
    if CONFIG['require_verification']:
      verification_code = binascii.hexlify(os.urandom(10)).decode()
      cur.execute(
        CONFIG['queries']['create_user_email_ver'],
        (userid, form['username'], 'email', form['email'], pass_hash, pass_salt, verification_code)
      )
      CONFIG['send_verification_email'](form['email'], verification_code)
    else:
      cur.execute(
        CONFIG['queries']['create_user_email'],
        (userid, form['username'], 'email', form['email'], pass_hash, pass_salt)
      )
      # note: only set_session in this !require_verification branch
      set_session(userid)
  if CONFIG['require_verification']:
    return flask.redirect(flask.url_for('oflex.blueprint.get_wait'))
  else:
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
  import phonenumbers # delayed for soft dep
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
  normal = flask.session['sms']
  received_code = flask.request.form['confirm']
  confirm_key = f'sms-{normal}'
  correct_code = flask.current_app.redis.get(confirm_key)
  if received_code.encode() != correct_code:
    flask.abort(flask.Response('Bad code. Try again or request another code', status=401))
  dest = flask.url_for(CONFIG['login_home'])
  with pool.withcon() as con:
    cur = con.cursor()
    # todo: rate limiting
    cur.execute(CONFIG['queries']['get_user_sms'], (normal,))
    row = cur.fetchone()
    row = row and CONFIG['query_fields']['get_user_sms'](*row)
    userid = row and row.userid
    if not row:
      userid = str(uuid.uuid4())
      cur.execute(CONFIG['queries']['create_user_sms'], (userid, 'sms', normal))
      row = cur.fetchone()
      dest = flask.url_for('oflex.blueprint.username')
    elif not row.username:
      dest = flask.url_for('oflex.blueprint.username')
    set_session(userid)
  flask.current_app.redis.delete(confirm_key)
  return flask.redirect(dest)

@APP.route('/login/username')
def username():
  assert CONFIG['support_sms']
  return flask.render_template('username.htm', username_comment=CONFIG['username_comment'])

@APP.route('/login/username', methods=['POST'])
@middleware.require_session
def post_username():
  assert CONFIG['support_sms']
  username = flask.request.form['username']
  if len(username) < 3:
    flask.abort(flask.Response('Username too short -- 3 characters minimum', status=400))
  if len(username) > 64:
    flask.abort(flask.Response('Username too long -- 64 characters max', status=400))
  with pool.withcon() as con:
    cur = con.cursor()
    cur.execute(CONFIG['queries']['get_username'], (flask.g.session['userid'],))
    row = CONFIG['query_fields']['get_username'](*cur.fetchone())
    if row.username:
      flask.abort(flask.Response("Can't set a username! You already have one", status=400))
    cur.execute(CONFIG['queries']['update_username'], (username, flask.g.session['userid']))
  return flask.redirect(flask.url_for(CONFIG['login_home']))
