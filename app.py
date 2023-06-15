import asyncio
import socketio
from bluetooth import *
from gpiozero import Motor
from time import sleep

motor = Motor(12, 13)
motor.stop()

socket = BluetoothSocket( RFCOMM )
socket.connect(("98:D3:31:F6:18:03", 1))
print("bluetooth connected!")

sio = socketio.AsyncClient()

humidity = None
temperature = None
water_level = None

async def get_bluetooth_data():
    global humidity, temperature, water_level
    
    loop = asyncio.get_event_loop()
    
    data = await loop.run_in_executor(None, socket.recv, 1024)
    # print("Received: {}".format(data))
    t = data.decode('utf-8')

    if t == 'h':
        humidity = float(socket.recv(1024))
    elif t == 't':
        temperature = float(socket.recv(1024))
    elif t == 'w':
        water_level = int(socket.recv(1024))
    else:
        pass
    
async def bluetooth_loop():
    while True:
        await get_bluetooth_data()
        if None not in (humidity, temperature, water_level):
            await sio.emit(
                'updateSensorMeasurements',
                {
                    'humidity': humidity,
                    'temperature': temperature,
                    'waterLevel': water_level
                }
            )
            # print(humidity, temperature, water_level)
            
        await sio.sleep(0)


@sio.event
async def connect():
    print('connection established')
    
@sio.on('actuatorStateUpdated')
async def on_actuator_state_updated(data):
    if data['set'] is True:
        print('set motor state to forward')
        motor.forward()
        await sio.sleep(12)
    elif data['set'] is False:
        print('set motor state to backward')
        motor.backward()
        await sio.sleep(12)
    motor.stop()
    print('set motor state to stop')

@sio.event
async def disconnect():
    print('disconnected from server')

async def main():
    await sio.connect('http://hydro.inft.kr:8080')
    task = sio.start_background_task(bluetooth_loop)
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())

