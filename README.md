# Oflex

O(pinionated) fl(ask) ex(tensions).

Flask login and connection-pooling stuff that I reuse in all my prototyping. The one-line goal of this project is to have drop-in login, however inflexible, rather than spending 6 hours setting it up every time.

This is only compatible with my postgres / redis stack and a similar DB users schema.

Will happily add docs if anyone else needs this, post a github issue to LMK.

## Features

These things wouldn't normally belong together and are only bound together by the common themes of (1) me needing them every time (2) not having found a right-fit library for any and (3) difficult to integrate automatically without some assumptions.

* [ ] flask blueprints for create-account and login pages
* [ ] and scrypt passwords
* [ ] and twilio login
* [ ] login-required decorator
* [ ] graphene / graphql middleware login-required
* [ ] HSTS middleware
* [ ] postgres & redis initializer
* [ ] postgres connection pool context manager
* [ ] basic RBAC
* [ ] werkzeug remote IP
* [ ] in-memory and redis rate limiting
* [ ] email verification

## What you should do to use this

* Look in `config.py` in this repo and make sure your SQL users table and environment variables conform to what this package expects.
* (You can customize the configs, but that's a waste)
* use `flask.current_app.pool` or `pool.withcon`, and `flask.current_app.redis` in your thing
* You have a base.htm template that defines styles, headers, etc
