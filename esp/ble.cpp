#include <NimBLEDevice.h>
#include "esp-now.h"
#include "ble.h"
#include "pins.h"

#define SERVICE_UUID "0a46dcd2-5dcd-4177-b03d-642d8058ed6a"
#define CHARACTERISTIC_UUID "bb651b13-47ff-4cd5-a3bc-6eb184a5a7b1"
#define BLE_NAME "BUZZERS"

bool is_master;

NimBLEServer* pServer;
NimBLEService* pService;

// ---------------- Server callbacks ----------------
class BLEBuzzerServerCallbacks : public NimBLEServerCallbacks {
public:
    void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) {
        Serial.printf("[BLE] Client connected: %s\n", connInfo.getAddress().toString().c_str());

        // Indicate successfull connection
        for (int i = 0; i < 5; i++) {
            digitalWrite(ONBOARD_LED, HIGH);
            delay(100);
            digitalWrite(ONBOARD_LED, LOW);
            delay(100);
        }
    }

    void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) {
        Serial.printf("[BLE] Client disconnected: %s (Reason: %x)\n", connInfo.getAddress().toString().c_str(), reason);
        advertise_ble();
    }

    void onMTUChange(uint16_t mtu, NimBLEConnInfo& connInfo) {
        Serial.printf("[BLE] MTU changed: %u\n", mtu);
    }

    uint32_t onPassKeyDisplay() {}

    void onConfirmPassKey(NimBLEConnInfo& connInfo, uint32_t pin) {}

    void onAuthenticationComplete(NimBLEConnInfo& connInfo) {}

    void onIdentity(NimBLEConnInfo& connInfo) {}

    void onConnParamsUpdate(NimBLEConnInfo& connInfo) {}

    void onPhyUpdate(NimBLEConnInfo& connInfo, uint8_t txPhy, uint8_t rxPhy) {}
};

// ---------------- Characteristic callbacks ----------------
class BLEBuzzerCallback : public NimBLECharacteristicCallbacks {
public:
    void onRead(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) {}

    void onWrite(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) {
        String value = pCharacteristic->getValue().c_str();
        Serial.printf("[BLE] WRITE FROM %s: %s\n", connInfo.getAddress().toString().c_str(), value);

        ESPNowMessage msg;
        msg.fwd_ble = 0;
        strncpy(msg.command, "TEST", sizeof(msg.command)-1);
        msg.command[14] = '\0';
        value.toCharArray(msg.data, sizeof(msg.data));
        esp_now_send_message(msg);

        // Ack: send back same value
        pCharacteristic->setValue(value);
        pCharacteristic->notify();
    }

    void onStatus(NimBLECharacteristic* pCharacteristic, int code) {}

    void onSubscribe(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo, uint16_t subValue) {}
};

// ---------------- Activate BLE ----------------
void activate_ble() {
    Serial.println("[BLE] Initializing BLE");

    // Init BLE
    NimBLEDevice::init(BLE_NAME);
    NimBLEDevice::setPower(ESP_PWR_LVL_P9);
    delay(100);

    // Set MTU to max size
    NimBLEDevice::setMTU(517);

    // Create server & attach callbacks
    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new BLEBuzzerServerCallbacks());
    Serial.println("[BLE] Server callbacks attached");

    // Create service
    pService = pServer->createService(SERVICE_UUID);

    // Create characteristic
    NimBLECharacteristic* pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        NIMBLE_PROPERTY::READ |
        NIMBLE_PROPERTY::WRITE |
        NIMBLE_PROPERTY::WRITE_NR |
        NIMBLE_PROPERTY::NOTIFY
    );

    // Add CCCD descriptor
    pCharacteristic->createDescriptor(NimBLEUUID((uint16_t)0x2902));

    // Attach characteristic callback
    pCharacteristic->setCallbacks(new BLEBuzzerCallback());
    Serial.println("[BLE] Characteristic callbacks attached");

    // Start service
    pService->start();

    advertise_ble();
}

void advertise_ble() {
    NimBLEAdvertising* pAdvertising = NimBLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setConnectableMode(BLE_GAP_CONN_MODE_UND);

    NimBLEAdvertisementData scanResp;
    scanResp.setName(BLE_NAME);
    pAdvertising->setScanResponseData(scanResp);

    pAdvertising->start();
    Serial.println("[BLE] Advertisement started");
}
