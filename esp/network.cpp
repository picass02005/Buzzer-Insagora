#include "network.h"
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define SERVICE_UUID "0a46dcd2-5dcd-4177-b03d-642d8058ed6a"
#define CHARACTERISTIC_UUID "bb651b13-47ff-4cd5-a3bc-6eb184a5a7b1"

BLEServer* server;
BLEService* service;

bool is_master;

class BLECallback : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* pChar) {
    String value = pChar->getValue();  // Get written data
    Serial.print("RECV : ");
    for (size_t i = 0; i < value.length(); i++) {
      Serial.print((uint8_t)value[i], HEX);
      Serial.print(" ");
    }
    Serial.println();

    // ACK
    pChar->setValue(value);  // Send back same value
    pChar->notify();         // Notify every connected clients
  }
};


void activate_ble() {
  // Set BLE device name
  BLEDevice::init("BUZZERS-INSAGORA");

  // Create BLE server
  server = BLEDevice::createServer();

  // Create service
  service = server->createService(SERVICE_UUID);

  // Create charasteristic with READ, WRITE, NOTIFY
  BLECharacteristic* characteristic = service->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_NOTIFY);

  // Setting initial value
  characteristic->setValue("Buzzers for Insagora by Club Info and Club Robot");

  // Add a descriptor to allow notifications
  characteristic->addDescriptor(new BLE2902());

  // Add callback on charasteristic
  characteristic->setCallbacks(new BLECallback());

  // Start service
  service->start();

  // Begin advertising
  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(SERVICE_UUID);
  advertising->start();
}