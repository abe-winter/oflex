import flask

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
