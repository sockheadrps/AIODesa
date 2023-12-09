from dataclasses import is_dataclass, fields
from pathlib import Path
import aiosqlite
from .utils.schema import make_schema
import inspect
import importlib


class Db:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = None
        self._create_db()

    def _create_db(self):
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_path.touch()

    async def read_table_schemas(self, schema):
        # single dataclass
        if is_dataclass(schema):
            class_fields = fields(schema)
            for field in class_fields:
                if field.name == "table_name":
                    schema_ = make_schema(field.default, schema)
                    await self.create_table(schema_, field.name)
            return

        # tuple of dataclasses
        if isinstance(schema, tuple):
            for class_obj in schema:
                class_fields = fields(class_obj)
                for field in class_fields:
                    if field.name == "table_name":
                        schema_ = make_schema(field.default, class_obj)
                        await self.create_table(schema_, field.name)
            return

        # .py file of dataclass objects
        try:
            schemas_path = Path(__file__).parent / schema
            if Path.exists(schemas_path):
                if schema[-2:] == "py":
                    table_module = importlib.import_module(schema[:-3])
                    for attribute in dir(table_module):
                        if inspect.isclass(getattr(table_module, attribute)):
                            # Get the class object
                            class_obj = getattr(table_module, attribute)

                            # Get the fields of the class using dataclasses.fields
                            class_fields = fields(class_obj)

                            # Print the field names and default values
                            for field in class_fields:
                                if field.name == "table_name":
                                    schema_ = make_schema(field.default, class_obj)
                                    await self.create_table(schema_, field.name)

        except AttributeError as e:
            raise e

    async def table_exists(self, table_name):
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        print(f"table name {table_name}")
        cursor = await self.conn.execute(query, (table_name,))
        return await cursor.fetchone() is not None

    async def create_table(self, named_data, name):
        print(named_data)
        if not await self.table_exists(name):
            async with self.conn.executescript(named_data.data) as cursor:
                await cursor.fetchall()
            await self.conn.commit()

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)

    async def close(self):
        await self.conn.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
