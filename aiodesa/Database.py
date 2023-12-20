from dataclasses import is_dataclass, fields
from typing import Tuple, Callable, Any
from pathlib import Path
import aiosqlite
from aiodesa.utils.table import make_schema, TableSchema
from aiodesa.utils.types import IsDataclass


class Db:
    """
    Represents a simple SQLite database interface.

    Args:
        db_path : str
                        The path to the SQLite database file.


    Example:

    .. code-block:: python

        class Users:
                username: str
                id: str | None = None
                table_name: str = "users"

        async with Db("database.sqlite3") as db:
            await db.read_table_schemas(Users)
            ...

    """

    _tables: dict
    db_path: Path
    _conn: Any

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self._conn = None
        self._create_db()
        self._tables = {}

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
        """Read table schemas and create tables in the database.

        Args:
            schema:
                The schema or tuple of schemas to be processed. Each schema
                should be a data class representing a table.

        Returns:
            This method does not return any value.

        Example:

        .. code-block:: python

            class Users:
                    username: str
                    id: str | None = None
                    table_name: str = "users"

            async with Db("database.sqlite3") as db:
                        await db.read_table_schemas(Users)
                ...

        Note:
            Provide any additional notes or considerations about the method.
        """
        # single dataclass
        if is_dataclass(schema):
            self._tables[schema.table_name] = schema
            class_fields = fields(schema)
            for field in class_fields:
                if field.name == "table_name":
                    schema_ = make_schema(str(field.default), schema)
                    await self._create_table(schema_, field.name)
            return

        # tuple of dataclasses
        if isinstance(schema, tuple):
            print("is tup")
            for class_obj in schema:
                class_fields = fields(class_obj)
                for field in class_fields:
                    if field.name == "table_name":
                        schema_ = make_schema(str(field.default), class_obj)
                        await self._create_table(schema_, field.name)
            return

    async def _table_exists(self, table_name: str) -> bool | None:
        """
        Create a table in the database based on the provided TableSchema instance.

        Args:
            table_name: The name of the table.

        Returns:
            None

        This method creates a table in the database with the specified name and schema.

        """
        if self._conn is not None:
            query = f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
            cursor = await self._conn.execute(query, (table_name,))
            return await cursor.fetchone() is not None
        else:
            return None

    async def _create_table(self, named_data: TableSchema, name: str) -> None:
        """
        Internal method to create a table in the database based on the provided TableSchema instance.

        Args:
            named_data: The TableSchema instance containing the table_name and SQL data definition.
            name: The name of the table.

        Returns:
            None

        Example:

        .. code-block:: python

            if is_dataclass(schema):
            class_fields = fields(schema)
            for field in class_fields:
                if field.name == "table_name":
                    schema_ = make_schema(str(field.default), schema)
                    await self._create_table(schema_, field.name)
            return


        This method creates a table in the database with the specified name and schema.

        Note:
        The `named_data` parameter should include the `table_name` property for the name of the table
        and the `sql_definition` property for the SQL data definition of the table.
        """
        if self._conn is not None:
            if not await self._table_exists(name):
                async with self._conn.executescript(named_data.data) as cursor:
                    await cursor.fetchall()
                await self._conn.commit()

    def insert(self, data_class: is_dataclass) -> Callable[..., None]:
        """
        Create a record and insert it into the specified table.

        Args:
            data_class: The data class representing the table structure.

        Returns:
            A function to be called with the record data.

        Example:

        .. code-block:: python

            class Users:
                    username: str
                    id: str | None = None
                    table_name: str = "users"

            async with Db("database.sqlite3") as db:
                        await db.read_table_schemas(Users)
                ...
                insert = db.update(UserEcon)
                await insert("john_doe")

        """

        async def _record(*args: Any, **kwargs: Any) -> None:
            data_cls = self._tables[data_class.table_name](*args, **kwargs)
            field_vals = {}
            for field in fields(data_cls):
                value = getattr(data_cls, field.name)
                if value is not None and value != data_cls.table_name:
                    field_vals[field.name] = value

            insertion_vals = tuple(field_vals.values())

            columns_str = ", ".join(field_vals.keys())
            placeholders = ", ".join("?" for _ in insertion_vals)
            sql = f"INSERT INTO {data_class.table_name} ({columns_str}) VALUES ({placeholders});"
            await self._conn.execute(sql, insertion_vals)
            await self._conn.commit()

        return _record

    def update(
        self, data_class: is_dataclass, column_identifier: None | str = None
    ) -> Callable[..., None]:
        """
        Create a record update operation for the specified table.

        Args:
            data_class: The data class representing the table structure.
            column_identifier: The column to use for identifying records.

        Returns:
            A function to be called with the record data for updating.

        Example:

        .. code-block:: python

            class Users:
                    username: str
                    id: str | None = None
                    table_name: str = "users"

            async with Db("database.sqlite3") as db:
                await db.read_table_schemas(Users)
                ...
                update = db.update(UserEcon)
                await update("john_doe")

        Note:
        If the `column_identifier` is not provided, the primary key of the data class will be used as the identifier.
        """

        async def _record(*args, **kwargs) -> None:
            data_cls = self._tables[data_class.table_name](*args, **kwargs)
            values = []
            set_clauses_placeholders = []
            for column, value in kwargs.items():
                values.append(value)
                set_clause = f"{column} = ?"
                set_clauses_placeholders.append(set_clause)
            set_clause_string = ", ".join(set_clauses_placeholders)
            values.extend(args)
            identifier = (
                column_identifier
                if column_identifier is not None
                else data_cls.primary_key
            )
            sql = f"UPDATE {data_class.table_name} SET {set_clause_string} WHERE {identifier} = ?"

            await self._conn.execute(sql, tuple(values))
            await self._conn.commit()

        return _record

    def find(
        self, data_class: is_dataclass, column_identifier: None | str = None
    ) -> Callable[..., None]:
        """
        Create a record retrieval operation for the specified table.

        Args:
            data_class: The data class representing the table structure.
            column_identifier: The column to use for identifying records.
        Defaults to the primary key of the data class if not specified.

        Returns:
            A function to be called with the identifier for record retrieval.

        Example:

        .. code-block:: python

            class MyBestFriends:
                    username: str
                    id: str | None = None
                    table_name: str = "users"

            async with Db("database.sqlite3") as db:
                        await db.read_table_schemas(MyBestFriends)

                ...

                find_jimmy = db.find(MyBestFriends)
                jimmy = await find_jimmy("jimmy")

        """

        async def _record(*args, **kwargs) -> None:
            data_cls = self._tables[data_class.table_name](*args, **kwargs)
            identifier = (
                column_identifier
                if column_identifier is not None
                else data_cls.primary_key
            )
            results = []
            sql = f"SELECT * FROM {data_cls.table_name} WHERE {identifier} = ?"
            sql_args = (args[0],)
            async with self._conn.execute(sql, sql_args) as cursor:
                results = await cursor.fetchall()
            rows_fetched = results[0]
            data_cls = data_class(*rows_fetched, *results[1:])

            return data_cls

        return _record

    def delete(
        self, data_class: is_dataclass, column_identifier: None | str = None
    ) -> Callable[..., None]:
        """
        Create a record deletion operation for the specified table. This defaults to the primary key if
        the column_identifier is not provided.

        Args:
            data_class: The data class representing the table structure.
            column_identifier: The column to use for identifying records.

        Returns:
            A function to be called with the identifier for record deletion.

        Example:

        .. code-block:: python

            class Users:
                    username: str
                    id: str | None = None
                    table_name: str = "users"

            async with Db("database.sqlite3") as db:
                        await db.read_table_schemas(Users)

                ...

                delete = db.delete(UserEcon)
                await delete("john_doe")

        """

        async def _record(*args, **kwargs) -> None:
            data_cls = self._tables[data_class.table_name](*args, **kwargs)
            identifier = (
                column_identifier
                if column_identifier is not None
                else data_cls.primary_key
            )

            sql = f"DELETE FROM {data_cls.table_name} WHERE {identifier} = ?"
            sql_args = (args[0],)

            async with self._conn.execute(sql, sql_args) as cursor:
                await cursor.fetchall()
            await self._conn.commit()

        return _record

    async def _connect(self) -> None:
        """
        Establish a connection to the SQLite database.

        Returns:
        None

        Example:

        .. code-block:: python

            connection = YourDatabaseConnection()
            await connection.connect()
            # The database connection is now established.

        Note:
        This method initializes the connection to the SQLite database using the provided `db_path`.
        """
        self._conn = await aiosqlite.connect(self.db_path)

    async def _close(self) -> None:
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
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

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
        await self._connect()
        # await self._conn.execute("BEGIN")
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
        await self._close()
