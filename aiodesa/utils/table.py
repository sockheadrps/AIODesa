"""
Database Schema Definitions

Module provides classes and functions for defining database schema elements
such as primary keys, unique keys, foreign keys, and table schema.

Classes:
    `ForeignKey`: Represents a foreign key relationship in a database.
    `PrimaryKey`: Represents primary key columns in a database table.
    `UniqueKey`: Represents unique key column in a table.
    `TableSchema`: Represents the schema for a database table.

Functions:
    `set_key`: Decorator for setting primary keys, unique keys, and foreign
    keys on a class.
    `make_schema`: Generate a `TableSchema` based on the provided data class.

Usage examples can be found in the docstrings of each class and function.

Note:
    This module is intended for use with data classes and provides a convenient
    way to define database schema elements in Python code.
"""

from dataclasses import dataclass
from typing import Any, NamedTuple
from aiodesa.utils.util_types import py_to_sql_type


class ForeignKey(NamedTuple):
    """
    Represents a foreign key relationship in a database.
    Args:
        key: The column name representing the foreign key.
        table: The name of the referenced table.

    Example:

    .. code-block:: python

        @set_key(ForeignKey(key='user_id', table='users'))

    Note:
        Intended to be consumed by set_key() \n
    """

    key: str
    table: str


class PrimaryKey(NamedTuple):
    """
    Represents primary key columns in a database table.

    Args:
        column: Primary key identifer.

    Example:

    .. code-block:: python

        # Define a primary key with the column names 'user_id' and 'post_id':
        @set_key(PrimaryKey('user_id')


    Note:
        Intended to be consumed by set_key() \n
    """

    column: str


class UniqueKey(NamedTuple):
    """
    Represents unique key column in a table.

    Args:
        column: column name representing unique key.

    Example:

    .. code-block:: python

        # Define a unique key with the column names 'username' and 'email':
        user_unique_key = UniqueKey('username')

    Note:
        Intended to be consumed by set_key() \n
    """

    column: str


def set_key(*args: PrimaryKey | UniqueKey | ForeignKey | tuple[ForeignKey, ...]):
    """
    Decorator for setting keys on a class.

    Args:
        `*args`: The keys to be set. Can include PrimaryKey, UniqueKey,
        ForeignKey, or a tuple of ForeignKeys.

    Returns:
        A decorator function to set keys on a class.

    Example:

    .. code-block:: python

        @dataclass
        @set_key(PrimaryKey(
            "username"), UniqueKey("id"), ForeignKey("username", "anothertable"
            ))
        class Users:
            username: str
            id: str | None = None
            table_name: str = "users"

    Note:
        Foreign keys can be specified individually or as a tuple.
    """

    def decorator(cls):
        for arg in args:
            if isinstance(arg, PrimaryKey):
                if not hasattr(cls, "primary_key"):
                    cls.primary_key: str = arg.column

            elif isinstance(arg, UniqueKey):
                if not hasattr(cls, "unique_key"):
                    cls.unique_key: str = arg.column

            elif isinstance(arg, tuple):
                if not any(
                    isinstance(existing_key, (PrimaryKey, UniqueKey))
                    for existing_key in getattr(cls, "foreign_keys", ())
                ):
                    existing_foreign_keys = getattr(cls, "foreign_keys", ())
                    cls.foreign_keys = existing_foreign_keys + (arg,)

            elif isinstance(arg, ForeignKey):
                existing_foreign_keys = getattr(cls, "foreign_keys", ())
                cls.foreign_keys = existing_foreign_keys + arg

        return cls

    return decorator


@dataclass
class TableSchema:
    """
    Represents the schema for a database table.

    Args:
        table_name: The name of the table.
        data: The SQL data definition language (DDL) statement.

    Example:

    .. code-block:: python

        # Create a TableSchema for a 'users' table
        user_table_schema = TableSchema(
            table_name='users',
            data='CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);')

    Note:
        The `data` attribute contains the SQL data definition language (DDL).
    """

    table_name: str
    data: str


def make_schema(name: str, data_cls: Any) -> TableSchema:
    """
    Generate a TableSchema based on the provided data class.

    Args:
        name: The name of the table.
        data_cls: A data class defining the schema for the table.

    Returns:
        TableSchema: An instance of TableSchema containing the table_name and
        SQL data definition.

    Example:

    .. code-block:: python

        user_table_schema = generate_table_schema(name='users', data_cls=User)

    Note:
        The function returns a TableSchema instance containing the table_name
        and SQL data definition.
    """
    columns = []
    name = name.replace(" ", "_")
    for field_name, field_type in data_cls.__annotations__.items():
        if field_name == "table_name":
            pass
        else:
            columns.append(f"{field_name} {py_to_sql_type(field_type)}")
    if hasattr(data_cls, "primary_key"):
        columns.append(f"PRIMARY KEY ({data_cls.primary_key})")
    if hasattr(data_cls, "unique_key"):
        columns.append(f"UNIQUE ({data_cls.unique_key})")

    schema = TableSchema(
        name, f"CREATE TABLE IF NOT EXISTS {name} (\n{', '.join(columns)}\n);"
    )

    return schema
