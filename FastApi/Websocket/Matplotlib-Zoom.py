from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import matplotlib.pyplot as plt
import io
import base64
import asyncio
from typing import Tuple  # Import Tuple from the typing module
import json
import numpy as np


app = FastAPI()
# Get the logger for FastAPI



# # Function to generate Matplotlib plot
# def generate_plot():
#     try:
#         plt.plot([1, 2, 3, 4])
#         plt.xlabel('X-axis')
#         plt.ylabel('Y-axis')

#         buffer = io.BytesIO()
#         plt.savefig(buffer, format='png')
#         buffer.seek(0)

#         plot_base64 = base64.b64encode(buffer.getvalue()).decode()
#         return plot_base64
#     except Exception as e:
#         print(f"Error generating plot: {e}")
#         return None

# # WebSocket endpoint to provide updated plot every second
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         plot_data = generate_plot()
#         if plot_data:
#             await websocket.send_text(plot_data)
#         await asyncio.sleep(1)





# Global variables to store current zoom parameters
x_range = (0, 10)
y_range = (0, 20)

# Function to generate Matplotlib plot with specified x and y ranges
def generate_plot(x_range, y_range):
    try:
        # Generate x data from the specified x range
        x_data = np.linspace(x_range[0], x_range[1], 100)
        # Generate y data using a sinusoidal function
        y_data = np.sin(x_data)

        plt.plot(x_data, y_data)
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')
        plt.xlim(x_range)
        plt.ylim(-1.2, 1.2)
        plt.axhline(0, color='black', linestyle='--', linewidth=1)

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        plot_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()  # Close the plot to avoid memory leaks
        return plot_base64
    except Exception as e:
        print(f"Error generating plot: {e}")
        return None



# WebSocket endpoint to handle zoom parameters
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global x_range, y_range
    await websocket.accept()
    while True: 
        data = await websocket.receive_text() 
        zoom_params = json.loads(data)
        x_range = zoom_params.get('x_range', x_range)
        y_range = zoom_params.get('y_range', y_range) 
        plot_data =  generate_plot(x_range, y_range)
        if plot_data:
            await websocket.send_text(plot_data)
        await asyncio.sleep(0.1)


 # Route to serve HTML page for WebSocket connection
@app.get("/")
async def get():
    with open("index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)
    
if __name__ == "__main__":
    import uvicorn 
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True ,workers=4)


