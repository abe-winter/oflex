import flask, json, functools
from datetime import datetime

def require_session_inner(wrapped, api_mode=False):
  "helper"
  if hasattr(wrapped, '__wrapped__'):
    print("warning: require_session is wrapping a function that already has been wrapped. Make sure you're using it *inside* the @route decorator", wrapped)
  @functools.wraps(wrapped)
  def outer(*args, **kwargs):
    # todo: remember redirect page
    userid = flask.session.get('userid')
    # note: 'expires' here should never matter b/c cookie expires in 31 days, but this is signed and that isn't I think so I have this
    if userid is None or 'expires' not in flask.session or flask.session['expires'] < datetime.now():
      if api_mode:
        flask.abort(flask.Response("missing or expired session, sign in", status=401))
      else:
        flask.flash('Session expired, sign in again')
        return flask.redirect(flask.url_for('oflex.blueprint.get_login'))
    flask.g.session = {'userid': userid}
    return wrapped(*args, **kwargs)
  return outer

def require_session(wrapped):
  "decorator to require login on a session. use beneath the @route() decorator or it won't work"
  return require_session_inner(wrapped)

def require_session_api(wrapped):
  "call this directly with api_mode=True for API routes that should raise 401 instead of redirecting"
  # note: redirecting is bad because it means axios doesn't raise auth failures as errors
  return require_session_inner(wrapped, api_mode=True)
