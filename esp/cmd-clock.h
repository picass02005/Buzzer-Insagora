/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#ifndef CMD_CLOCK_H
#define CMD_CLOCK_H

#include "esp-now.h"

extern int64_t clock_offset;

int64_t get_clock();
void reset_clock();
void lltoa(long long value, char *buf);

void get_clock_cmd(ESPNowMessage msg);
void reset_clock_cmd(ESPNowMessage msg);
void set_clock_cmd(ESPNowMessage msg);
void auto_set_clock_cmd(ESPNowMessage msg);

#endif