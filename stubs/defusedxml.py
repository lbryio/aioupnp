import typing


class ElementTree:
    tag: typing.Optional[str] = None
    """The element's name."""

    attrib: typing.Optional[typing.Dict[str, str]] = None
    """Dictionary of the element's attributes."""

    text: typing.Optional[str] = None

    tail: typing.Optional[str] = None

    def __len__(self) -> int:
        raise NotImplementedError()

    def __iter__(self) -> typing.Iterator['ElementTree']:
        raise NotImplementedError()

    @classmethod
    def fromstring(cls, xml_str: str) -> 'ElementTree':
        raise NotImplementedError()