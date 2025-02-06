import sys
from tempfile import NamedTemporaryFile

from dparams.params import load, merge, recursive_update


def test_recursive_update():
    dst = {
        'default': {
            'name': 'test',
            'lr': 1e-3,
            'debug': True,
        }
    }
    src = {'default': {'name': 'test123'}}
    recursive_update(dst, src)
    assert dst['default']['name'] == 'test123'


def test_toml_no_profiles():
    toml_data = (
        """
        name = 'test'
        lr = 1e-3
        debug = true
        """
    )
    with NamedTemporaryFile(mode='w+', newline='', delete_on_close=False, suffix='.toml') as fp:
        fp.write(toml_data)
        fp.close()
        sys.argv = ['test.py']
        params = load(fp.name)
    assert params.name == 'test'
    assert params.lr == 1e-3
    assert params.debug


def test_toml_default():
    toml_data = (
        """
        [default]
        name = 'test'
        lr = 1e-3
        debug = true
        """
    )
    with NamedTemporaryFile(mode='w+', newline='', delete_on_close=False, suffix='.toml') as fp:
        fp.write(toml_data)
        fp.close()
        sys.argv = ['test.py']
        params = load(fp.name)
    assert params.name == 'test'
    assert params.lr == 1e-3
    assert params.debug


def test_merge_profile():
    params = {
        'default': { 'debug': True },
        'prod': { 'debug': False }
    }
    params = merge([params], [], None, 'default', 'prod')
    assert not params.debug


def test_merge_override_layers():
    params = {'default': { 'name': 'test' }}
    override_params = {'name': 'test123'}
    params = merge([params], [override_params], None, 'default', None)
    assert params.name == 'test123'
