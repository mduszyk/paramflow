import os
from tempfile import NamedTemporaryFile

from params import load_params, merge_params


def test_toml_default():
    toml_data = (
        """
        [default]
        name = 'test'
        lr = 1e-3
        debug = true
        """
    )
    with NamedTemporaryFile(mode='w+', newline='', delete_on_close=False) as fp:
        fp.write(toml_data)
        fp.close()
        params = load_params(fp.name)
    assert params.name == 'test'
    assert params.lr == 1e-3
    assert params.debug


def test_merge_profile():
    params = {
        "default": { 'debug': True },
        'prod': { 'debug': False }
    }
    params = merge_params(params, profile='prod')
    assert not params.debug


def test_merge_env():
    params = {
        "default": { 'name': 'test' },
    }
    os.environ['PARAMS_NAME'] = 'test123'
    params = merge_params(params, env_prefix='PARAMS_')
    assert params.name == 'test123'
