#ifndef CMD_LED_H
#define CMD_LED_H

#include "esp-now.h"

void setup_led();
void led_welcome_animation();

void led_bluetooth_connect();
void led_bluetooth_disconnect();
void led_master();

void set_led_cmd(ESPNowMessage msg);
void clear_led_cmd(ESPNowMessage msg);
void get_led_nb_cmd(ESPNowMessage msg);

#endif