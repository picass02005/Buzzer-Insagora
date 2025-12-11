#include <Arduino.h>
#include "esp-now.h"

void ping_cmd(ESPNowMessage msg) {
    char mac_str[18];

    for (int i = 0; i < 6; i++)
    {
        sprintf(mac_str + i * 3, "%02X%s", macAddress[i], (i < 5) ? ":" : "");
    }

    mac_str[17] = '\0';

    ESPNowMessage res;
    snprintf(res.data, sizeof(res.data), "PONG %s", mac_str);
    memset(&res.target, 0, sizeof(res.target));

    res.fwd_ble = 1;
    esp_now_send_message(&res);
}