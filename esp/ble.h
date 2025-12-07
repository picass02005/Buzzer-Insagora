#include "esp-now.h"

#ifndef BLE_H
#define BLE_H

extern bool is_master;

void activate_ble();
void advertise_ble();
void ble_send_message(ESPNowMessage msg);

#endif
