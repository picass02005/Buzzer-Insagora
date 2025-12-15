/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 * 
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#include "esp-now.h"

#ifndef BLE_H
#define BLE_H

extern bool is_master;

void activate_ble();
void advertise_ble();
void ble_send_message(const ESPNowMessage *msg);

#endif
