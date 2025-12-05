#include <esp_now.h>
#include <WiFi.h>
#include "esp-now.h"

#define CHANNEL 1 // Recommended to set it to a unused value (best ones may be 6 or 11)
                  // To check: nmcli dev wifi list

const uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

void onReceiveEspNow(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len)
{
    ESPNowMessage msgIncoming;

    memcpy(&msgIncoming, incomingData, sizeof(msgIncoming));

    char srcMacStr[18];
for (int i = 0; i < 6; i++) {
    sprintf(srcMacStr + i*3, "%02X%s", info->src_addr[i], (i < 5) ? ":" : "");
}

    Serial.printf(
        "[ESP-NOW] RECV:\n\t%s\n\tSRC: %s\n\tFWD BLE: %d\n\tData: %s\n",
        msgIncoming.command,
        srcMacStr,
        msgIncoming.fwd_ble,
        msgIncoming.data
    );
}

void onSendEspNow(const wifi_tx_info_t *info, esp_now_send_status_t status)
{
    if (status == ESP_NOW_SEND_FAIL)
    {
        Serial.println("[ESP-NOW] Failure while sending packet");
    }
}

void activate_esp_now()
{
    WiFi.mode(WIFI_STA);

    if (esp_now_init() != ESP_OK)
    {
        Serial.println("[ESP-NOW] Error: couldn't establish init");
        return;
    }

    esp_now_register_recv_cb(onReceiveEspNow);
    esp_now_register_send_cb(onSendEspNow);

    // Add broadcast as peer
    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, broadcastAddress, 6);
    peerInfo.channel = CHANNEL; // Avoid WiFi interferances
    peerInfo.encrypt = false;

    if (esp_now_add_peer(&peerInfo) == ESP_OK)
    {
        Serial.println("[ESP-NOW] Broadcast added as peer");
    }
    else
    {
        Serial.println("[ESP-NOW] Unable to add broadcast as peer");
    }
}

void esp_now_send_message(ESPNowMessage message)
{
    esp_now_send(broadcastAddress, (uint8_t *)&message, sizeof(message));
    Serial.printf(
        "[ESP-NOW] SEND:\n\tCMD: %s\n\tFWD BLE: %d\n\tData: %s\n",
        message.command,
        message.fwd_ble,
        message.data
    );
}
