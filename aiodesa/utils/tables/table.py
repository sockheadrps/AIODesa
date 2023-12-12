from dataclasses import dataclass
from typing import Any, NamedTuple
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


class UpdateRecord(NamedTuple):
    column_name: str
    value: Any


def set_key(*args: PrimaryKey | UniqueKey | ForeignKey | tuple[ForeignKey, ...]):
    """
    Decorator for setting primary keys, unique keys, and foreign keys on a class.

    Parameters:
    - *args (PrimaryKey | UniqueKey | ForeignKey | tuple[ForeignKey, ...]):
        The keys to be set. Can include PrimaryKey, UniqueKey, ForeignKey, or a tuple of ForeignKeys.

    Returns:
    - Callable[[Type], Type]: A decorator function to set keys on a class.

    Example:
    ```python
    @YourClass.set_key(PrimaryKey("id"), UniqueKey("username"))
    class YourModel:
        # Class definition
    ```

    Note:
    - When using tuples for ForeignKeys, make sure not to include PrimaryKey or UniqueKey instances within the tuple.
    - Foreign keys can be specified individually or as a tuple.

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
    if hasattr(data_cls, "primary_key"):
        columns.append(f"PRIMARY KEY ({data_cls.primary_key})")
    if hasattr(data_cls, "unique_key"):
        columns.append(f"UNIQUE ({data_cls.unique_key})")

    schema = TableSchema(
        name, f"CREATE TABLE IF NOT EXISTS {name} (\n{', '.join(columns)}\n);"
    )

    return schema
