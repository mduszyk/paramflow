import pytest

from paramflow.convert import convert_type, infer_type


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


def test_infer_type():
    assert infer_type('42') == 42
    assert type(infer_type('42')) is int
    assert infer_type('3.14') == 3.14
    assert type(infer_type('3.14')) is float
    assert infer_type('hello') == 'hello'
    assert type(infer_type('hello')) is str
    assert infer_type('true') is True
    assert infer_type('false') is False
    assert infer_type('True') is True
    assert infer_type('False') is False


def test_convert_type_none_dst():
    assert convert_type(None, 42) == 42
    assert convert_type(None, 'hello') == 'hello'
    assert convert_type(None, [1, 2, 3]) == [1, 2, 3]


def test_convert_type_bool_false():
    assert convert_type(False, 'false') == False
    assert convert_type(True, 'false') == False


def test_convert_type_str_to_tuple():
    result = convert_type(('a',), 'hello')
    assert result == ('hello',)
    assert type(result) is tuple


def test_convert_type_error_message_with_path():
    with pytest.raises(TypeError, match='mykey'):
        convert_type({}, 5, path='mykey')
