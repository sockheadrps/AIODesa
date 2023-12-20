from aiodesa.utils.util_types import SQLDataType, py_to_sql_type
import pytest
from dataclasses import dataclass


def test_SQLDataTypes():
    """
    Why? Idk, 100% test coverage I guess...
    """
    assert SQLDataType.INT.value == "INT"
    assert SQLDataType.VARCHAR.value == "VARCHAR"
    assert SQLDataType.CHAR.value == "CHAR"
    assert SQLDataType.TEXT.value == "TEXT"
    assert SQLDataType.BOOLEAN.value == "BOOLEAN"
    assert SQLDataType.FLOAT.value == "FLOAT"
    assert SQLDataType.DATE.value == "DATE"
    assert SQLDataType.DATETIME.value == "DATETIME"
    assert SQLDataType.DECIMAL.value == "DECIMAL"
    assert SQLDataType.DOUBLE.value == "DOUBLE"
    assert SQLDataType.INTEGER.value == "INTEGER"
    assert SQLDataType.SMALLINT.value == "SMALLINT"
    assert SQLDataType.BIGINT.value == "BIGINT"
    assert SQLDataType.NONE.value == "NULL"
    assert SQLDataType.PRIMARY.value == " PRIMARY KEY"
    assert SQLDataType.UNIQUE.value == " UNIQUE KEY"


def test_py_to_sql_type():
    """
    Tests conversion from python primitive types to mapped SQL types from SQLDataType
    """
    assert py_to_sql_type(int) == SQLDataType.INT.value
    assert py_to_sql_type(str) == SQLDataType.VARCHAR.value
    assert py_to_sql_type(float) == SQLDataType.FLOAT.value
    assert py_to_sql_type(bool) == SQLDataType.BOOLEAN.value
    assert py_to_sql_type(bytes) == SQLDataType.TEXT.value
    assert py_to_sql_type(bytearray) == SQLDataType.TEXT.value
    assert py_to_sql_type(list) == SQLDataType.TEXT.value
    assert py_to_sql_type(tuple) == SQLDataType.TEXT.value
    assert py_to_sql_type(set) == SQLDataType.TEXT.value
    assert py_to_sql_type(dict) == SQLDataType.TEXT.value
    assert py_to_sql_type(None) == SQLDataType.NONE.value

    with pytest.raises(ValueError, match="Unsupported data type"):
        py_to_sql_type(complex(1, 2))
