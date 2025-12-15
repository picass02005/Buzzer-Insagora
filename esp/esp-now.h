#include <esp_now.h>

#ifndef ESPNOW_H
#define ESPNOW_H

// Message structure
// Data length: 247 bytes (BLE max size)
typedef struct __attribute__((packed))
{
    char fwd_ble;
    char target[6];
    char data[240];
} ESPNowMessage;

const uint8_t broadcastAddress[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

extern uint8_t macAddress[6];
extern char macStr[18];

void activate_esp_now();
void esp_now_send_message(const ESPNowMessage *message);

void onReceiveEspNow(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len);
void onSendEspNow(const wifi_tx_info_t *info, esp_now_send_status_t status);

#endif
