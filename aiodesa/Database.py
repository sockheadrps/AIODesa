from dataclasses import is_dataclass, fields
from typing import Union, Tuple, Type, Optional
from pathlib import Path
import aiosqlite
from aiodesa.utils.tables import make_schema, TableSchema
import inspect
import importlib
import os


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

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.conn = None
        self._create_db()

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

    async def read_table_schemas(self, schema: Union[Type, Tuple[Type, ...], str]):
        """
        Read table schemas and create tables in the database based on the provided schema.

        Parameters
        ----------
        schema : Union[type, Tuple[type, ...], str]
                The schema definition, which can be a single dataclass, a tuple of dataclasses,
                or the path to a .py file containing dataclass objects.
        """

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

        # Load all the classes in the mydata.py file
        try:
            schemas_path = Path(__file__).parent / schema

            if Path.exists(schemas_path):
                if schema[-2:] == "py":
                    module_folder = os.getcwd()
                    spec = importlib.util.spec_from_file_location(
                        schema[:-3], module_folder + "/" + schema[:-3] + ".py"
                    )
                    table_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(table_module)
                    for attribute in dir(table_module):
                        if inspect.isclass(getattr(table_module, attribute)):
                            # Get the class object
                            class_obj = getattr(table_module, attribute)

                            # Get the fields of the class using dataclasses.fields
                            class_fields = fields(class_obj)

                            # field names and default values
                            for field in class_fields:
                                if field.name == "table_name":
                                    schema_ = make_schema(str(field.default), class_obj)
                                    await self.create_table(schema_, field.name)

        except AttributeError as e:
            raise e

    async def table_exists(self, table_name: str) -> Optional[bool]:
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

    async def insert_into(self, table_name, user):
        field_names = [field for field in user.__annotations__]
        values = [getattr(user, i) for i in field_names if getattr(user, i) is not None]
        non_none_columns = [
            (field, value)
            for field, value in zip(field_names, values)
            if value is not None
        ]
        columns, filtered_values = zip(*non_none_columns)
        columns_str = ", ".join(columns)
        placeholders = ", ".join("?" for _ in filtered_values)
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"

        await self.conn.execute(sql, values)
        await self.conn.commit()

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
