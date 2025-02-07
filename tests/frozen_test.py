from dparams.frozen import freeze, FrozenList, FrozenAttrDict


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
    assert isinstance(params, FrozenAttrDict)
    assert params.default.name == 'test'
    assert params.default.lr == 1e-3
    assert params.default.debug
    assert isinstance(params.default.list, FrozenList)
    assert params.default.list[2] == 3
    assert isinstance(params.default.dict, FrozenAttrDict)
    assert params.default.dict.foo == 1
    assert params.default.dict.bar == 2
