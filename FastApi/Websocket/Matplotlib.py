from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import matplotlib.pyplot as plt
import io
import base64
import asyncio

app = FastAPI()

# Function to generate Matplotlib plot
def generate_plot():
    try:
        plt.plot([1, 2, 3, 4])
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        plot_base64 = base64.b64encode(buffer.getvalue()).decode()
        return plot_base64
    except Exception as e:
        print(f"Error generating plot: {e}")
        return None

# WebSocket endpoint to provide updated plot every second
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        plot_data = generate_plot()
        if plot_data:
            await websocket.send_text(plot_data)
        await asyncio.sleep(1)

# Route to serve HTML page for WebSocket connection
@app.get("/")
async def get():
    with open("index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)
    
if __name__ == "__main__":
import uvicorn 
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True ,workers=4)


