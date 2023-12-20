# tests/test_database.py
import pytest
from aiodesa import Db
from aiodesa.utils.table import make_schema
import aiosqlite
from dataclasses import dataclass, fields
from pathlib import Path
import secrets


@pytest.fixture
def db_path():
    """
    DB path initializer
    """
    return "test.sqlite3"


@pytest.fixture(scope="session", autouse=True)
def name():
    """
    DB name initializer
    _ is to satisfy SQL convention in case secrets returns a string with a numeric in position 0
    """
    return "_" + secrets.token_hex(16)


def delete_test_db(db_path):
    """
    For tearing down test
    """
    file_name = db_path
    parent_folder = Path.cwd()
    file_path = parent_folder / file_name
    file_path = Path(file_path)
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def test_data_fixture(name):
    """
    Fixture for testing DB from dataclass
    """

    @dataclass
    class TestData:
        test_column: str | None = None
        test_column_two: str | None = None
        table_name: str = name

    return TestData


@pytest.mark.asyncio
async def test_db_init(db_path):
    """
    Tests the creation of the following class attributes
            self.db_path = Path(db_path)
            self._conn = None
            self._create_db()
            self._tables = {}
    """
    db = Db(db_path)
    db_path = Path(db.db_path)
    assert db_path.is_file()
    assert db._conn == None
    assert isinstance(db._tables, dict)


@pytest.mark.asyncio
async def test_read_table_schemas_single_dataclass(test_data_fixture, db_path, name):
    """
    Tests creation of table from single data class
    """
    single_data_class = test_data_fixture

    async with Db(db_path) as db:
        await db.read_table_schemas(single_data_class)
        assert await db._table_exists(name)


@pytest.mark.asyncio
async def test_read_table_schemas_tuple_of_dataclasses(db_path):
    """
    Tests creation of tables from tuple of data classes
    """
    table_one_name = "_" + secrets.token_hex(16)
    table_two_name = "_" + secrets.token_hex(16)

    @dataclass
    class Dataclass1:
        id: int
        name: str
        table_name: str = table_one_name

    @dataclass
    class Dataclass2:
        id: int
        value: float
        table_name: str = table_two_name

    async with Db(db_path) as db:
        await db.read_table_schemas((Dataclass1, Dataclass2))
        assert await db._table_exists(table_one_name)
        assert await db._table_exists(table_two_name)


@pytest.mark.asyncio
async def test_table_exists(db_path, test_data_fixture, name):
    """
    Tests that the internal method _table_exists returns if tables exist or not
    """
    async with Db(db_path) as db:
        assert not await db._table_exists("nonexistent_table")
        await db.read_table_schemas(test_data_fixture)
        assert await db._table_exists(name)


@pytest.mark.asyncio
async def test_create_table(test_data_fixture, db_path):
    """
    Tests that _create_table actually creates the table. Test is done with raw sql, not by testing against
    internal class methods.
    """
    class_fields = fields(test_data_fixture)
    db = Db(db_path)
    for field in class_fields:
        if field.name == "table_name":
            schema_ = make_schema(str(field.default), test_data_fixture)
            await db._create_table(schema_, field.name)

    async with Db(db_path) as db:
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        cursor = await db._conn.execute(query, (test_data_fixture.table_name,))
        assert await cursor.fetchone() is not None


@pytest.mark.asyncio
async def test_insert(test_data_fixture, db_path, name):
    """
    Tests insert method of DB class
    """
    async with Db(db_path) as db:
        await db.read_table_schemas(test_data_fixture)
        insert = db.insert(test_data_fixture)
        await insert("test")
        query = f"SELECT * FROM {name} WHERE test_column=?;"
        cursor = await db._conn.execute(query, ("test",))
        assert await cursor.fetchone() is not None


@pytest.mark.asyncio
async def test_update(test_data_fixture, db_path, name):
    """
    Tests update method of DB class. Test is done with raw sql, not by testing against
    internal class methods.
    """
    async with Db(db_path) as db:
        await db.read_table_schemas(test_data_fixture)
        update = db.update(test_data_fixture, column_identifier="test_column")
        await update("test", test_column_two="test_2")

        query = f"SELECT * FROM {name} WHERE test_column_two=?;"
        cursor = await db._conn.execute(query, ("test_2",))
        assert await cursor.fetchone() is not None


@pytest.mark.asyncio
async def test_find(test_data_fixture, db_path):
    """
    Test the find method of DB class.
    """
    async with Db(db_path) as db:
        await db.read_table_schemas(test_data_fixture)
        find = db.find(test_data_fixture, column_identifier="test_column")
        find_record = await find("test")
        assert find_record.test_column == "test"


@pytest.mark.asyncio
async def test_delete(test_data_fixture, db_path, name):
    """
    Test the find method of DB class. Test is done with raw sql, not by testing against
    internal class methods.
    """
    async with Db(db_path) as db:
        await db.read_table_schemas(test_data_fixture)
        delete = db.delete(test_data_fixture, column_identifier="test_column")
        await delete("test")

        query = f"SELECT * FROM {name} WHERE test_column=?;"
        cursor = await db._conn.execute(query, ("test",))
        assert await cursor.fetchone() is None


@pytest.mark.asyncio
async def test_connect(db_path):
    """
    Tests aiosqlite connection
    """
    db = Db(db_path)
    await db._connect()
    assert db._conn is not None
    assert isinstance(db._conn, aiosqlite.Connection)
    await db._close()


@pytest.mark.asyncio
async def test_close(db_path):
    """
    Tests aiosqlite connection close
    """
    db = Db(db_path)
    await db._connect()
    await db._close()
    assert db._conn is None


@pytest.mark.asyncio
async def test_aenter(db_path):
    """
    Tests aiosqlite asynchronous connection
    """
    async with Db(db_path) as db:
        assert db._conn is not None


@pytest.mark.asyncio
async def test_aclose(db_path):
    """
    Tests aiosqlite asynchronous connection close
    """
    async with Db(db_path) as db:
        assert db._conn is not None
    assert db._conn is None


def test_teardown(db_path):
    # remove the test sqlite db
    delete_test_db(db_path)
