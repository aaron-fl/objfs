from scripts.core.cfg import Config

@Config.target()
def local(c):
    pass

@Config.target()
def test(c):
    pass

@Config.target()
def initial(c):
    c.name = 'objfs'
    c.version = '0.1.0'
    c.grep_groups = dict(
        docs = [('rst, md', 'docs', '*/_static/*', '*/html/*', '*/__pycache__/*')],
        scripts = [('py', 'scripts', '*/__pycache__/*')],
        config = [('', 'config.py', '*/__pycache__/*')],
        lib = [('py', 'objfs', '*/__pycache__/*')],
    )


@Config.target()
def final(c):
    pass
