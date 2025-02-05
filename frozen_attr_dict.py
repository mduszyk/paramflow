
class FrozenAttrDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, '__dict__', self)

    def __setattr__(self, key, value):
        raise AttributeError('FrozenAttrDict is immutable')

    def __delattr__(self, key):
        raise AttributeError('FrozenAttrDict is immutable')

    def __setitem__(self, key, value):
        raise TypeError('FrozenAttrDict is immutable')

    def __delitem__(self, key):
        raise TypeError('FrozenAttrDict is immutable')
