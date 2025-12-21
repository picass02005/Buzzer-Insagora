import asyncio
import time
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "0a46dcd2-5dcd-4177-b03d-642d8058ed6a"
CHAR_UUID = "bb651b13-47ff-4cd5-a3bc-6eb184a5a7b1"
TARGET_NAME = "BUZZERS-INSAGORA"

LastSend = 0

LastBtnClk = 0
ActLed = 0
client: BleakClient

MAC = [
    b"\xFF\xFF\xFF\xFF\xFF\xFF",
    b"\x78\x1C\x3C\x2D\x57\x94",
    b"\x6C\xC8\x40\x06\xBE\x2C"
]

# --- Callback appelée à chaque notification reçue ---
def notification_handler(sender, data):
    global LastSend
    global LastBtnClk
    global ActLed

    # print(f"[NOTIFICATION] [{(time.time() - LastSend) * 100:.2f} ms] From {sender} -> {data.decode(errors='ignore')}")
    m = data.decode(errors='ignore').strip("\x00")
    print(f"[NOTIFICATION] [{(time.time() - LastSend) * 100:.2f} ms] {m}")

    if m.split(" ")[0] == "BPRS":
        led = b""
        if LastBtnClk < int(m.split(" ")[2]):
            LastBtnClk = int(m.split(" ")[2])
            ActLed += 1
            if ActLed >= 8:
                ActLed = 0
            
            for i in range(8):
                if i != ActLed:
                    led += b"\x00\x00\x00"
                
                else:
                    led += b"\x00\x00\xFF"
            
            asyncio.create_task(send_packet(b"SLED " + led))
        

async def send_packet(pkt):
    await client.write_gatt_char(CHAR_UUID, b"\xFF\xFF\xFF\xFF\xFF\xFF" + pkt, response=False)


async def main():
    global LastSend
    global client

    print("BLE scanning")
    devices = await BleakScanner.discover(timeout=5.0)
    
    esp32 = None
    for d in devices:
        print(f"- {d.name} : {d.address}")
        if d.name == TARGET_NAME:
            esp32 = d.address

    if esp32 is None:
        print("\nBuzzer not found")
        return

    print(f"\nConnecting to {TARGET_NAME} ({esp32})...")
    client = BleakClient(esp32)
    await client.connect()

    if not client.is_connected:
        print("Couldn't connect")
        return

    print("Connected")

    # Recv notifs
    await client.start_notify(CHAR_UUID, notification_handler)
    print("Notifications registered")

    print("Adresses mac:")
    for i, j in enumerate(MAC):
        print(f"\t{i}: {''.join(f'\\x{b:02X}' for b in j)}")
    
    print("Example:")
    print("\t0 PING")

    await asyncio.sleep(0.25)
    await client.write_gatt_char(CHAR_UUID, b"\xFF\xFF\xFF\xFF\xFF\xFFSLED " + b"\x08\x08\x00\x00\x00\x08"*4, response=False)
    # await client.write_gatt_char(CHAR_UUID, b"\xFF\xFF\xFF\xFF\xFF\xFFSLED " + b"\x00\x08\x08"*8, response=False)
    await asyncio.sleep(0.25)

    """

    while True:
        for i in range(8):
            leds = bytearray(24)
            leds[i*3 + 0] = 255
            leds[i*3 + 1] = 0
            leds[i*3 + 2] = 0
            await client.write_gatt_char(CHAR_UUID, b"\xFF\xFF\xFF\xFF\xFF\xFFSLED " + leds, response=False)
            await asyncio.sleep(0.05)
    """

    print("ACLK")
    await client.write_gatt_char(CHAR_UUID, b"\xFF\xFF\xFF\xFF\xFF\xFFACLK", response=False)
    LastSend = time.time()
    await asyncio.sleep(1)
    await client.write_gatt_char(CHAR_UUID, b"\xFF\xFF\xFF\xFF\xFF\xFFGCLK", response=False)
    LastSend = time.time()
    await asyncio.sleep(1)

    while True:
        inp = await asyncio.to_thread(input, "")
        try:
            m = MAC[int(inp.split(" ")[0])]
            msg = " ".join(inp.split(" ")[1:])
        except ValueError:
            print("Invalid format, defaulting to MAC[0]")
            m = MAC[0]
            msg = inp

        msg_b = m + msg.encode()
        print(f"SEND: {msg_b}")
        await client.write_gatt_char(CHAR_UUID, msg_b, response=False)
        LastSend = time.time()


if __name__ == "__main__":
    asyncio.run(main())
