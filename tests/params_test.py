import os
import sys
from functools import reduce
from tempfile import NamedTemporaryFile

import pytest

import paramflow as pf
from paramflow.params import activate_profile, deep_merge, build_parsers
from paramflow.parser import EnvParser, DictParser, get_env_params


@pytest.fixture
def temp_file(request):
    def create_temp_file(content, suffix):
        tmp = NamedTemporaryFile(delete=False, mode='w+', suffix=suffix)
        tmp.write(content)
        tmp.close()
        request.addfinalizer(lambda: os.remove(tmp.name))
        return tmp.name
    return create_temp_file


def test_deep_merge():
    dst = {
        'default': {
            'name': 'test',
            'lr': 1e-3,
            'debug': True,
        }
    }
    src = {'default': {'name': 'test123'}}
    deep_merge(dst, src)
    assert dst['default']['name'] == 'test123'

def test_deep_merge_list():
    dst = {'default': {'tags': ['a', 'b', 'c']}}
    src = {'default': {'tags': ['x', 'y', 'z']}}
    deep_merge(dst, src)
    assert dst['default']['tags'] == ['x', 'y', 'z']


def test_deep_merge_empty_dict():
    dst = {
        'default': {
            'kwargs': {
                'lr': 1e-3,
                'debug': True,
            }
        }
    }
    src = {'default': {'kwargs': {}}}
    deep_merge(dst, src)
    assert dst['default']['kwargs'] == {}


def test_activate_profile():
    params = {
        'default': { 'debug': True },
        'prod': { 'debug': False }
    }
    params = activate_profile(params, 'default', 'prod')
    assert not params['debug']


def test_merge_override_layers():
    params = {'default': { 'name': 'test' }}
    overrides = {'default': {'name': 'test123'}}
    params = reduce(deep_merge, [params, overrides])
    params = activate_profile(params, 'default', 'default')
    assert params['name'] == 'test123'


def test_merge_multiple_layers_and_activate():
    layer1 = {'default': {'debug': True, 'name': 'Joe', 'age': 20}}
    layer2 = {'prod': { 'debug': False }}
    layer3 = {'prod': {'name': 'Jane'}}
    layer4 = {'prod': {'age': 30}}
    layers = [layer1, layer2, layer3, layer4]
    params = reduce(deep_merge, layers)
    params = activate_profile(params, 'default', 'prod')
    assert not params['debug']
    assert params['name'] == 'Jane'
    assert params['age'] == 30


def test_toml_no_profiles(temp_file, monkeypatch):
    file_content = (
        """
        name = 'test'
        lr = 1e-3
        debug = true
        """
    )
    file_path = temp_file(file_content, '.toml')
    monkeypatch.setattr(sys, 'argv', ['test.py'])
    params = pf.load(file_path)
    assert params.name == 'test'
    assert params.lr == 1e-3
    assert params.debug


def test_toml_default(temp_file, monkeypatch):
    file_content = (
        """
        [default]
        name = 'test'
        lr = 1e-3
        debug = true
        """
    )
    file_path = temp_file(file_content, '.toml')
    monkeypatch.setattr(sys, 'argv', ['test.py'])
    params = pf.load(file_path)
    assert params.name == 'test'
    assert params.lr == 1e-3
    assert params.debug


def test_yaml_profile_env_args(temp_file, monkeypatch):
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
    monkeypatch.setenv('P_LR', '0.0001')
    monkeypatch.setattr(sys, 'argv', ['test.py', '--profile', 'prod', '--name', 'production'])
    params = pf.load(file_path)
    assert params.name == 'production'
    assert params.lr == 1e-4
    assert not params.debug
    assert params.__source__ == [file_path, 'env', 'args']


def test_load_all_layers(temp_file, monkeypatch):
    file1 = temp_file("default:\n  lr: 0.001", '.yaml')
    file2 = temp_file("[default]\nname = 'dev'", '.ini')
    file3 = temp_file('[default]\ndebug = true\nbatch_size=32', '.toml')
    file4 = temp_file('{"prod": {"debug": false}}', '.json')
    file5 = temp_file('P_NAME=production', '.env')
    monkeypatch.setenv('P_LR', '0.0001')
    monkeypatch.setenv('P_PROFILE', 'prod')
    monkeypatch.setattr(sys, 'argv', ['test.py', '--batch_size', '64'])
    params = pf.load(file1, file2, file3, file4, file5)
    assert params.name == 'production'
    assert params.lr == 0.0001
    assert params.batch_size == 64
    assert not params.debug
    assert params.__source__ == [file1, file2, file3, file4, file5, 'env', 'args']
    assert params.__profile__ == ['default', 'prod']


def test_custom_merge_order(temp_file, monkeypatch):
    file_toml = temp_file('[default]\nname = "local"\ndebug = true\nbatch_size=32', '.toml')
    dot_env = temp_file('P_NAME=prod', '.env')
    monkeypatch.setenv('P_NAME', 'dev')
    monkeypatch.setattr(sys, 'argv', ['test.py', '--batch_size', '64'])
    source = [file_toml, 'env', dot_env, 'args']
    params = pf.load(*source)
    assert params.name == 'prod'
    assert params.batch_size == 64
    assert params.debug
    assert params.__source__ == source
    assert params.__profile__ == ['default']


def test_specify_file_via_cmd(temp_file, monkeypatch):
    file_toml = temp_file('[default]\nname = "dev"\ndebug = true\nbatch_size=32', '.toml')
    monkeypatch.setattr(sys, 'argv', ['test.py', '--sources', file_toml])
    params = pf.load()
    assert params.name == 'dev'
    assert params.batch_size == 32
    assert params.debug
    assert params.__source__ == [file_toml]
    assert params.__profile__ == ['default']


def test_nested_configuration(temp_file):
    file1_yaml = temp_file(
        """
        default:
          level1:
            name: 'abc'
            value: 17
            level2:
                name: 'foo'
                value: 0
        """, '.yaml')
    file2_yaml = temp_file(
        """
        default:
          level1:
            name: 'bar'
            level2:
                value: 42
        """, '.yaml')
    params = pf.load(file1_yaml, file2_yaml)
    assert params.level1.name == 'bar'
    assert params.level1.value == 17
    assert params.level1.level2.name == 'foo'
    assert params.level1.level2.value == 42


def test_args_only_param(temp_file, monkeypatch):
    file_content = (
        """
        [default]
        lr = 1e-3
        debug = true
        """
    )
    file_path = temp_file(file_content, '.toml')
    monkeypatch.setattr(sys, 'argv', ['test.py', '--batch_size', '64', '--name', 'test'])
    params = pf.load(file_path)
    assert params.lr == 1e-3
    assert params.debug
    assert params.batch_size == 64
    assert params.name == 'test'


def test_dict_params(temp_file, monkeypatch):
    file_content = (
        """
        [default]
        lr = 1e-3
        debug = true
        """
    )
    file_path = temp_file(file_content, '.toml')
    monkeypatch.setattr(sys, 'argv', ['test.py'])
    params = pf.load(file_path, {'name': 'test'})
    assert params.lr == 1e-3
    assert params.debug
    assert params.name == 'test'


def test_deep_merge_source_key():
    dst = {'__source__': ['a']}
    src = {'__source__': ['b', 'c']}
    deep_merge(dst, src)
    assert dst['__source__'] == ['a', 'b', 'c']


def test_deep_merge_list_length_mismatch():
    dst = {'default': {'tags': ['a', 'b']}}
    src = {'default': {'tags': ['x', 'y', 'z']}}
    deep_merge(dst, src)
    assert dst['default']['tags'] == ['x', 'y', 'z']


def test_deep_merge_list_of_dicts():
    dst = {'items': [{'name': 'a', 'val': 1}, {'name': 'b', 'val': 2}]}
    src = {'items': [{'val': 10}, {'name': 'B'}]}
    deep_merge(dst, src)
    assert dst['items'][0]['name'] == 'a'
    assert dst['items'][0]['val'] == 10
    assert dst['items'][1]['name'] == 'B'
    assert dst['items'][1]['val'] == 2


def test_activate_profile_missing():
    params = {'default': {'x': 1}, 'prod': {'x': 2}}
    with pytest.raises(ValueError, match="profile 'staging' not found"):
        activate_profile(params, 'default', 'staging')


def test_activate_profile_missing_lists_available():
    params = {'default': {'x': 1}, 'prod': {'x': 2}, 'dev': {'x': 3}, '__source__': ['f.toml']}
    with pytest.raises(ValueError) as exc:
        activate_profile(params, 'default', 'staging')
    msg = str(exc.value)
    assert 'prod' in msg
    assert 'dev' in msg
    assert 'default' not in msg
    assert '__source__' not in msg


def test_activate_profile_none():
    params = {'default': {'x': 1}, 'prod': {'x': 2}}
    result = activate_profile(params, 'default', None)
    assert result['x'] == 1
    assert result['__profile__'] == ['default']


def test_activate_profile_same_as_default():
    params = {'default': {'x': 1}}
    result = activate_profile(params, 'default', 'default')
    assert result['x'] == 1
    assert result['__profile__'] == ['default']


def test_activate_profile_no_profile_key():
    params = {'x': 1, 'y': 2}
    result = activate_profile(params, 'default', None)
    assert result['x'] == 1
    assert result['__profile__'] == ['default']


def test_activate_profile_source_propagation():
    params = {
        'default': {'x': 1},
        '__source__': ['file.toml'],
    }
    result = activate_profile(params, 'default', None)
    assert result['__source__'] == ['file.toml']


def test_load_with_profile_kwarg(temp_file, monkeypatch):
    file_content = """
    [default]
    debug = true
    [prod]
    debug = false
    """
    file_path = temp_file(file_content, '.toml')
    monkeypatch.setattr(sys, 'argv', ['test.py'])
    params = pf.load(file_path, profile='prod')
    assert not params.debug


def test_get_env_params_direct():
    env = {'P_NAME': 'alice', 'P_LR': '0.01', 'OTHER': 'ignored'}
    ref_params = {'name': 'bob', 'lr': 0.001}
    result = get_env_params(env, 'P_', ref_params)
    assert result == {'name': 'alice', 'lr': '0.01'}


def test_env_parser_no_match():
    parser = EnvParser('ZZZNOMATCH_', 'default')
    result = parser({'default': {'name': 'test', 'lr': 0.001}})
    assert result == {}


def test_dict_parser_direct():
    data = {'name': 'test', 'lr': 0.001}
    parser = DictParser(data)
    result = parser()
    assert result['default'] == data
    assert result['__source__'] == [data]
    assert result['default'] is not data


def test_build_parsers_unknown_extension():
    meta = pf.freeze({
        'env_prefix': 'P_',
        'args_prefix': '',
        'default_profile': 'default',
        'profile': None,
    })
    with pytest.raises(ValueError, match=r"unsupported file format '\.xyz'"):
        build_parsers(['config.xyz'], meta)


def test_help(temp_file, monkeypatch, capsys):
    file_content = (
        """
        [default]
        lr = 1e-3
        debug = true
        """
    )
    file_path = temp_file(file_content, '.toml')
    monkeypatch.setattr(sys, 'argv', ['test.py', '--help'])
    with pytest.raises(SystemExit) as exc:
        pf.load(file_path)
    captured = capsys.readouterr()
    assert 'Meta-parameters' in captured.out
    assert 'Parameters' in captured.out
