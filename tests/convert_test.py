import pytest

from paramflow.convert import convert_type


def test_convert_type():
    assert type(convert_type(3, 10)) is int
    assert convert_type(3, 10) == 10
    assert convert_type(3, '10') == 10
    assert type(convert_type(3.0, 10)) is float
    assert convert_type(3.0, 10) == 10.0
    assert convert_type(3.14, '2.73') == 2.73
    assert convert_type(False, 'true') == True
    assert convert_type({}, '{"a": 1, "b": 2}') == {'a': 1, 'b': 2}
    assert convert_type([], '[1, 2, 3]') == [1, 2, 3]


def test_failed_conversion():
    with pytest.raises(TypeError):
        convert_type({}, 5)
