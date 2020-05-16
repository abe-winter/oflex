import flask, json, functools
from datetime import datetime

def require_session(inner):
  "decorator to require login on a session. use beneath the @route() decorator or it won't work"
  if hasattr(inner, '__wrapped__'):
    print("warning: require_session is wrapping a function that already has been wrapped. Make sure you're using it *inside* the @route decorator", inner)
  @functools.wraps(inner)
  def outer(*args, **kwargs):
    # todo: remember redirect page
    userid = flask.session.get('userid')
    if userid is None or 'expires' not in flask.session or flask.session['expires'] < datetime.now():
      return flask.redirect(flask.url_for('oflex.blueprint.get_login'))
    flask.g.session = {'userid': userid}
    return inner(*args, **kwargs)
  return outer
