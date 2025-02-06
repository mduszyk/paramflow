import os
import sys
from tempfile import NamedTemporaryFile

from params import load_params, merge_params, update_leaves


def test_update_leaves():
    dst = {
        'default': {
            'name': 'test',
            'lr': 1e-3,
            'debug': True,
        }
    }
    src = {'default': {'name': 'test123'}}
    update_leaves(dst, src)
    assert dst['default']['name'] == 'test123'


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
        params = load_params(fp.name)
    assert params.name == 'test'
    assert params.lr == 1e-3
    assert params.debug


def test_merge_profile():
    params = {
        'default': { 'debug': True },
        'prod': { 'debug': False }
    }
    params = merge_params([params], [], None, 'default', 'prod')
    assert not params.debug


def test_merge_override_layers():
    params = {'default': { 'name': 'test' }}
    override_params = {'name': 'test123'}
    params = merge_params([params], [override_params], None, 'default', None)
    assert params.name == 'test123'
