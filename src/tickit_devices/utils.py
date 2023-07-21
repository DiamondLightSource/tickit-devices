from typing import Any, List, Mapping, Union

from pydantic.v1 import BaseModel

_Serialized = Union[str, float, int, bool, List[Any], Mapping[str, Any]]
_Serializable = Union[_Serialized, BaseModel]


def serialize(document: _Serializable) -> _Serialized:
    """Helper to serialize using pydantic base models

    Args:
        document: A JSON-serializable document or base model

    Raises:
        TypeError: If the document cannot be serialized

    Returns:
        _Serialized: A JSON-serializable document
    """

    if (
        isinstance(document, str)
        or isinstance(document, float)
        or isinstance(document, int)
        or isinstance(document, bool)
        or isinstance(document, list)
        or isinstance(document, dict)
    ):
        return document
    elif isinstance(document, BaseModel):
        return document.dict(by_alias=True)
    else:
        raise TypeError(f"Document {document} is of unrecognized type {type(document)}")
