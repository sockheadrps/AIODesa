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

        Notes:
        - This method is automatically called during the initialization of the Db class.
        - It ensures that the SQLite database file is created at the specified path if it does not exist.
        """
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_path.touch()

    async def read_table_schemas(
        self, schema: IsDataclass | Tuple[IsDataclass, ...]
    ) -> None:
        """
        Check if a table with the specified name exists in the database.

        Parameters:
        - table_name (str): The name of the table to check.

        Returns:
        - Optional[bool]: True if the table exists, False otherwise.

        Example:
        .. code-block:: python

            if your_database_instance.table_exists("users"):
                print("The 'users' table exists.")
            else:
                print("The 'users' table does not exist.")


        This method returns True if a table with the specified name exists in the database; otherwise, it returns False.

        Args:
        - table_name: The name of the table to check for existence.

        Note:
        This method provides an optional boolean result, as it may return None if there are issues determining table existence.
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
        Create a table in the database based on the provided TableSchema instance.

        Parameters:
        - named_data (TableSchema): The TableSchema instance containing the table_name and SQL data definition.
        - name (str): The name of the table.

        Returns:
        None

        Example:
        ```python
        table_schema = TableSchema(table_name="users", sql_definition="id INTEGER PRIMARY KEY, name TEXT, email TEXT")
        your_database_instance.create_table(table_schema, name="users")
        ```

        This method creates a table in the database with the specified name and schema.

        Args:
        - named_data: An instance of TableSchema representing the schema definition for the table.
        - name: The name to be assigned to the table in the database.

        Note:
        The `named_data` parameter should include the `table_name` property for the name of the table
        and the `sql_definition` property for the SQL data definition of the table.
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

        Parameters:
        - named_data (TableSchema): The TableSchema instance containing the table_name and SQL data definition.
        - name (str): The name of the table.

        Returns:
        None

        Example:
        ```python
        table_schema = TableSchema(table_name="users", sql_definition="id INTEGER PRIMARY KEY, name TEXT, email TEXT")
        your_database_instance.create_table(table_schema, name="users")
        ```

        This method creates a table in the database with the specified name and schema.

        Args:
        - named_data: An instance of TableSchema representing the schema definition for the table.
        - name: The name to be assigned to the table in the database.

        Note:
        The `named_data` parameter should include the `table_name` property for the name of the table
        and the `sql_definition` property for the SQL data definition of the table.
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
        - data_class (Type[YourDataClass]): The data class representing the table structure.

        Returns:
        - Callable[..., None]: A function to be called with the record data.

        Example:
        .. code-block:: python

            insert_user = your_database_instance.insert(User)
            await insert_user(username="john_doe", email="john@example.com")


        The returned function can be called with the record data to insert a new record into the specified table.

        Args:
        - `**kwargs`: Keyword arguments representing the data for the new record.

        Example:
        .. code-block:: python

            await insert_record(username="john_doe", email="john@example.com")


        The record insertion operation adds a new record to the specified table.

        Note:
        The primary key of the data class will be automatically generated if it is not provided in the record data.
        """

        async def record(*args: Any, **kwargs: Any) -> None:
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
        - column_identifier (Optional[str]): The column to use for identifying records.

        Returns:
        - Callable[..., None]: A function to be called with the record data for updating.

        Example:
        .. code-block:: python

            update_user = your_database_instance.update(User)
            await update_user(username="john_doe", email="john@example.com")


        The returned function can be called with the record data to update a record in the specified table.

        Args:
        - `**kwargs`: Keyword arguments representing the updated data for the record.

        Example:
        .. code-block:: python

            await update_record(username="john_doe", email="john@example.com")


        The record update operation modifies a record in the specified table based on the provided identifier.

        Note:
        If the `column_identifier` is not provided, the primary key of the data class will be used as the identifier.
        """

        async def record(*args, **kwargs) -> None:
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
        - column_identifier (Optional[Union[None, str]]): The column to use for identifying records.
        Defaults to the primary key of the data class if not specified.

        Returns:
        - Callable[..., None]: A function to be called with the identifier for record retrieval.

        Example:
        .. code-block:: python

            find_user = your_database_instance.find(User, column_identifier="username")
            user_record = await find_user("john_doe")


        The returned function can be called with the identifier to retrieve a record from the specified table.

        Args:
        - `*args`: Positional arguments representing the identifier for record retrieval.
        - `**kwargs`: Keyword arguments representing the identifier for record retrieval.

        Returns:
        Type[YourDataClass]: An instance of the data class representing the retrieved record.

        Example:
        .. code-block:: python

            user_record = await find_record("john_doe")

        The record retrieval operation fetches a record from the specified table based on the provided identifier.
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
        .. code-block:: python

            delete_user = your_database_instance.delete(User, column_identifier="username")
            await delete_user("john_doe")

        The returned function can be called with the identifier to delete a record from the specified table.

        Args:
        - `*args`: Positional arguments representing the identifier for record deletion.
        - `**kwargs`: Keyword arguments representing the identifier for record deletion.

        Example:
        .. code-block:: python

            await delete_record("john_doe")

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

        Returns:
        None

        Example:
        ```python
        connection = YourDatabaseConnection()
        await connection.connect()
        # The database connection is now established.
        ```

        Note:
        This method initializes the connection to the SQLite database using the provided `db_path`.
        """
        self.conn = await aiosqlite.connect(self.db_path)

    async def close(self) -> None:
        """
        Close the connection to the SQLite database.

        Returns:
        None

        Example:
        .. code-block:: python

            connection = YourDatabaseConnection()
            await connection.connect()

        # Your database operations here

        await connection.close()
        # The database connection is now closed.

        Note:
        This method closes the connection to the SQLite database if it is open.
        """
        if self.conn is not None:
            await self.conn.close()

    async def __aenter__(self) -> "Db":
        """
        Asynchronous context manager entry point.

        Automatically connects to the database upon entering the context.

        Returns:
        Db:
            The Db instance with an active database connection.

        Example:
        .. code-block:: python

            async with YourDatabaseConnection() as connection:
                # Your asynchronous code here

        # Upon entering the context, the database connection is automatically established.

        Note:
        This method is intended for use with the `async with` statement in an asynchronous context manager.
        The returned `Db` instance represents the connection to the database.
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Asynchronous context manager exit point.

        Automatically closes the database connection upon exiting the context.

        Parameters:
        - exc_type (Type): The type of the exception raised, if any.
        - exc_value (Exception): The exception object, if an exception occurred. Otherwise, None.
        - traceback (TracebackType): The traceback information related to the exception, if any.

        Returns:
        None

        Example:
        .. code-block:: python

            async with YourDatabaseConnection() as connection:
                # Your asynchronous code here

        # Upon exiting the context, the database connection is automatically closed.

        Note:
        This method is intended for use with the `async with` statement in an asynchronous context manager.
        """
        await self.close()
