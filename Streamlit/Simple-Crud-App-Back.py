#run with: uvicorn main:app --reload

from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from bson import ObjectId  # Import ObjectId from bson module
from pydantic import BaseModel

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["crud_db"]
collection = db["items"]

app = FastAPI()

# Model for the Item
class Item(BaseModel):
    name: str
    description: str

# Routes for CRUD operations with pagination
@app.post("/items/")
async def create_item(item: Item):
    item_id = collection.insert_one(item.dict()).inserted_id
    return {"id": str(item_id), **item.dict()}

@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    items = list(collection.find().skip(skip).limit(limit))
    # Convert ObjectId to string for each item
    for item in items:
        item["_id"] = str(item["_id"])
    return items

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    item = collection.find_one({"_id": ObjectId(item_id)})
    if item:
        # Convert ObjectId to string
        item["_id"] = str(item["_id"])
        return item
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}")
async def update_item(item_id: str, item: Item):
    result = collection.update_one({"_id": ObjectId(item_id)}, {"$set": item.dict()})
    if result.modified_count == 1:
        return {"message": "Item updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    result = collection.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 1:
        return {"message": "Item deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")
