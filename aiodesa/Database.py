from dataclasses import is_dataclass, fields
from typing import Tuple, Callable, Any
from pathlib import Path
import aiosqlite
from aiodesa.utils.tables import make_schema, TableSchema
from aiodesa.utils.types import IsDataclass
from aiodesa.utils.records import (
    get_field_names,
    get_field_values,
    get_non_none_columns,
)


class Db:
    """
    Represents a simple SQLite database interface.

    Parameters
    ----------
    db_path : str
                    The path to the SQLite database file.

    Attributes
    ----------
    db_path : pathlib.Path
                    The path to the SQLite database file.
    conn : aiosqlite.Connection or None
                    The SQLite database connection object. Initialized as None until the database is connected.

    Methods
    -------
    _create_db()
                    Internal method to create the database file if it does not exist.
    read_table_schemas(schema)
                    Read table schemas and create tables in the database based on the provided schema.
    table_exists(table_name)
                    Check if a table with the specified name exists in the database.
    create_table(named_data, name)
                    Create a table in the database based on the provided TableSchema instance.
    connect()
                    Establish a connection to the SQLite database.
    close()
                    Close the connection to the SQLite database.
    __aenter__()
                    Async context manager entry point to automatically connect to the database.
    __aexit__(exc_type, exc_value, traceback)
                    Async context manager exit point to automatically close the database connection.
    """

    tables: dict
    db_path: Path
    conn: Any

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.conn = None
        self._create_db()
        self.tables = {}

    def _create_db(self) -> None:
        """
        Internal method to create the database file if it does not exist.
        Notes
        -----
        This method is automatically called during the initialization of the Db class.
        It ensures that the SQLite database file is created at the specified path if it does not exist.
        """
        if self.db_path.exists():
            self.db_path.unlink()
            print(f"Database {self.db_path.name} deleted successfully.")
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_path.touch()

    async def read_table_schemas(
        self, schema: IsDataclass | Tuple[IsDataclass, ...]
    ) -> None:
        """
        Read table schemas and create tables in the database based on the provided schema.

        Parameters
        ----------
        schema : Union[type, Tuple[type, ...], str]
                        The schema definition, which can be a single dataclass, a tuple of dataclasses,
                        or the path to a .py file containing dataclass objects.
        """
        self.tables[schema.table_name] = schema
        # single dataclass
        if is_dataclass(schema):
            class_fields = fields(schema)
            for field in class_fields:
                if field.name == "table_name":
                    schema_ = make_schema(str(field.default), schema)
                    await self.create_table(schema_, field.name)
            return

        # tuple of dataclasses
        if isinstance(schema, tuple):
            for class_obj in schema:
                class_fields = fields(class_obj)
                for field in class_fields:
                    if field.name == "table_name":
                        schema_ = make_schema(str(field.default), class_obj)
                        await self.create_table(schema_, field.name)
            return

    async def table_exists(self, table_name: str) -> bool | None:
        """
        Check if a table with the specified name exists in the database.

        Parameters
        ----------
        table_name : str
                        The name of the table to check.

        Returns
        -------
        Optional[bool]
                        True if the table exists, False otherwise.
        """
        if self.conn is not None:
            query = f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
            cursor = await self.conn.execute(query, (table_name,))
            return await cursor.fetchone() is not None
        else:
            return None

    async def create_table(self, named_data: TableSchema, name: str) -> None:
        """
        Create a table in the database based on the provided TableSchema instance.

        Parameters
        ----------
        named_data : TableSchema
                        The TableSchema instance containing the table_name and SQL data definition.
        name : str
                        The name of the table.
        """
        if self.conn is not None:
            if not await self.table_exists(name):
                async with self.conn.executescript(named_data.data) as cursor:
                    await cursor.fetchall()
                await self.conn.commit()

    def insert(self, table_name: str) -> Callable[..., None]:
        """
        Create a record and insert it into the specified table.

        Parameters:
        - table_name (str): The name of the table to insert the record into.

        Returns:
        - Callable[..., None]: A function to be called with the record data.

        Example:
        ```python
        insert_user = your_database_instance.insert("users")
        await insert_user(username="john_doe", email="john@example.com")
        ```
        """

        async def record(*args: Any, **kwargs: Any) -> None:
            """
            Insert a record into the specified table.

            Arguments:
            - *args: Positional arguments representing the record data.
            - **kwargs: Keyword arguments representing the record data.

            Example:
            ```python
            await record(username="john_doe", email="john@example.com")
            ```
            """
            data_cls = self.tables[table_name](*args, **kwargs)
            field_vals = {}
            for field in fields(data_cls):
                value = getattr(data_cls, field.name)
                if value is not None and value != data_cls.table_name:
                    field_vals[field.name] = value

            insertion_vals = tuple(field_vals.values())

            columns_str = ", ".join(field_vals.keys())
            placeholders = ", ".join("?" for _ in insertion_vals)
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"
            await self.conn.execute(sql, insertion_vals)
            await self.conn.commit()

        return record

    def update(self, table_name: str, column_identifier: str) -> Callable[..., None]:
        """
        Create a record update operation for the specified table.

        Parameters:
        - table_name (str): The name of the table to update records in.

        Returns:
        - Callable[..., None]: A function to be called with the record data for updating.

        Example:
        ```python
        update_user = your_database_instance.update("users")
        await update_user(username="john_doe", email="john@example.com")
        ```
        """

        async def record(*args, **kwargs) -> None:
            """
            Update records in the specified table.

            Arguments:
            - *args: Positional arguments representing the record data.
            - **kwargs: Keyword arguments representing the record data.

            Example:
            ```python
            await record(username="john_doe", email="john@example.com")
            ```
            """
            data_cls = self.tables[table_name](*args, **kwargs)
            field_names = get_field_names(data_cls)
            field_names.remove(column_identifier)
            values = get_field_values(data_cls, field_names)
            tup = (values[0], args[0])
            non_none_columns = get_non_none_columns(field_names, values)
            set_clauses_placeholders = []
            for column in non_none_columns:
                set_clause = f"{column[0]} = ?"
                set_clauses_placeholders.append(set_clause)

            set_clause_string = ", ".join(set_clauses_placeholders)

            sql = f"UPDATE {table_name} SET {set_clause_string} WHERE username = ?"

            await self.conn.execute(sql, tup)
            await self.conn.commit()

        return record

    def update(self, table_name: str, column_identifier: str) -> Callable[..., None]:
        """
        Create a record update operation for the specified table.

        Parameters:
        - table_name (str): The name of the table to update records in.
        - column_identifier (str): The column used to identify the record.

        Returns:
        - Callable[..., None]: A function to be called with the record data for updating.

        Example:
        ```python
        update_user = your_database_instance.update("users", "username")
        await update_user(username="john_doe", email="john@example.com")
        ```
        """

        async def record(*args: Any, **kwargs: Any) -> None:
            """
            Update records in the specified table.

            Arguments:
            - *args: Positional arguments representing the record data.
            - **kwargs: Keyword arguments representing the record data.

            Example:
            ```python
            await record(username="john_doe", email="john@example.com")
            ```
            """
            data_cls = self.tables[table_name](*args, **kwargs)

            field_vals = {}
            for field in fields(data_cls):
                if field.name != column_identifier:
                    value = getattr(data_cls, field.name)
                    if value is not None and value != data_cls.table_name:
                        field_vals[field.name] = value
                else:
                    # Always the value we're identifying on
                    field_vals[field.name] = args[0]

            record_identifier = field_vals[column_identifier]
            del field_vals[column_identifier]
            insertion_vals = tuple(field_vals.values()) + (record_identifier,)

            set_clauses_placeholders = [f"{column} = ?" for column in field_vals.keys()]
            set_clause_string = ", ".join(set_clauses_placeholders)

            sql = f"UPDATE {table_name} SET {set_clause_string} WHERE {column_identifier} = ?"
            await self.conn.execute(sql, insertion_vals)
            await self.conn.commit()

        return record

    async def connect(self) -> None:
        """
        Establish a connection to the SQLite database.
        """
        self.conn = await aiosqlite.connect(self.db_path)

    async def close(self) -> None:
        """
        Close the connection to the SQLite database.
        """
        if self.conn is not None:
            await self.conn.close()

    async def __aenter__(self) -> "Db":
        """
        Async context manager entry point to automatically connect to the database.

        Returns
        -------
        Db
                        The Db instance with an active database connection.
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Async context manager exit point to automatically close the database connection.
        """
        await self.close()
