"""
SQL Data and Type Utilities

This module provides utilities for working with SQL data types and defining data class protocols.

Classes:
    `SQLDataType`: Enumeration representing common SQL data types.
    `IsDataclass`: Protocol indicating that a class is a data class.

Functions:
    `py_to_sql_type`: Determine the SQL type of a Python primitive.

Usage Examples:

    1. SQL Data Types Enumeration:
        .. code-block:: python

            sql_type = SQLDataType.VARCHAR

    2. Determine SQL Type from Python Primitive:
        .. code-block:: python

            sql_type = py_to_sql_type("hello")
            print(sql_type)  # Output: "VARCHAR"

    3. Data Class Protocol:
        .. code-block:: python

        class MyDataClass(IsDataclass):
            __dataclass_fields__: ClassVar[Dict]

Note:
    `SQLDataType` provides a convenient way to represent common SQL data types.
    `py_to_sql_type` is used to determine the SQL type of a Python primitive.
    `IsDataclass` is a protocol indicating that a class is a data class.

"""
from enum import Enum
import builtins
from typing import Any
from types import UnionType


class SQLDataType(Enum):
    """
    Enumeration representing common SQL data types.
    """

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
    NONE = "NULL"
    PRIMARY = " PRIMARY KEY"
    UNIQUE = " UNIQUE KEY"


def py_to_sql_type(data: Any) -> str:
    """
    Determine the SQL type of a python primitive.

    Args:
        data: The Python variable / primitive.

    Returns:
        The corresponding SQL data type.

    Raises:
        ValueError: If the data type is not supported.

    Example:

    .. code-block:: python

        sql_type = py_to_sql_type("hello")
        print(sql_type)  # Output: "VARCHAR"

    """
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
        case builtins.bytes | builtins.bytearray | builtins.list | builtins.tuple | builtins.set | builtins.dict:
            return_type = "TEXT"
        case None:
            return_type = "NULL"
        case _:
            raise ValueError(f"Unsupported data type: {type(data)}")
    return return_type
