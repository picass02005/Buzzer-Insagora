/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#include <Arduino.h>
#include <NimBLEDevice.h>
#include <WiFi.h>
#include "esp-now.h"
#include "ble.h"
#include "cmd-led.h"
#include "command-handler.h"
#include "pins.h"

#define SERVICE_UUID "0a46dcd2-5dcd-4177-b03d-642d8058ed6a"
#define CHARACTERISTIC_UUID "bb651b13-47ff-4cd5-a3bc-6eb184a5a7b1"
#define BLE_NAME "BUZZERS-INSAGORA"

bool is_master;

NimBLEServer *pServer;
NimBLEService *pService;

// ---------------- Server callbacks ----------------
class BLEBuzzerServerCallbacks : public NimBLEServerCallbacks
{
public:
    void onConnect(NimBLEServer *pServer, NimBLEConnInfo &connInfo)
    {
#ifdef DEBUG
        Serial.printf("[BLE] Client connected: %s\n", connInfo.getAddress().toString().c_str());
#endif

        led_bluetooth_connect();
    }

    void onDisconnect(NimBLEServer *pServer, NimBLEConnInfo &connInfo, int reason)
    {
#ifdef DEBUG
        Serial.printf("[BLE] Client disconnected: %s (Reason: %x)\n", connInfo.getAddress().toString().c_str(), reason);
#endif

        advertise_ble();

        led_bluetooth_disconnect();
    }

    void onMTUChange(uint16_t mtu, NimBLEConnInfo &connInfo)
    {
#ifdef DEBUG
        Serial.printf("[BLE] MTU changed: %u\n", mtu);
#endif
    }

    uint32_t onPassKeyDisplay() {}

    void onConfirmPassKey(NimBLEConnInfo &connInfo, uint32_t pin) {}

    void onAuthenticationComplete(NimBLEConnInfo &connInfo) {}

    void onIdentity(NimBLEConnInfo &connInfo) {}

    void onConnParamsUpdate(NimBLEConnInfo &connInfo) {}

    void onPhyUpdate(NimBLEConnInfo &connInfo, uint8_t txPhy, uint8_t rxPhy) {}
};

// ---------------- Characteristic callbacks ----------------
class BLEBuzzerCallback : public NimBLECharacteristicCallbacks
{
public:
    void onRead(NimBLECharacteristic *pCharacteristic, NimBLEConnInfo &connInfo) {}

    void onWrite(NimBLECharacteristic *pCharacteristic, NimBLEConnInfo &connInfo)
    {
        char value[246];
        memset(value, 0, sizeof(value));
        std::string raw = pCharacteristic->getValue();
        int length = raw.size();
        if (length > 246)
            length = 246;
        memcpy(value, raw.data(), length);

#ifdef DEBUG
        Serial.printf("[BLE] WRITE FROM %s: %s\n", connInfo.getAddress().toString().c_str(), value);
#endif

        ESPNowMessage msg;

        memcpy(msg.target, value, 6);

        msg.cmd_id = value[6];

        memcpy(msg.data, &value[7], sizeof(msg.data));
        msg.data[sizeof(msg.data) - 1] = '\0';

        msg.fwd_ble = 0;

        if (memcmp(msg.target, macAddress, 6) == 0)
        {
            commands_handler(&msg);
        }
        else if (memcmp(msg.target, broadcastAddress, 6) == 0)
        {
            esp_now_send_message(&msg);
            commands_handler(&msg);
        }
        else
        {
            esp_now_send_message(&msg);
        }
    }

    void onStatus(NimBLECharacteristic *pCharacteristic, int code) {}

    void onSubscribe(NimBLECharacteristic *pCharacteristic, NimBLEConnInfo &connInfo, uint16_t subValue) {}
};

// ---------------- Activate BLE ----------------
void activate_ble()
{
#ifdef DEBUG
    Serial.println("[BLE] Initializing BLE");
#endif

    // Init BLE
    NimBLEDevice::init(BLE_NAME);
    NimBLEDevice::setPower(ESP_PWR_LVL_P9);
    delay(100);

    // Set MTU to max size
    NimBLEDevice::setMTU(517);

    // Create server & attach callbacks
    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new BLEBuzzerServerCallbacks());
#ifdef DEBUG
    Serial.println("[BLE] Server callbacks attached");
#endif

    // Create service
    pService = pServer->createService(SERVICE_UUID);

    // Create characteristic
    NimBLECharacteristic *pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        NIMBLE_PROPERTY::READ |
            NIMBLE_PROPERTY::WRITE |
            NIMBLE_PROPERTY::WRITE_NR |
            NIMBLE_PROPERTY::NOTIFY);

    // Add CCCD descriptor
    pCharacteristic->createDescriptor(NimBLEUUID((uint16_t)0x2902));

    // Attach characteristic callback
    pCharacteristic->setCallbacks(new BLEBuzzerCallback());
#ifdef DEBUG
    Serial.println("[BLE] Characteristic callbacks attached");
#endif

    // Start service
    pService->start();

    advertise_ble();
}

void advertise_ble()
{
    NimBLEAdvertising *pAdvertising = NimBLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setConnectableMode(BLE_GAP_CONN_MODE_UND);

    NimBLEAdvertisementData scanResp;
    scanResp.setName(BLE_NAME);
    pAdvertising->setScanResponseData(scanResp);

    pAdvertising->start();

#ifdef DEBUG
    Serial.println("[BLE] Advertisement started");
#endif
}

void ble_send_message(const ESPNowMessage *msg)
{
    if (!is_master)
    {
        return;
    }

    NimBLECharacteristic *pCharacteristic = pService->getCharacteristic(CHARACTERISTIC_UUID);
    if (pCharacteristic == nullptr)
    {
        return;
    }

    if (msg->fwd_ble != 0)
    {
        char tmpData[sizeof(msg->data) + 1];
        tmpData[0] = msg->cmd_id;
        strncpy(&(tmpData[1]), msg->data, sizeof(tmpData) - 1);
        tmpData[sizeof(tmpData) - 1] = '\0';

        pCharacteristic->setValue(tmpData);
        pCharacteristic->notify();

#ifdef DEBUG
        Serial.printf(
            "[BLE] MESSAGE SENT: Data: %s\n",
            msg->data);
#endif
    }
}
