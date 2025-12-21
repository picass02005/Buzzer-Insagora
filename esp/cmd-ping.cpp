/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#include <Arduino.h>
#include "esp-now.h"

void ping_cmd(ESPNowMessage msg)
{
    ESPNowMessage res;
    snprintf(res.data, sizeof(res.data), "PING %s", macStr);
    memset(&res.target, 0, sizeof(res.target));

    res.cmd_id = msg.cmd_id;
    res.fwd_ble = 1;
    esp_now_send_message(&res);
}