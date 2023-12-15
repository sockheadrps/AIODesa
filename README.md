# Asyncio Dead Easy Sql API

## Are you tired of re-writing SQLite DB's for your projects? Me too. AIODesa makes standing up simple, usable applications extremely easy and effective.

### AIODesa offers a straightforward and 100% Python interface for managing asynchronous data access. By leveraging Python's built-ins and standard library, it seamlessly wraps around AioSqlite, providing a hassle-free experience. With AIODesa, you can define, generate, and commit data effortlessly, thanks to shared objects for tables and records.

AIODesa aims to make defining SQL tables and records easy by utilizing dataclasses to define structure of both tables and records. No more re-writing schemas.

## AioDesa

![AIODesa](https://github.com/sockheadrps/AIODesa/blob/main/AIODesaEx.png?raw=true)

# Usage

__Install via pip__
```
pip install aiodesa
```

Sample API usage:

```
from aiodesa import Db
import asyncio
from dataclasses import dataclass
from aiodesa.utils.tables import ForeignKey, UniqueKey, PrimaryKey, set_key


async def main():
	# Define structure for both tables and records
	# Easily define key types
	@dataclass
	@set_key(PrimaryKey("username"), UniqueKey("id"), ForeignKey("username", "anothertable"))
	class UserEcon:
		username: str
		credits: int | None = None
		points: int | None = None
		id: str | None = None
		table_name: str = "user_economy"


	async with Db("database.sqlite3") as db:
		# Create table from UserEcon class
		await db.read_table_schemas(UserEcon)

		# Insert a record
		record = db.insert(UserEcon.table_name)
		await record('sockheadrps', id="fffff")

		# Update a record
		record = db.update(UserEcon.table_name, column_identifier="username")
		await record('sockheadrps', points=2330, id="1234")
		

asyncio.run(main())

```

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
