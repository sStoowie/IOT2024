import asyncio
import websockets
from smbus2 import SMBus  # Updated to use smbus2, which is more commonly used
import time

bus = SMBus(1)

def readData():
    bus.write_i2c_block_data(0x44, 0x2C, [0x06])
    time.sleep(0.5)
    data = bus.read_i2c_block_data(0x44, 0x00, 6)
    return convertData(data)

def convertData(data):
    temp = data[0] * 256 + data[1]
    cTemp = -45 + (175 * temp / 65535.0)
    fTemp = -49 + (315 * temp / 65535.0)
    humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
    return cTemp, fTemp, humidity

connected_clients = set()

async def send_data_periodically():
    while True:
        cTemp, fTemp, humidity = readData()
        if connected_clients:  # Check if there are any connected clients
            message = f"Temperature: {cTemp:.2f}°C, Humidity: {humidity:.2f}%"
            tasks = [asyncio.create_task(client.send(message)) for client in connected_clients]
            await asyncio.gather(*tasks)
        await asyncio.sleep(5)  # Send data every 5 seconds

async def echo(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Receive from client: {message}")
            await websocket.send(f"Server received: {message}")
    finally:
        connected_clients.remove(websocket)

async def main():
    server = await websockets.serve(echo, "0.0.0.0", 8765)
    print("Server started, waiting for communication...")
    # Start sending temperature data periodically
    asyncio.create_task(send_data_periodically())
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())

    