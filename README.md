# Asyncio Dead Easy Sql API

## AIODesa is for simple data access and definition for your python projects

### AIODesa simplifies async SQLite database management for your projects. It provides a convenient wrapper around Asiosqlite, allowing easy definition of table and record schemas using Python's dataclasses. Define SQL tables and records effortlessly with AIODesa using a single data class, a tuple of data classes, or a .py file with dataclasses.

AIODesa aims to make defining SQL tables and records easy by utilizing dataclasses to define schemas of tables and records. Table and record schemas can be defined with:
1. a single data class
2. a tuple of data classes
3. a .py file with dataclasses.
<br>

# Usage

__Install via pip__
```
pip install aiodesa
```

For example, define your table schemas in a seperate file.  
__schemas.py__

![schema file](https://github.com/sockheadrps/AIODesa/blob/main/schemafile.png?raw=true)

Import db from the package and run with asyncio

__main.py__

```
from aiodesa import Db
import asyncio


async def main():
	schema_file = "table_schemas.py"
	path_to_generate_db = "database.sqlite3"
	async with Db(path_to_generate_db) as db:
		await db.read_table_schemas(schema_file)

asyncio.run(main())
```

Tables are automatically generated
![sql file](https://github.com/sockheadrps/AIODesa/blob/main/sql.png?raw=true)

<br>

# Development:

Ensure poetry is installed:

```
pip install poetry
```

Install project using poetry

```
poetry add git+https://github.com/sockheadrps/AIODesa.git
poetry install
```

create a python file for using AIODesa and activate poetry virtual env to run it

```
poetry shell
poetry run python main.py
```

Sample API usage:

```
from dataclasses import dataclass
from Database import Db
import asyncio


async def main():
	@dataclass
	class Table:
		username: str
		credits: int
		table_name: str = "table 1"

	schema = Table

	async with Db("database.sqlite3") as db:
		await db.read_table_schemas(schema)

asyncio.run(main())
```
