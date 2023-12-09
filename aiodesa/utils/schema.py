from dataclasses import dataclass


@dataclass
class TableSchema:
    table_name: str
    data: str


def make_schema(name, data_cls):
    columns = []
    name = name.replace(" ", "_")
    for field_name, field_type in data_cls.__annotations__.items():
        if field_name == "table_name":
            pass
        else:
            sql_type = "INTEGER" if field_type == int else "VARCHAR(255)"
            columns.append(f"{field_name} {sql_type}")

    schema = TableSchema(
        name, f"CREATE TABLE IF NOT EXISTS {name} (\n{', '.join(columns)}\n);"
    )

    return schema
