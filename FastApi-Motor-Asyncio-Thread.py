from fastapi import FastAPI
from bson import ObjectId
import json
from bson import json_util

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio

app = FastAPI()

# Replace with your actual MongoDB connection details
client = AsyncIOMotorClient("mongodb://localhost:27017/")
db = client["testdb"]
collection = db["group"]

USE_THREADS = False  # Set to True to use threads, False for no threads

async def get_item(item_id: str):
    item = await collection.find_one({"_id": ObjectId(item_id)})
    return item

async def get_all_items():
    cursor = collection.find({})
    items = [document async for document in cursor]
    return items

async def create_item(data: dict):
    result = await collection.insert_one(data)
    return result.inserted_id

async def update_item(item_id: str, data: dict):
    result = await collection.update_one({"_id": ObjectId(item_id)}, {"$set": data})
    return result.modified_count

async def delete_item(item_id: str):
    result = await collection.delete_one({"_id": ObjectId(item_id)})
    return result.deleted_count

async def run_in_executor(func, *args):
    if USE_THREADS:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)
    else:
        return await func(*args)

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    item = await run_in_executor(get_item, item_id)
    if item is None:
        return {"message": "Item not found"}
    return item

@app.get("/items")
async def read_all_items():
    items = await run_in_executor(get_all_items)
    return json.loads(json_util.dumps(items)) 


@app.post("/items")
async def create_item_route(data: dict):
    item_id = await run_in_executor(create_item, data)
    return {"message": "Item created successfully", "id": str(item_id)}

@app.put("/items/{item_id}")
async def update_item_route(item_id: str, data: dict):
    updated_count = await run_in_executor(update_item, item_id, data)
    if updated_count == 0:
        return {"message": "Item not found or no changes made"}
    return {"message": "Item updated successfully"}

@app.delete("/items/{item_id}")
async def delete_item_route(item_id: str):
    deleted_count = await run_in_executor(delete_item, item_id)
    if deleted_count == 0:
        return {"message": "Item not found"}
    return {"message": "Item deleted successfully"}
