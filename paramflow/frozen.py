from typing import Union, List, Dict, Any


class ParamsDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, '__dict__', self)

    def __setattr__(self, key, value):
        raise AttributeError(f'{self.__class__.__name__} is immutable')

    def __delattr__(self, key):
        raise AttributeError(f'{self.__class__.__name__} is immutable')

    def __setitem__(self, key, value):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def __delitem__(self, key):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def __getattr__(self, key) -> Any:
        return self[key]

class ParamsList(list):

    def __setitem__(self, index, value):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def __delitem__(self, index):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def append(self, value):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def extend(self, iterable):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def insert(self, index, value):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def remove(self, value):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def pop(self, index=-1):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def clear(self):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def __iadd__(self, other):
        raise TypeError(f'{self.__class__.__name__} is immutable')

    def __imul__(self, other):
        raise TypeError(f'{self.__class__.__name__} is immutable')


def freeze(params: Union[List[any], Dict[str, any]]) -> Union[ParamsList[any], ParamsDict[str, any]]:
    """
    Recursively freeze dictionaries and list making them read-only. Frozen dict profides attribute-style access.
    :param params: parameters as python dict and list tree
    :return: frozen parameters
    """
    if isinstance(params, dict):
        for key, value in params.items():
            if isinstance(value, dict) or isinstance(value, list):
                params[key] = freeze(value)
        return ParamsDict(params)
    elif isinstance(params, list):
        for i in range(len(params)):
            value = params[i]
            if isinstance(value, dict) or isinstance(value, list):
                params[i] = freeze(value)
        return ParamsList(params)


def unfreeze(params: Union[ParamsList[any], ParamsDict[str, any]]) -> Union[List[any], Dict[str, any]]:
    """
    Recursively unfreeze tree of frozen dicts and lists.
    Useful for serialization, where deserialization of immutable dict or list may fail.
    :param params: frozen parameters tree
    :return: parameters as dict and list tree
    """
    if isinstance(params, dict):
        params = dict(params)
        for key, value in params.items():
            if isinstance(value, dict) or isinstance(value, list):
                params[key] = unfreeze(value)
        return params
    elif isinstance(params, list):
        params = list(params)
        for i in range(len(params)):
            value = params[i]
            if isinstance(value, dict) or isinstance(value, list):
                params[i] = unfreeze(value)
        return params
