import asyncio
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "0a46dcd2-5dcd-4177-b03d-642d8058ed6a"
CHAR_UUID = "bb651b13-47ff-4cd5-a3bc-6eb184a5a7b1"
TARGET_NAME = "BUZZERS"


# --- Callback appelée à chaque notification reçue ---
def notification_handler(sender, data):
    print(f"[NOTIFICATION] From {sender} -> {data.decode(errors='ignore')}")


async def main():

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

        while True:
            msg = await asyncio.to_thread(input, "")
            print(f"SEND: {msg}")
            await client.write_gatt_char(CHAR_UUID, msg.encode(), response=False)


if __name__ == "__main__":
    asyncio.run(main())

# TODO: N'arrive pas à être détecté par l'ESP 
