#include <NimBLEDevice.h>

#define SERVICE_UUID "0a46dcd2-5dcd-4177-b03d-642d8058ed6a"
#define CHARACTERISTIC_UUID "bb651b13-47ff-4cd5-a3bc-6eb184a5a7b1"
#define BLE_NAME "BUZZERS-INSAGORA"

bool is_master;

NimBLEServer *pServer;
NimBLEService *pService;

class BLEBuzzerCallback : public NimBLECharacteristicCallbacks
{
  void onWrite(NimBLECharacteristic *pCharacteristic)
  {
    String value = pCharacteristic->getValue().c_str(); // Get written data

    Serial.println(value); // For debug purposes

    // ACK
    pCharacteristic->setValue(value); // Send back same value
    pCharacteristic->notify();        // Notify every connected clients
  }
};

void activate_ble()
{
  // Initialize BLE
  NimBLEDevice::init(BLE_NAME);

  // Enable max MTU and long data packets
  NimBLEDevice::setMTU(517);

  // Create BLE server and service
  NimBLEServer *pServer = NimBLEDevice::createServer();
  NimBLEService *pService = pServer->createService(SERVICE_UUID);

  // Create charasteristic with READ, WRITE, NOTIFY
  NimBLECharacteristic *pCharacteristic = pService->createCharacteristic(
      CHARACTERISTIC_UUID,
      NIMBLE_PROPERTY::READ |
          NIMBLE_PROPERTY::WRITE |
          NIMBLE_PROPERTY::NOTIFY);

  // Setting callback
  pCharacteristic->setCallbacks(new BLEBuzzerCallback());

  // Start the service
  pService->start();

  NimBLEAdvertising *pAdvertising = NimBLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->start();
}
