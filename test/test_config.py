from oflex import config

def test_render():
  # this is confirming that there aren't any missing keys in the default config
  config.render_config()

def test_query_render_dialect():
  assert config.QueryRenderer({}, {}, 'postgres').wildcard == '%s'
  assert config.QueryRenderer({}, {}, 'sqlite').wildcard == '?'

def test_query_render_dialect():
  render = config.QueryRenderer({'c1': 'C1', 'c2': 'C2'}, {'tab': 'TAB'}, 'postgres')
  assert render.select('tab', ('c1',), 'c2') == "select C1 from TAB\nwhere C2 = %s"
  assert render.update('tab', 'c1', 'c2') == "update TAB\nset C1 = %s\nwhere C2 = %s"
  assert render.insert('tab', ('c1', 'c2')) == "insert into TAB (C1, C2)\nvalues (%s, %s)"
