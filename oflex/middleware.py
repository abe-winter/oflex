import flask, json, functools

def require_session(inner):
  "decorator to require login on a session. use beneath the @route() decorator or it won't work"
  @functools.wraps(inner)
  def outer(*args, **kwargs):
    # todo: remember redirect page
    # todo: freak out if inner fn is already decorated with a route
    sessionid = flask.session.get('sessionid')
    print('sessionid', sessionid, flask.session)
    if not sessionid:
      return flask.redirect(flask.url_for('oflex.blueprint.get_login'))
    raw = flask.current_app.redis.get(f'session-{sessionid}')
    if not raw:
      return flask.redirect(flask.url_for('oflex.blueprint.get_login'))
    flask.g.session = json.loads(raw)
    return inner(*args, **kwargs)
  return outer

class GQLAuthMiddleware:
  "authorization middleware for graphql with graphene"
  def resolve(self, next, root, info, **args):
    if not hasattr(flask.g, 'session'):
      sessionid = flask.session.get('sessionid')
      if not sessionid:
        flask.abort(401)
      dets = flask.current_app.redis.get(f'session-{sessionid}')
      if not dets:
        flask.abort(401)
      flask.g.session = json.loads(dets)
    return next(root, info, **args)
