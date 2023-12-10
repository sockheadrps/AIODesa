from dataclasses import dataclass
from collections import namedtuple
from typing import Tuple, Any, NamedTuple
from aiodesa.utils.types import py_to_sql_type


class ForeignKey(NamedTuple):
    """
    Represents a foreign key relationship in a database.

    Attributes:
        key (str): The column name representing the foreign key.
        table (str): The name of the referenced table.

    Example:
        Define a foreign key with the column name 'user_id' referencing the 'users' table:

        >>> user_foreign_key = ForeignKey(key='user_id', table='users')

    Attributes:
        key (str): The column name representing the foreign key.
        table (str): The name of the referenced table.
    """

    key: str
    table: str


class PrimaryKey(NamedTuple):
    """
    Represents primary key columns in a database table.

    Attributes:
        columns (Tuple[str]): Tuple of column names representing primary keys.

    Example:
        Define a primary key with the column names 'user_id' and 'post_id':

        >>> user_primary_key = PrimaryKey(columns=('user_id', 'post_id'))

    Attributes:
        column str: Column name representing primary key.
    """

    column: str


class UniqueKey(NamedTuple):
    """
    Represents unique key columns in a database table.

    Attributes:
        columns (Tuple[str]): Tuple of column names representing unique keys.

    Example:
        Define a unique key with the column names 'username' and 'email':

        >>> user_unique_key = UniqueKey(columns=('username', 'email'))

    Attributes:
        columns str: Column name representing unique keys
    """

    column: str


def foreign_key(*foreign_keys: Tuple[str, str]):
    """
    Decorator to specify foreign keys for a database table.

    Args:
        *foreign_keys (Tuple[str, str]): One or more tuples representing foreign key relationships.
            Each tuple should contain two strings: the column name representing the foreign key
            and the name of the referenced table.

    Returns:
        Callable: A decorator function.

    Usage:
        @foreign_key(('other_table', 'other_column'), ('another_table', 'another_column'))
        @dataclass
        class Table:
            username: str
            credits: int
            points: int
            table_name: str = "user_econ"
    """

    def decorator(cls):
        existing_foreign_keys = getattr(cls, "foreign_keys", ())
        cls.foreign_keys: Tuple[Tuple[str, str], ...] = (
            existing_foreign_keys + foreign_keys
        )
        return cls

    return decorator


def primary_key(primary_key: str):
    """
    Decorator to specify primary key for a database table.

    Args:
        primary_key (str): A string representing primary key column name.

    Returns:
        Callable: A decorator function.

    Usage:
        @primary_key('username')
        @dataclass
        class Table:
            username: str
            credits: int
            points: int
            table_name: str = "user_econ"
    """

    def decorator(cls):
        cls.primary_key: str = primary_key
        return cls

    return decorator


def unique_key(unique_key: str):
    """
    Decorator to specify unique key for a database table.

    Args:
        unique_key (str): A string representing unique key column name.

    Returns:
        Callable: A decorator function.

    Usage:
        @unique_key('username')
        @dataclass
        class Table:
            username: str
            credits: int
            points: int
            table_name: str = "user_econ"
    """

    def decorator(cls):
        cls.unique_key: str = unique_key
        return cls

    return decorator


@dataclass
class TableSchema:
    """
    Represents the schema for a database table.

    Parameters
    ----------
    table_name : str
        The name of the table.
    data : str
        The SQL data definition language (DDL) statement for creating the table.
    """

    table_name: str
    data: str


def make_schema(name: str, data_cls: Any) -> TableSchema:
    """
    Generate a TableSchema based on the provided data class.

    Parameters
    ----------
    name : str
        The name of the table.
    data_cls : type
        A data class defining the schema for the table.

    Returns
    -------
    TableSchema
        An instance of TableSchema containing the table_name and SQL data definition.
    """
    columns = []
    name = name.replace(" ", "_")
    for field_name, field_type in data_cls.__annotations__.items():
        if field_name == "table_name":
            pass
        else:
            columns.append(f"{field_name} {py_to_sql_type(field_type)}")

    if isinstance(data_cls.primary_key, PrimaryKey):
        columns.append(f"PRIMARY KEY ({', '.join(data_cls.primary_key)})")
    if isinstance(data_cls.primary_key, UniqueKey):
        columns.append(f"UNIQUE KEY ({', '.join(data_cls.primary_key)})")

    schema = TableSchema(
        name, f"CREATE TABLE IF NOT EXISTS {name} (\n{', '.join(columns)}\n);"
    )

    return schema
