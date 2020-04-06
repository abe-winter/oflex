# Oflex

O(pinionated) fl(ask) ex(tensions).

Flask login and connection-pooling stuff that I reuse in all my prototyping. The one-line goal of this project is to have drop-in login, however inflexible, rather than spending 6 hours setting it up every time.

This is only compatible with my postgres / redis stack and a similar DB users schema.

Will happily add docs if anyone else needs this, post a github issue to LMK.

## Features

These things wouldn't normally belong together and are only bound together by the common themes of (1) me needing them every time (2) I haven't found a right-fit library to do any of them in flask (3) they're all difficult to integrate automatically without some schema / template / backend assumptions.

* [x] flask blueprints for create-account and login pages
* [x] and scrypt passwords
* [ ] and twilio login
* [x] login-required decorator
* [x] graphene / graphql middleware login-required
* [ ] HSTS middleware
* [x] postgres & redis initializer
* [x] postgres connection pool context manager
* [ ] basic RBAC
* [ ] werkzeug remote IP
* [ ] in-memory and redis rate limiting
* [ ] email verification
* [ ] invitations & preapproval lists

## What you should do to use this

* Look in `config.py` in this repo and make sure your SQL users table and environment variables conform to what this package expects.
* (You can customize the configs, but that's a waste)
* use `flask.current_app.pool` or `pool.withcon`, and `flask.current_app.redis` in your thing
* You have a base.htm template that defines styles, headers, etc
