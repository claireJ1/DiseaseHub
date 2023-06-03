from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SendRequest(_message.Message):
    __slots__ = ["data", "data_source", "dataset_type", "event_type", "name", "token"]
    DATASET_TYPE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    DATA_SOURCE_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    data: str
    data_source: str
    dataset_type: str
    event_type: str
    name: str
    token: str
    def __init__(self, token: _Optional[str] = ..., name: _Optional[str] = ..., data: _Optional[str] = ..., data_source: _Optional[str] = ..., dataset_type: _Optional[str] = ..., event_type: _Optional[str] = ...) -> None: ...

class SendResponse(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...
