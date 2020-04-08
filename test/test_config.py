from oflex import config

def test_render():
  # this is confirming that there aren't any missing keys in the default config
  config.render_config()
