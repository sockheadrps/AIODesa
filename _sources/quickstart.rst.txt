Quick Start Guide
=================

To quickly get started with aiodesa, follow these steps:

1. Install aiodesa:

   .. code-block:: bash

      pip install aiodesa

2. Use aiodesa in your asyncio Python code:

   .. code-block:: python

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

                # Insert record
                insert = db.insert(UserEcon)
                await insert('sockheadrps', id="fffff")
                insert = db.insert(UserEcon)
                await insert('someguy', id="aaaaa")

                # Update a record
                update = db.update(UserEcon)
                await update('sockheadrps', points=52330, id="51234")

                # Search
                find = db.find(UserEcon)
                sockheadrps = await find("sockheadrps")
                print(sockheadrps.username)
                print(sockheadrps.points)

                # Delete
                delete = db.delete(UserEcon)
                await delete('sockheadrps')

        asyncio.run(main())
