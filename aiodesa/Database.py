from dataclasses import is_dataclass, fields
from typing import Tuple, Callable, Any
from pathlib import Path
import aiosqlite
from aiodesa.utils.tables import make_schema, TableSchema
from aiodesa.utils.types import IsDataclass


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

    def insert(self, data_class: is_dataclass) -> Callable[..., None]:
        """
        Create a record and insert it into the specified table.

        Parameters:
        - data_class (Type): The data class representing the table structure.

        Returns:
        - Callable[..., None]: A function to be called with the record data.

        Example:
        ```python
        insert_user = your_database_instance.insert(User)
        await insert_user(username="john_doe", email="john@example.com")
        ```
        """

        async def record(*args: Any, **kwargs: Any) -> None:
            """
            Insert a record into the specified table.


            Arguments:
            - *args: Positional arguments representing the record data. (e.g., str, int, ...)
            - **kwargs: Keyword arguments representing the record data. (e.g., username=str, email=str, ...)

            Example:
            ```python
            await record(username="john_doe", email="john@example.com")
            ```
            """
            data_cls = self.tables[data_class.table_name](*args, **kwargs)
            field_vals = {}
            for field in fields(data_cls):
                value = getattr(data_cls, field.name)
                if value is not None and value != data_cls.table_name:
                    field_vals[field.name] = value

            insertion_vals = tuple(field_vals.values())

            columns_str = ", ".join(field_vals.keys())
            placeholders = ", ".join("?" for _ in insertion_vals)
            sql = f"INSERT INTO {data_class.table_name} ({columns_str}) VALUES ({placeholders});"
            await self.conn.execute(sql, insertion_vals)
            await self.conn.commit()

        return record

    def update(
        self, data_class: is_dataclass, column_identifier: None | str = None
    ) -> Callable[..., None]:
        """
        Create a record update operation for the specified table.

        Parameters:
        - data_class (Type[YourDataClass]): The data class representing the table structure.
        - column_identifier (None | str): The column to use for identifying records.

        Returns:
        - Callable[..., None]: A function to be called with the record data for updating.

        Example:
        ```python
        update_user = your_database_instance.update(User)
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
            data_cls = self.tables[data_class.table_name](*args, **kwargs)
            values = []
            set_clauses_placeholders = []
            for column, value in kwargs.items():
                values.append(value)
                set_clause = f"{column} = ?"
                set_clauses_placeholders.append(set_clause)
            set_clause_string = ", ".join(set_clauses_placeholders)
            values.append(data_cls.username)
            identifier = (
                column_identifier
                if column_identifier is not None
                else data_cls.primary_key
            )
            sql = f"UPDATE {data_class.table_name} SET {set_clause_string} WHERE {identifier} = ?"

            await self.conn.execute(sql, tuple(values))
            await self.conn.commit()

        return record

    def find(
        self, data_class: is_dataclass, column_identifier: None | str = None
    ) -> Callable[..., None]:
        """
        Create a record retrieval operation for the specified table.

        Parameters:
        - data_class (Type[YourDataClass]): The data class representing the table structure.
        - column_identifier (None | str): The column to use for identifying records.

        Returns:
        - Callable[..., None]: A function to be called with the identifier for record retrieval.

        Example:
        ```python
        find_user = your_database_instance.find(User, column_identifier="username")
        user_instance = await find_user("john_doe")
        ```

        The returned function can be called with the identifier to retrieve a record from the specified table.

        Args:
        - *args: Positional arguments representing the identifier for record retrieval.
        - **kwargs: Keyword arguments representing the identifier for record retrieval.

        Example:
        ```python
        user_instance = await record("john_doe")
        ```

        The record retrieval operation fetches a record from the specified table based on the provided identifier.

        Returns:
        - Type[YourDataClass]: An instance of the data class representing the retrieved record.
        """

        async def record(*args, **kwargs) -> None:
            data_cls = self.tables[data_class.table_name](*args, **kwargs)
            identifier = (
                column_identifier
                if column_identifier is not None
                else data_cls.primary_key
            )
            results = []
            sql = f"SELECT * FROM {data_cls.table_name} WHERE {identifier} = ?"
            sql_args = (args[0],)
            async with self.conn.execute(sql, sql_args) as cursor:
                results = await cursor.fetchall()
            username_tuple = results[0]
            data_cls = data_class(*username_tuple, *results[1:])

            return data_cls

        return record

    def delete(
        self, data_class: is_dataclass, column_identifier: None | str = None
    ) -> Callable[..., None]:
        """
        Create a record deletion operation for the specified table.

        Parameters:
        - data_class (Type[YourDataClass]): The data class representing the table structure.
        - column_identifier (None | str): The column to use for identifying records.

        Returns:
        - Callable[..., None]: A function to be called with the identifier for record deletion.

        Example:
        ```python
        delete_user = your_database_instance.delete(User, column_identifier="username")
        await delete_user("john_doe")
        ```

        The returned function can be called with the identifier to delete a record from the specified table.

        Args:
        - *args: Positional arguments representing the identifier for record deletion.
        - **kwargs: Keyword arguments representing the identifier for record deletion.

        Example:
        ```python
        await delete_record("john_doe")
        ```

        The record deletion operation removes a record from the specified table based on the provided identifier.
        """

        async def delete_record(*args, **kwargs) -> None:
            data_cls = self.tables[data_class.table_name](*args, **kwargs)
            identifier = (
                column_identifier
                if column_identifier is not None
                else data_cls.primary_key
            )

            sql = f"DELETE FROM {data_cls.table_name} WHERE {identifier} = ?"
            sql_args = (args[0],)

            async with self.conn.execute(sql, sql_args) as cursor:
                await cursor.fetchall()
            await self.conn.commit()

        return delete_record

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
