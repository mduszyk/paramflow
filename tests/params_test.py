import os
import sys
from tempfile import NamedTemporaryFile

import pytest

from paramflow.params import load, merge, merge_layers


def test_merge_layers():
    dst = {
        'default': {
            'name': 'test',
            'lr': 1e-3,
            'debug': True,
        }
    }
    src = {'default': {'name': 'test123'}}
    merge_layers(dst, src)
    assert dst['default']['name'] == 'test123'


def test_merge_profile():
    params = {
        'default': { 'debug': True },
        'prod': { 'debug': False }
    }
    params = merge([params], 'default', 'prod')
    assert not params['debug']


def test_merge_override_layers():
    params = {'default': { 'name': 'test' }}
    overrides = {'default': {'name': 'test123'}}
    params = merge([params, overrides], 'default', 'default')
    assert params['name'] == 'test123'


def test_merge_multiple_layers():
    layer1 = {'default': {'debug': True, 'name': 'Joe', 'age': 20}}
    layer2 = {'prod': { 'debug': False }}
    layer3 = {'prod': {'name': 'Jane'}}
    layer4 = {'prod': {'age': 30}}
    params = merge([layer1, layer2, layer3, layer4], 'default', 'prod')
    assert not params['debug']
    assert params['name'] == 'Jane'
    assert params['age'] == 30


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
    params = load(file=file_path)
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
    params = load(file=file_path)
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
    params = load(file=file_path)
    assert params.name == 'production'
    assert params.lr == 1e-4
    assert not params.debug
    assert params.__source__ == [file_path, 'environment', 'arguments']


def test_load_all_layers(temp_file):
    file1 = temp_file("default:\n  lr: 0.001", '.yaml')
    file2 = temp_file("[default]\nname = 'dev'", '.ini')
    file3 = temp_file('[default]\ndebug = true\nbatch_size=32', '.toml')
    file4 = temp_file('{"prod": {"debug": false}}', '.json')
    file5 = temp_file('P_NAME=production', '.env')
    os.environ['P_LR'] = '0.0001'
    sys.argv = ['test.py', '--profile', 'prod', '--batch_size', '64']
    params = load(file=[file1, file2, file3, file4], dot_env_file=file5)
    assert params.name == 'production'
    assert params.lr == 0.0001
    assert params.batch_size == 64
    assert not params.debug
    assert params.__source__ == [file1, file2, file3, file4, file5, 'environment', 'arguments']
    assert params.__profile__ == ['default', 'prod']
