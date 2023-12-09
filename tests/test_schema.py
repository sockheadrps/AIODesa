from aiodesa.utils import schema
from dataclasses import dataclass


def test_table_schema_creation():
    # Test creating a TableSchema instance
    @dataclass
    class Sample:
        username: str
        credits: int
        table_name: str = "table 1"

    data = Sample
    table_schema = schema.TableSchema(table_name="table 1", data=data)

    assert table_schema.table_name == "table 1"
    assert table_schema.data == data
