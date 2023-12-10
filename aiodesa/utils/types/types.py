from enum import Enum
from typing import Any
from enum import Enum
import builtins


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
            raise ValueError(f"Unsupported data type: {type(data)}")

    return return_type
