from aiodesa.utils.table import (
    ForeignKey,
    PrimaryKey,
    UniqueKey,
    set_key,
    make_schema,
)
from dataclasses import dataclass
from uuid import uuid4


def test_ForeignKey():
    """
    Test the ForeignKey named tuple.

    This test checks the correctness of the class by verifying that
    the result is as expected for various input cases.
    """
    table = uuid4()
    key = uuid4()
    foreign_key = ForeignKey(key, table)
    assert foreign_key.table == table
    assert foreign_key.key == key


def test_PrimaryKey():
    """
    Test the PrimaryKey named tuple.

    This test checks the correctness of the class by verifying that
    the result is as expected for various input cases.
    """
    column = uuid4()
    primary_key = PrimaryKey(column)
    assert primary_key.column == column


def test_UniqueKey():
    """
    Test the UniqueKey named tuple.

    This test checks the correctness of the class by verifying that
    the result is as expected for various input cases.
    """
    column = uuid4()
    unique_key = UniqueKey(column)
    assert unique_key.column == column


def test_set_key():
    """
    Test the behavior of the set_key decorator.

    This test checks that the set_key decorator correctly sets primary, unique, and foreign keys
    on a class using PrimaryKey, UniqueKey, and ForeignKey attributes.
    """
    test_column_1 = uuid4()
    test_column_2 = uuid4()
    foriegn_key_table = uuid4()
    foriegn_key_key = uuid4()

    @set_key(
        PrimaryKey(test_column_1),
        UniqueKey(test_column_2),
        ForeignKey(foriegn_key_key, foriegn_key_table),
    )
    class TestTable:
        test_column_1: str | None = None
        test_column_2: int | None = None

    assert TestTable.primary_key == test_column_1
    assert TestTable.unique_key == test_column_2
    assert TestTable.foreign_keys[0].table == foriegn_key_table
    assert TestTable.foreign_keys[0].key == foriegn_key_key

    def test_make_schema():
        """
        Tests that the table SQL is generated correctly
        """
        table_name = uuid4

        @dataclass
        class TestTable:
            table_name: str
            test_column_1: str = "Test"

        table = TestTable(table_name)
        schema = make_schema(table_name, table)
        # Build the expected sql by hand....
        expected_sql = f"CREATE TABLE IF NOT EXISTS test (\n{table.test_column_1} VARCHAR\n);"

        assert schema.table_name == table_name
        assert schema.data == expected_sql
