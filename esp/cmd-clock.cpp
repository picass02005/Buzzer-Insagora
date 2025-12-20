/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#include <Arduino.h>
#include <stdint.h>
#include "ble.h"
#include "esp-now.h"
#include "pins.h"

// Number of packets sent to automatically set clock
#define AUTO_SET_CLK_NB 10
// Delay between each packet
#define AUTO_SET_CLK_DELAY 10

int64_t clock_offset;

int64_t get_clock()
{
    if (clock_offset == INT64_MAX)
    {
        return INT64_MAX;
    }
    else
    {
        return millis() - clock_offset;
    }
}

void reset_clock()
{
    if (is_master == true)
    {
        clock_offset = millis(); // Reset overall clock to 0
    }
    else
    {
        clock_offset = INT64_MAX;
    }
}

void lltoa(long long value, char *buf)
{
    // Write value in buf
    // buf need to be at least 22 chars long
    // Qicker than sprintf

    char tmp[21];
    int i = 0;
    int neg = value < 0;

    if (neg)
        value = -value;

    do
    {
        tmp[i++] = '0' + (value % 10);
        value /= 10;
    } while (value);

    int j = 0;
    if (neg)
        buf[j++] = '-';

    while (i--)
        buf[j++] = tmp[i];
    buf[j] = '\0';
}

void get_clock_cmd(ESPNowMessage msg)
{
    char mac_str_tmp[sizeof(macStr)];
    char clock_buffer[22];

    memcpy(&mac_str_tmp, &macStr, sizeof(macStr));
    mac_str_tmp[sizeof(mac_str_tmp) - 1] = ' ';

    lltoa(get_clock(), clock_buffer);

    ESPNowMessage res;

    memcpy(&res.data, "GCLK ", 5);
    memcpy(&(res.data[5]), &mac_str_tmp, sizeof(mac_str_tmp));
    memcpy(&(res.data[sizeof(mac_str_tmp) + 5]), &clock_buffer, sizeof(clock_buffer));

    memset(&res.target, 0, sizeof(res.target));

    res.fwd_ble = 1;
    esp_now_send_message(&res);
}

void reset_clock_cmd(ESPNowMessage msg)
{
    reset_clock();
}

void set_clock_cmd(ESPNowMessage msg)
{
    u_int32_t actual_millis = millis();
    int64_t s_clock;

    int64_t old_clock;

    // 1st argument is the clock used sync to (s_clock)
    // We change clock_offset if actual_millis + s_clock < get_clock

    sscanf(msg.data, "SCLK %lld", &s_clock);

    old_clock = actual_millis - clock_offset;

    if (clock_offset == INT64_MAX || s_clock < old_clock)
    {
        clock_offset = millis() - s_clock;
#ifdef DEBUG
        Serial.printf("[CLOCK] Internal clock updated: old=%lld new=%lld get_clock=%lld\n", old_clock, s_clock, get_clock());
#endif
    }
}

void auto_set_clock_cmd(ESPNowMessage msg)
{
    if (is_master == true)
    {
        reset_clock(); // Reset master clock
    }
    else
    {
        return; // Avoid other buzzers to be the "giver"
    }

    ESPNowMessage out_msg;
    memset(&out_msg.target, 0xFF, sizeof(out_msg.target));
    out_msg.fwd_ble = 0;

    // Reset all clocks
    memcpy(&out_msg.data, "RCLK\0", 5);

    delay(3); // Avoid spamming other buffers
    esp_now_send_message(&out_msg);

    delay(AUTO_SET_CLK_DELAY);

    for (int i = 0; i < AUTO_SET_CLK_NB; i++)
    {
        memcpy(out_msg.data, "SCLK ", 5);
        lltoa(get_clock(), &(out_msg.data[5]));
        esp_now_send_message(&out_msg);

        delay(AUTO_SET_CLK_DELAY);
    }

    // Confirmation message
    ESPNowMessage res;
    memcpy(&res.data, "ACLK success\0", 13);
    memset(&res.target, 0, sizeof(res.target));

    res.fwd_ble = 1;
    esp_now_send_message(&res);
}
