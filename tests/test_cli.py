import importlib
import os
import sys
from contextlib import contextmanager

from fret.app import App, get_app, set_global_app
from fret.cli import main
import py
import pytest


@contextmanager
def chapp(appdir):
    _app = get_app()
    _cwd = os.getcwd()
    _path = sys.path.copy()
    appdir = str(appdir)
    os.chdir(appdir)
    app = App()
    set_global_app(app)
    imp = app.import_modules()
    if imp:
        try:
            importlib.reload(imp)
        except (ImportError, AttributeError):
            pass
    try:
        yield app
    finally:
        set_global_app(_app)
        os.chdir(_cwd)
        sys.path = _path


code1 = '''
import fret

@fret.configurable
class Model:
    def __init__(self, x=3, y=4):
        ...

@fret.command
def run(ws):
    model = ws.build()
    print(model)
    return model
'''

code2 = '''
import fret

@fret.command
def train(ws):
    model = ws.build()
    model.train()
    ws.save(model, 'trained')

@fret.command
def test(ws):
    model = ws.load('ws/best/snapshot/main.trained.pt')
    print(model.weight)
    return model

@fret.configurable
@fret.stateful('weight')
class Model:
    def __init__(self):
        self.weight = 0
    def train(self):
        self.weight = 23
'''


def test_main(tmpdir: py.path.local):
    with pytest.raises(SystemExit):
        main()

    appdir = tmpdir.join('appdir1')
    appdir.mkdir()

    with appdir.join('main.py').open('w') as f:
        f.write(code1)

    with chapp(appdir) as app:
        app.main('config Model'.split())
        model = app.main(['run'])
        assert model.config.x == 3

        app.main('config Model -x 5 -y 10'.split())
        model = app.main(['run'])
        assert model.config.x == 5
        assert model.config.y == 10

        assert app.main(['config']) is not None

        app.main(['clean', '-c'])
        with pytest.raises(SystemExit):
            app.main(['run'])

        with pytest.raises(SystemExit):
            assert app.main(['config']) is None

        app.main('-w ws/model1 config Model'.split())
        app.main('-w ws/model2 config Model -x 5 -y 10'.split())
        model = app.main('-w ws/model1 run'.split())
        assert model.config.x == 3
        model = app.main('-w ws/model2 run'.split())
        assert model.config.x == 5

    appdir.join('fret.toml').open('w').close()
    with chapp(appdir.join('ws/model2')) as app:
        model = app.main(['run'])
        assert model.config.x == 5

    appdir = tmpdir.join('appdir2')
    appdir.mkdir()
    appdir.join('main.py').open('w').close()

    with appdir.join('main.py').open('w') as f:
        f.write(code2)
    with chapp(appdir) as app:
        app.main('-w ws/best config Model'.split())
        app.main(' -w ws/best train'.split())
        model = app.main(['test'])
        assert model.weight == 23
