from enum import Enum
from enum import Enum
import builtins
from typing import ClassVar, Dict, Protocol, Any
from types import UnionType


class SQLDataType(Enum):
    INT = "INT"
    VARCHAR = "VARCHAR"
    CHAR = "CHAR"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    FLOAT = "FLOAT"
    DATE = "DATE"
    DATETIME = "DATETIME"
    DECIMAL = "DECIMAL"
    DOUBLE = "DOUBLE"
    INTEGER = "INTEGER"
    SMALLINT = "SMALLINT"
    BIGINT = "BIGINT"
    PRIMARY = " PRIMARY KEY"
    UNIQUE = " UNIQUE"


def py_to_sql_type(data: Any) -> str:
    if isinstance(data, UnionType):
        tmp = data.__args__
        if len(tmp) == 2:
            if tmp[0]() is None:
                data = tmp[1]
            elif tmp[1]() is None:
                data = tmp[0]

        match data:
            case builtins.int:
                return_type = "INT"
            case builtins.str:
                return_type = "VARCHAR"
            case builtins.float:
                return_type = "FLOAT"
            case builtins.bool:
                return_type = "BOOLEAN"
            case builtins.bytes, builtins.bytearray, builtins.list, builtins.tuple, builtins.set, builtins.dict:
                return_type = "TEXT"
            case None:
                return_type = "TEXT"
            case _:
                print(data.__args__[0])
                raise ValueError(f"Unsupported data type: {type(data)}")
        return return_type


class IsDataclass(Protocol):
    __dataclass_fields__: ClassVar[Dict]
