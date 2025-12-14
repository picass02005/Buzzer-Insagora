#include <Arduino.h>
#include <stdint.h>
#include "ble.h"
#include "esp-now.h"
#include "pins.h"

// Number of packets sent to automatically set clock
#define AUTO_SET_CLK_NB 10
// Delay between each packet
#define AUTO_SET_CLK_DELAY 5


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
        clock_offset = millis();  // Reset overall clock to 0
    }
    else
    {
        clock_offset = INT64_MAX;
    }
}

void get_clock_cmd(ESPNowMessage msg)
{
    char mac_str[18];

    for (int i = 0; i < 6; i++)
    {
        sprintf(mac_str + i * 3, "%02X%s", macAddress[i], (i < 5) ? ":" : "");
    }

    mac_str[17] = '\0';

    ESPNowMessage res;
    snprintf(res.data, sizeof(res.data), "%lld %s", get_clock(), mac_str); // %lld => long long decimal
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

    if (clock_offset == INT64_MAX || s_clock < old_clock) {
        clock_offset = millis() - s_clock;
        #ifdef DEBUG
        Serial.printf("[CLOCK] Internal clock updated: old=%lld new=%lld get_clock=%lld\n", old_clock, s_clock, get_clock());
        #endif
    }
}

void auto_set_clock_cmd(ESPNowMessage msg)
{
    if (is_master == false) {
        return;  // Avoid other buzzers to be the "giver"
    }

    ESPNowMessage out_msg;
    memset(&out_msg.target, 0xFF, sizeof(out_msg.target));
    out_msg.fwd_ble = 0;

    // Reset all clocks
    snprintf(out_msg.data, sizeof(out_msg.data), "RCLK");
    esp_now_send_message(&out_msg);

    delay(AUTO_SET_CLK_DELAY);

    for (int i=0; i<AUTO_SET_CLK_NB; i++) {
        snprintf(out_msg.data, sizeof(out_msg.data), "SCLK %lld", get_clock());
        esp_now_send_message(&out_msg);

        delay(AUTO_SET_CLK_DELAY);
    }

    // Confirmation message
    ESPNowMessage res;
    snprintf(res.data, sizeof(res.data), "ACLK success");
    memset(&res.target, 0, sizeof(res.target));

    res.fwd_ble = 1;
    esp_now_send_message(&res);
}
