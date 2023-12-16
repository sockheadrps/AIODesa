from dataclasses import dataclass
from typing import Any, NamedTuple
from aiodesa.utils.types import py_to_sql_type


class ForeignKey(NamedTuple):
    """
    Represents a foreign key relationship in a database.

    Attributes:
    - key (str): The column name representing the foreign key.
    - table (str): The name of the referenced table.

    Example:
    .. code-block:: python

        # Define a foreign key with the column name 'user_id' referencing the 'users' table:
        user_foreign_key = ForeignKey(key='user_id', table='users')

    Note:
    - This class is a NamedTuple representing a foreign key relationship in a database.
    - The `key` attribute is the column name representing the foreign key.
    - The `table` attribute is the name of the referenced table.
    """

    key: str
    table: str


class PrimaryKey(NamedTuple):
    """
    Represents primary key columns in a database table.

    Attributes:
    - columns (Tuple[str]): Tuple of column names representing primary keys.

    Example:
    .. code-block:: python

        # Define a primary key with the column names 'user_id' and 'post_id':
        user_primary_key = PrimaryKey(columns=('user_id', 'post_id'))

    Note:
    - This class is a NamedTuple representing primary key columns in a database table.
    - The `columns` attribute is a tuple of column names representing primary keys.
    """

    column: str


class UniqueKey(NamedTuple):
    """
    Represents unique key columns in a database table.

    Attributes:
    - columns (Tuple[str]): Tuple of column names representing unique keys.

    Example:
    .. code-block:: python

        # Define a unique key with the column names 'username' and 'email':
        user_unique_key = UniqueKey(columns=('username', 'email'))

    Note:
    - This class is a NamedTuple representing unique key columns in a database table.
    - The `columns` attribute is a tuple of column names representing unique keys.
    """

    column: str


class UpdateRecord(NamedTuple):
    """
    Represents a record update in a database table.

    Attributes:
    - column_name (str): The name of the column to be updated.
    - value (Any): The new value to set for the specified column.

    Example:
    .. code-block:: python

        # Define an update record for changing the 'email' column to 'new_email@example.com':
        update_email_record = UpdateRecord(column_name='email', value='new_email@example.com')

    Note:
    - This class is a NamedTuple representing a record update in a database table.
    - The `column_name` attribute is the name of the column to be updated.
    - The `value` attribute is the new value to set for the specified column.
    """

    column_name: str
    value: Any


def set_key(*args: PrimaryKey | UniqueKey | ForeignKey | tuple[ForeignKey, ...]):
    """
    Decorator for setting primary keys, unique keys, and foreign keys on a class.

    Parameters:
    - `*args` (PrimaryKey | UniqueKey | ForeignKey | Tuple[ForeignKey, ...]):
    The keys to be set. Can include PrimaryKey, UniqueKey, ForeignKey, or a tuple of ForeignKeys.

    Returns:
    - Callable[[Type], Type]: A decorator function to set keys on a class.

    Example:
    .. code-block:: python

        @YourClass.set_key(PrimaryKey("id"), UniqueKey("username"))
        class YourModel:
        #    Class definition

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

    Parameters:
    - table_name (str): The name of the table.
    - data (str): The SQL data definition language (DDL) statement for creating the table.

    Example:
    .. code-block:: python

        # Create a TableSchema for a 'users' table
        user_table_schema = TableSchema(table_name='users', data='CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);')

    Note:
    - This class is decorated with the @dataclass decorator for concise attribute initialization.
    - The `table_name` attribute represents the name of the table.
    - The `data` attribute contains the SQL data definition language (DDL) statement for creating the table.
    """

    table_name: str
    data: str


def make_schema(name: str, data_cls: Any) -> TableSchema:
    """
    Generate a TableSchema based on the provided data class.

    Parameters:
    - name (str): The name of the table.
    - data_cls (Type): A data class defining the schema for the table.

    Returns:
    - TableSchema: An instance of TableSchema containing the table_name and SQL data definition.

    Example:
    .. code-block:: python

        # Generate a TableSchema for a 'users' table based on the User data class
        user_table_schema = generate_table_schema(name='users', data_cls=User)

    Note:
    - The `name` parameter represents the name of the table.
    - The `data_cls` parameter is the data class defining the schema for the table.
    - The function returns a TableSchema instance containing the table_name and SQL data definition.
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
