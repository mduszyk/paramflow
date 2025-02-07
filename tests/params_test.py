import os
import sys
from tempfile import NamedTemporaryFile

import pytest

from dparams.params import load, merge, recursive_update, convert_type


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


def test_convert_type():
    assert convert_type(3, '10') == 10
    assert convert_type(3.14, '2.73') == 2.73
    assert convert_type(False, 'true') == True
    assert convert_type({}, '{"a": 1, "b": 2}') == {'a': 1, 'b': 2}
    assert convert_type([], '[1, 2, 3]') == [1, 2, 3]
