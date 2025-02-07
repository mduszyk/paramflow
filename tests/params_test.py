import os
import sys
from tempfile import NamedTemporaryFile

import pytest

from paramflow.params import load, merge, recursive_update


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


@pytest.fixture
def temp_file(request):
    def create_temp_file(content, suffix):
        tmp = NamedTemporaryFile(delete=False, mode='w+', suffix=suffix)
        tmp.write(content)
        tmp.close()
        request.addfinalizer(lambda: os.remove(tmp.name))
        return tmp.name
    return create_temp_file


def test_toml_no_profiles(temp_file):
    file_content = (
        """
        name = 'test'
        lr = 1e-3
        debug = true
        """
    )
    file_path = temp_file(file_content, '.toml')
    sys.argv = ['test.py']
    params = load(file_path)
    assert params.name == 'test'
    assert params.lr == 1e-3
    assert params.debug


def test_toml_default(temp_file):
    file_content = (
        """
        [default]
        name = 'test'
        lr = 1e-3
        debug = true
        """
    )
    file_path = temp_file(file_content, '.toml')
    sys.argv = ['test.py']
    params = load(file_path)
    assert params.name == 'test'
    assert params.lr == 1e-3
    assert params.debug


def test_yaml_profile_env_args(temp_file):
    file_content = (
        """
        default:
          name: 'dev'
          lr: 0.001
          debug: true
        prod:
          debug: false
        """
    )
    file_path = temp_file(file_content, '.yaml')
    os.environ['P_LR'] = '0.0001'
    sys.argv = ['test.py', '--profile', 'prod', '--name', 'production']
    params = load(file_path)
    assert params.name == 'production'
    assert params.lr == 1e-4
    assert not params.debug


def test_merge_profile():
    params = {
        'default': { 'debug': True },
        'prod': { 'debug': False }
    }
    params = merge([params], [], active_profile='prod')
    assert not params['debug']


def test_merge_override_layers():
    params = {'default': { 'name': 'test' }}
    override_params = {'name': 'test123'}
    params = merge([params], [override_params])
    assert params['name'] == 'test123'


def test_merge_no_profiles_override_layers():
    params = {'name': 'test' }
    override_params = {'name': 'test123'}
    params = merge([params], [override_params])
    assert params['name'] == 'test123'


def test_merge_multiple_layers():
    layer1 = {
        'default': {'debug': True, 'name': 'Joe', 'age': 20},
    }
    layer2 = {
        'prod': { 'debug': False }
    }
    override_layer1 = {
        'name': 'Jane',
    }
    override_layer2 = {
        'age': 30,
    }
    params = merge([layer1, layer2], [override_layer1, override_layer2], active_profile='prod')
    assert not params['debug']
    assert params['name'] == 'Jane'
    assert params['age'] == 30
