/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#include <Arduino.h>
#include <esp_now.h>
#include <WiFi.h>
#include <stdlib.h>
#include "pins.h"
#include "esp-now.h"
#include "command-handler.h"
#include "ble.h"

#define CHANNEL 1 // Recommended to set it to a unused value (best ones may be 6 or 11)
                  // To check: nmcli dev wifi list

uint8_t macAddress[6];
char macStr[18];

void onReceiveEspNow(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len)
{
    ESPNowMessage msgIncoming;
    memset(&msgIncoming, 0, sizeof(msgIncoming));

    memcpy(&msgIncoming, incomingData, min((unsigned int)len, sizeof(msgIncoming)));
    msgIncoming.data[sizeof(msgIncoming.data) - 1] = '\0';

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

#ifdef DEBUG
    Serial.printf(
        "[ESP-NOW] RECV:\n\tTARGET: %s\n\tSRC: %s\n\tCMD ID: %d\n\tFWD BLE: %d\n\tData: %s\n",
        target_str,
        srcMacStr,
        msgIncoming.cmd_id
        msgIncoming.fwd_ble,
        msgIncoming.data);
#endif

    if (is_master)
    {
        ble_send_message(&msgIncoming);
    }

    if (memcmp(msgIncoming.target, macAddress, 6) == 0 || memcmp(msgIncoming.target, broadcastAddress, 6) == 0)
    {
        commands_handler(&msgIncoming);
    }
}

void onSendEspNow(const wifi_tx_info_t *info, esp_now_send_status_t status)
{
    if (status == ESP_NOW_SEND_FAIL)
    {
#ifdef DEBUG
        Serial.println("[ESP-NOW] Failure while sending packet");
#endif
    }
}

void activate_esp_now()
{
    WiFi.mode(WIFI_STA);
    delay(50); // Wait for full init

    WiFi.macAddress(macAddress);

    for (int i = 0; i < 6; i++)
    {
        sprintf(macStr + i * 3, "%02X%s", macAddress[i], (i < 5) ? ":" : "");
    }

#ifdef DEBUG
    Serial.printf("[ESP-NOW] Board MAC address: %s\n", macStr);
#endif

    if (esp_now_init() != ESP_OK)
    {
#ifdef DEBUG
        Serial.println("[ESP-NOW] Error: couldn't establish init");
#endif

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
#ifdef DEBUG
        Serial.println("[ESP-NOW] Broadcast added as peer");
#endif
    }
    else
    {
#ifdef DEBUG
        Serial.println("[ESP-NOW] Unable to add broadcast as peer");
#endif
    }
}

void esp_now_send_message(const ESPNowMessage *message)
{
    if (message->fwd_ble != 0 && is_master)
    {
        ble_send_message(message);

        if (memcmp(message->target, broadcastAddress, 6) != 0)
        {
            return;
        }
    }

    esp_now_send(broadcastAddress, (uint8_t *)message, sizeof(*message));

    char target_str[18];

    for (int i = 0; i < 6; i++)
    {
        sprintf(target_str + i * 3, "%02X%s", message->target[i], (i < 5) ? ":" : "");
    }

    target_str[17] = '\0';

#ifdef DEBUG
    Serial.printf(
        "[ESP-NOW] SEND:\n\tTarget: %s\n\tCMD ID: %d\n\tFWD BLE: %d\n\tData: %s\n",
        target_str,
        message->cmd_id,
        message->fwd_ble,
        message->data);
#endif
}
