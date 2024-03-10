import asyncio
from fastapi import FastAPI
from pyee import AsyncIOEventEmitter

app = FastAPI()
emitter = AsyncIOEventEmitter()

# Define an asynchronous event listener function
async def event_listener(arg):
    print("Received:", arg)

# Subscribe the event listener to the event named 'example_event'
emitter.on('example_event', event_listener)

@app.get("/trigger/{data}")
async def trigger_event(data: str):
    # Emit the event and await its completion
    emitter.emit('example_event', data)
    return {"message": "Event triggered with data: " + data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
