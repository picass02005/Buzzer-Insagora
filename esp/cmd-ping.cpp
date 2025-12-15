#include <Arduino.h>
#include "esp-now.h"

void ping_cmd(ESPNowMessage msg) {
    ESPNowMessage res;
    snprintf(res.data, sizeof(res.data), "PONG %s", macStr);
    memset(&res.target, 0, sizeof(res.target));

    res.fwd_ble = 1;
    esp_now_send_message(&res);
}