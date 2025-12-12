import asyncio
import time
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "0a46dcd2-5dcd-4177-b03d-642d8058ed6a"
CHAR_UUID = "bb651b13-47ff-4cd5-a3bc-6eb184a5a7b1"
TARGET_NAME = "BUZZERS-INSAGORA"

LastSend = 0

MAC = [
    b"\xFF\xFF\xFF\xFF\xFF\xFF",
    b"\x6C\xC8\x40\x06\xE7\x3C",
    b"\x6C\xC8\x40\x06\xBE\x2C"
]

# --- Callback appelée à chaque notification reçue ---
def notification_handler(sender, data):
    global LastSend

    print(f"[NOTIFICATION] [{(time.time() - LastSend) * 100:.2f} ms] From {sender} -> {data.decode(errors='ignore')}")


async def main():
    global LastSend

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
    async with BleakClient(esp32) as client:

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

        await asyncio.sleep(0.5)
        await client.write_gatt_char(CHAR_UUID, b"\xFF\xFF\xFF\xFF\xFF\xFFSLED \xFF\x00\x00\x00\xFF\x00\x00\x00\xFF", response=False)

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
