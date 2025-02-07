from dparams.frozen import freeze, FrozenList, FrozenAttrDict


def test_freeze():
    params = freeze({
        'default': {
            'name': 'test',
            'lr': 1e-3,
            'debug': True,
            'lst': [1, 2, 3]
        }
    })
    assert isinstance(params, FrozenAttrDict)
    assert params.default.name == 'test'
    assert params.default.lr == 1e-3
    assert params.default.debug
    assert isinstance(params.default.lst, FrozenList)
    assert params.default.lst[0] == 1
