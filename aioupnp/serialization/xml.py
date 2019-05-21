import typing
from collections import OrderedDict
from defusedxml import ElementTree

str_any_dict = typing.Dict[str, typing.Any]


def parse_xml(xml_str: str) -> ElementTree:
    element: ElementTree = ElementTree.fromstring(xml_str)
    return element


def _element_text(element_tree: ElementTree) -> typing.Optional[str]:
    # if element_tree.attrib:
    #     element: typing.Dict[str, str] = OrderedDict()
    #     for k, v in element_tree.attrib.items():
    #         element['@' + k] = v
    #     if not element_tree.text:
    #         return element
    #     element['#text'] = element_tree.text.strip()
    #     return element
    if element_tree.text:
        return element_tree.text.strip()
    return None


def _get_element_children(element_tree: ElementTree) -> typing.Dict[str, typing.Union[
                                                     str, typing.List[typing.Union[typing.Dict[str, str], str]]]]:
    element_children = _get_child_dicts(element_tree)
    element: typing.Dict[str, typing.Any] = OrderedDict()
    keys: typing.List[str] = list(element_children.keys())
    for k in keys:
        v: typing.Union[str, typing.List[typing.Any], typing.Dict[str, typing.Any]] = element_children[k]
        if len(v) == 1 and isinstance(v, list):
            l: typing.List[typing.Union[typing.Dict[str, str], str]] = v
            element[k] = l[0]
        else:
            element[k] = v
    return element


def _get_child_dicts(element: ElementTree) -> typing.Dict[str, typing.List[typing.Union[typing.Dict[str, str], str]]]:
    children_dicts: typing.Dict[str, typing.List[typing.Union[typing.Dict[str, str], str]]] = OrderedDict()
    children: typing.List[ElementTree] = list(element)
    for child in children:
        child_dict = _recursive_element_to_dict(child)
        child_keys: typing.List[str] = list(child_dict.keys())
        for k in child_keys:
            assert k in child_dict
            v: typing.Union[typing.Dict[str, str], str] = child_dict[k]
            if k not in children_dicts.keys():
                new_item = [v]
                children_dicts[k] = new_item
            else:
                sublist = children_dicts[k]
                assert isinstance(sublist, list)
                sublist.append(v)
    return children_dicts


def _recursive_element_to_dict(element_tree: ElementTree) -> typing.Dict[str, typing.Any]:
    if len(element_tree):
        element_result: typing.Dict[str, typing.Dict[str, typing.Union[
            str, typing.List[typing.Union[str, typing.Dict[str, typing.Any]]]]]] = OrderedDict()
        children_element = _get_element_children(element_tree)
        if element_tree.tag is not None:
            element_result[element_tree.tag] = children_element
        return element_result
    else:
        element_text = _element_text(element_tree)
        if element_text is not None:
            base_element_result: typing.Dict[str, typing.Any] = OrderedDict()
            if element_tree.tag is not None:
                base_element_result[element_tree.tag] = element_text
            return base_element_result
    null_result: typing.Dict[str, str] = OrderedDict()
    return null_result


def xml_to_dict(xml_str: str) -> typing.Dict[str, typing.Any]:
    return _recursive_element_to_dict(parse_xml(xml_str))
