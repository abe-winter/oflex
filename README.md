# Oflex

O(pinionated) fl(ask) ex(tensions).

Flask login and connection-pooling stuff that I reuse in all my prototyping.

Will happily add docs if anyone else needs this.

This is 'highly opinionated' in that it likely only works for my stack.

Extensive reliance on flask globals. I don't like it either, but it makes integration *really easy*.

## Features

* [ ] flask blueprints for create-account and login pages
* [ ] and scrypt passwords
* [ ] and twilio login
* [ ] login-required decorator
* [ ] graphene / graphql middleware login-required
* [ ] HSTS middleware
* [ ] postgres & redis initializer
* [ ] postgres connection pool context manager

## What you should do to use this

* Look in `config.py` in this repo and make sure your SQL users table and environment variables conform to what this package expects.
* (You can customize the configs, but that's a waste)
* use `flask.current_app.pool` or `pool.withcon`, and `flask.current_app.redis` in your thing
