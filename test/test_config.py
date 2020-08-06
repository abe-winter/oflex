from oflex import config

def test_render():
  # this is confirming that there aren't any missing keys in the default config
  config.render_config()

def test_query_render_dialect():
  assert config.QueryRenderer('postgres').wildcard == '%s'
  assert config.QueryRenderer('sqlite').wildcard == '?'

def test_query_render_dialect():
  render = config.QueryRenderer('postgres')
  assert render.select('tab', ('c1',), 'c2') == "select c1 from tab where c2 = %s"
  assert render.update('tab', 'c1', 'c2') == "update tab set c1 = %s where c2 = %s"
  assert render.insert('tab', ('c1', 'c2')) == "insert into tab (c1, c2) values (%s, %s)"
