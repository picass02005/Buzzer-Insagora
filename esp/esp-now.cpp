#include <esp_now.h>
#include <WiFi.h>
#include "esp-now.h"

#define CHANNEL 1 // Recommended to set it to a unused value (best ones may be 6 or 11)
                  // To check: nmcli dev wifi list

void onReceiveEspNow(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len)
{
    ESPNowMessage msgIncoming;

    memcpy(&msgIncoming, incomingData, sizeof(msgIncoming));

    char srcMacStr[18];
    for (int i = 0; i < 6; i++)
    {
        sprintf(srcMacStr + i * 3, "%02X%s", info->src_addr[i], (i < 5) ? ":" : "");
    }

    char target_str[18];

    for (int i = 0; i < 6; i++)
    {
        sprintf(target_str + i * 3, "%02X%s", msgIncoming.target[i], (i < 5) ? ":" : "");
    }

    target_str[17] = '\0';

    Serial.printf(
        "[ESP-NOW] RECV:\n\tTARGET: %s\n\tSRC: %s\n\tFWD BLE: %d\n\tData: %s\n",
        target_str,
        srcMacStr,
        msgIncoming.fwd_ble,
        msgIncoming.data);

    if (memcmp(msgIncoming.target, macAddress, 6) == 0 || memcmp(msgIncoming.target, broadcastAddress, 6) == 0)
    {
        Serial.println("TODO: COMMAND HANDLER ESP NOW");
    }
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
    delay(50); // Wait for full init

    WiFi.macAddress(macAddress);

    char macStr[18];
    for (int i = 0; i < 6; i++)
    {
        sprintf(macStr + i * 3, "%02X%s", macAddress[i], (i < 5) ? ":" : "");
    }

    Serial.printf("[ESP-NOW] Board MAC address: %s\n", macStr);

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

    char target_str[18];

    for (int i = 0; i < 6; i++)
    {
        sprintf(target_str + i * 3, "%02X%s", message.target[i], (i < 5) ? ":" : "");
    }

    target_str[17] = '\0';

    Serial.printf(
        "[ESP-NOW] SEND:\n\tTarget: %s\n\tFWD BLE: %d\n\tData: %s\n",
        target_str,
        message.fwd_ble,
        message.data);
}
