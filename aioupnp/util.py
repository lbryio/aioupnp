import typing
from collections import OrderedDict


str_any_dict = typing.Dict[str, typing.Any]


def _recursive_flatten(to_flatten: typing.Any, strip: str) -> typing.Any:
    if not isinstance(to_flatten, (list, dict)):
        return to_flatten
    if isinstance(to_flatten, list):
        assert isinstance(to_flatten, list)
        return [_recursive_flatten(i, strip) for i in to_flatten]
    assert isinstance(to_flatten, dict)
    keys: typing.List[str] = list(to_flatten.keys())
    copy: str_any_dict = OrderedDict()
    for k in keys:
        item: typing.Any = to_flatten[k]
        if strip in k and strip != k:
            copy[k.split(strip)[1]] = _recursive_flatten(item, strip)
        else:
            copy[k] = _recursive_flatten(item, strip)
    return copy


def flatten_keys(to_flatten: str_any_dict, strip: str) -> str_any_dict:
    keys: typing.List[str] = list(to_flatten.keys())
    copy: str_any_dict = OrderedDict()
    for k in keys:
        item = to_flatten[k]
        if strip in k and strip != k:
            new_key: str = k.split(strip)[1]
            copy[new_key] = _recursive_flatten(item, strip)
        else:
            copy[k] = _recursive_flatten(item, strip)
    return copy


def get_dict_val_case_insensitive(source: typing.Dict[typing.AnyStr, typing.AnyStr],
                                  key: typing.AnyStr) -> typing.Optional[typing.AnyStr]:
    match: typing.List[typing.AnyStr] = list(filter(lambda x: x.lower() == key.lower(), source.keys()))
    if not len(match):
        return None
    if len(match) > 1:
        raise KeyError("overlapping keys")
    if len(match) == 1:
        matched_key: typing.AnyStr = match[0]
        return source[matched_key]
    raise KeyError("overlapping keys")
