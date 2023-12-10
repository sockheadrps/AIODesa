from dataclasses import dataclass
from typing import Any


@dataclass
class TableSchema:
    """
    Represents the schema for a database table.

    Parameters
    ----------
    table_name : str
        The name of the table.
    data : str
        The SQL data definition language (DDL) statement for creating the table.
    """

    table_name: str
    data: str


def make_schema(name: str, data_cls: Any) -> TableSchema:
    """
    Generate a TableSchema based on the provided data class.

    Parameters
    ----------
    name : str
        The name of the table.
    data_cls : type
        A data class defining the schema for the table.

    Returns
    -------
    TableSchema
        An instance of TableSchema containing the table_name and SQL data definition.
    """
    columns = []
    name = name.replace(" ", "_")
    for field_name, value in data_cls.__annotations__.items():
        if field_name == "table_name":
            pass
        else:
            sql_type = "INTEGER" if value == int else "VARCHAR(255)"
            columns.append(f"{field_name} {sql_type}")

    schema = TableSchema(
        name, f"CREATE TABLE IF NOT EXISTS {name} (\n{', '.join(columns)}\n);"
    )

    return schema
