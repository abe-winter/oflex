# Changelog

## 0.0.x series

* 0.0.3
  - bugfix: `include_package_data`
  - feature: sqlite support (major refactor, might break postgres support, haven't tested)
  - switch from indirect session to signed userid in cookie to remove redis dependency in some cases
* 0.0.2
  - add SMS login behind a flag (defaults to on)
  - CI / test / lint
  - configurable sql params & render\_config
  - internal: use named instead of positional vars for sql
  - internal: pytest
* 0.0.1 initial release
