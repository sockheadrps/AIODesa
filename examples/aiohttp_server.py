import asyncio
from dataclasses import dataclass
import aiohttp
from aiohttp import web
from aiodesa.utils.table import set_key, UniqueKey, PrimaryKey
from aiodesa import Db


"""
This is an example of a basic aiohttp CRUD webserver utilizing aiodesa for
database access.
"""


@set_key(PrimaryKey("name"), UniqueKey("value"))
@dataclass
class Users:
    name: str
    value: int | None = None
    table_name: str = "users"


async def create_table():
    async with Db("database.sqlite3") as db:
        await db.read_table_schemas(Users)
    return db


async def create_item(user_name, value):
    async with Db("database.sqlite3") as db:
        Users.db.read_table_schemas(Users)
        record = db.insert(Users)
        await record(user_name, value=value)


async def find(name):
    async with Db("database.sqlite3") as db:
        await db.read_table_schemas(Users)
        find = db.find(Users, column_identifier="name")
        person = await find(name)
        if person != "null":
            return person
        else:
            return False


async def update_item_value(user_name, new_value):
    async with Db("database.sqlite3") as db:
        await db.read_table_schemas(Users)
        update = db.insert(Users)
        await update(user_name, new_value)


async def delete_item(name):
    async with Db("database.sqlite3") as db:
        await db.read_table_schemas(Users)
        delete = db.delete(Users, column_identifier="name")
        await delete(name)


async def create_handler(request):
    data = await request.json()
    await create_item(data["name"], data["value"])
    return web.json_response(
        {"code": "201", "message": "created"}, content_type="application/json"
    )


async def find_handler(request):
    data = await request.json()

    person = await find(data.get("name"))
    if person:
        return web.json_response(
            {"code": "200", "message": "OK", "data": person},
            content_type="application/json",
        )
    else:
        return web.json_response(
            {"code": "204", "message": "no content"},
            content_type="application/json",
        )


async def update_handler(request):
    data = await request.json()
    name = data.get("name")
    new_value = data.get("value")
    if name is not None:
        await update_item_value(name, new_value)
        return web.json_response(
            {"code": "200", "message": "Item updated"},
            content_type="application/json",
        )
    else:
        return web.json_response(
            {"code": "204", "message": "Invalid request"},
            content_type="application/json",
        )


async def delete_handler(request):
    data = await request.json()
    name = data.get("name")

    if name is not None:
        await delete_item(name)
        return web.json_response(
            {"code": "200", "message": "Item deleted"},
            content_type="application/json",
        )
    else:
        return web.json_response(
            {"code": "204", "message": "Invalid request"},
            content_type="application/json",
        )


async def main():
    await create_table()

    app = web.Application()
    app.router.add_post("/create", create_handler)
    app.router.add_get("/find", find_handler)
    app.router.add_post("/update", update_handler)
    app.router.add_post("/delete", delete_handler)

    # Set up the web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8080)

    print("Starting server on http://localhost:8080")
    await site.start()

    try:
        # Run the application until interrupted
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
    except asyncio.CancelledError:
        pass
    finally:
        # Cleanup
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
