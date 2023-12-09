# tests/test_database.py
import pytest
from aiodesa import Db
from aiodesa.utils.schema import TableSchema
from dataclasses import dataclass
from pathlib import Path
import textwrap
import os

# Necessary for import lib testing....
os.chdir("aiodesa")


@pytest.fixture
def db_path():
    return "test.sqlite3"


def create_test_module(file_name="test_module.py"):
    # Mocks a fake file of table schema definitions
    parent_folder = Path.cwd()
    file_path = parent_folder / file_name
    file_content = textwrap.dedent(
        """
        from dataclasses import dataclass

        @dataclass
        class PyFileDataclass:
            id: int
            name: str
            table_name: str = "py_file_table"
    """
    )

    with open(file_path, "w") as file:
        file.write(file_content)

    return file_path


def delete_test_module(file_name="test_module.py"):
    parent_folder = Path.cwd()
    file_path = parent_folder / file_name
    file_path = Path(file_path)
    if file_path.exists():
        file_path.unlink()


def delete_test_db(file_name="test.sqlite3"):
    parent_folder = Path.cwd()
    file_path = parent_folder / file_name
    file_path = Path(file_path)
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def test_data_fixture():
    @dataclass
    class TestData:
        username: str
        credits: int
        table_name: str = "table1"

    return TestData


@pytest.mark.asyncio
async def test_db_creation(db_path, test_data_fixture):
    # Tests creation of sqlite3 db
    async with Db(db_path) as db:
        await db.read_table_schemas(test_data_fixture)
        assert await db.table_exists("table1")


@pytest.mark.asyncio
async def test_read_table_schemas_single_dataclass(db_path):
    # Tests creation of table from single data class
    @dataclass
    class SingleDataclass:
        id: int
        name: str
        table_name: str = "example_table"

    async with Db(db_path) as db:
        await db.read_table_schemas(SingleDataclass)
        assert await db.table_exists("example_table")


@pytest.mark.asyncio
async def test_read_table_schemas_tuple_of_dataclasses(db_path):
    # Tests creation of table from tuple of data classes
    @dataclass
    class Dataclass1:
        id: int
        name: str
        table_name: str = "table1"

    @dataclass
    class Dataclass2:
        id: int
        value: float
        table_name: str = "table2"

    async with Db(db_path) as db:
        await db.read_table_schemas((Dataclass1, Dataclass2))
        assert await db.table_exists("table1")
        assert await db.table_exists("table2")


@pytest.mark.asyncio
async def test_read_table_schemas_py_file(db_path):
    # Tests creation of table from py file with data classes
    create_test_module("test_module.py")

    async with Db(db_path) as db:
        await db.read_table_schemas("test_module.py")
        assert await db.table_exists("py_file_table")


@pytest.mark.asyncio
async def test_table_exists(db_path, test_data_fixture):
    # Tests table_exists method
    async with Db(db_path) as db:
        assert not await db.table_exists("nonexistent_table")
        await db.read_table_schemas(test_data_fixture)
        assert await db.table_exists("table1")


def test_teardown():
    # remove the test module and test sqlite db
    delete_test_module("test_module.py")
    delete_test_db()
