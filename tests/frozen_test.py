import pytest

from paramflow.frozen import freeze, unfreeze, ParamsList, ParamsDict


def test_freeze():
    params = freeze({
        'default': {
            'name': 'test',
            'lr': 1e-3,
            'debug': True,
            'list': [1, 2, 3],
            'dict': {'foo': 1, 'bar': 2},
        }
    })
    assert isinstance(params, ParamsDict)
    assert params.default.name == 'test'
    assert params.default.lr == 1e-3
    assert params.default.debug
    assert isinstance(params.default.list, ParamsList)
    assert params.default.list[2] == 3
    assert isinstance(params.default.dict, ParamsDict)
    assert params.default.dict.foo == 1
    assert params.default.dict.bar == 2

def test_unfreeze():
    params = freeze({
        'default': {
            'name': 'test',
            'list': [1, 2, 3],
        }
    })
    params2 = freeze(unfreeze(params))
    assert params.default.name == params2.default.name
    assert len(params.default.list) == len(params2.default.list)
    assert params.default.list[0] == params2.default.list[0]
    assert params.default.list[1] == params2.default.list[1]
    assert params.default.list[2] == params2.default.list[2]


def test_params_dict_immutability():
    params = freeze({'x': 1, 'y': 2})
    with pytest.raises(AttributeError):
        params.x = 10
    with pytest.raises(AttributeError):
        del params.x
    with pytest.raises(TypeError):
        params['x'] = 10
    with pytest.raises(TypeError):
        del params['x']


def test_params_dict_missing_key():
    params = freeze({'x': 1})
    with pytest.raises(AttributeError, match="has no param 'z'"):
        _ = params.z


def test_params_list_immutability():
    pl = freeze([1, 2, 3])
    with pytest.raises(TypeError):
        pl[0] = 99
    with pytest.raises(TypeError):
        del pl[0]
    with pytest.raises(TypeError):
        pl.append(4)
    with pytest.raises(TypeError):
        pl.extend([4, 5])
    with pytest.raises(TypeError):
        pl.insert(0, 0)
    with pytest.raises(TypeError):
        pl.remove(1)
    with pytest.raises(TypeError):
        pl.pop()
    with pytest.raises(TypeError):
        pl.clear()
    with pytest.raises(TypeError):
        pl.__iadd__([4])
    with pytest.raises(TypeError):
        pl.__imul__(2)


def test_freeze_list():
    frozen = freeze([1, {'a': 2}, [3, 4]])
    assert isinstance(frozen, ParamsList)
    assert frozen[0] == 1
    assert isinstance(frozen[1], ParamsDict)
    assert frozen[1].a == 2
    assert isinstance(frozen[2], ParamsList)


def test_unfreeze_list():
    frozen = freeze([1, {'a': 2}, [3, 4]])
    unfrozen = unfreeze(frozen)
    assert type(unfrozen) is list
    assert unfrozen[0] == 1
    assert type(unfrozen[1]) is dict
    assert type(unfrozen[2]) is list
