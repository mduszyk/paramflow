
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


class FrozenList(list):

    def __setitem__(self, index, value):
        raise TypeError('FrozenList is immutable')

    def __delitem__(self, index):
        raise TypeError('FrozenList is immutable')

    def append(self, value):
        raise TypeError('FrozenList is immutable')

    def extend(self, iterable):
        raise TypeError('FrozenList is immutable')

    def insert(self, index, value):
        raise TypeError('FrozenList is immutable')

    def remove(self, value):
        raise TypeError('FrozenList is immutable')

    def pop(self, index=-1):
        raise TypeError('FrozenList is immutable')

    def clear(self):
        raise TypeError('FrozenList is immutable')

    def __iadd__(self, other):
        raise TypeError('FrozenList is immutable')

    def __imul__(self, other):
        raise TypeError('FrozenList is immutable')
