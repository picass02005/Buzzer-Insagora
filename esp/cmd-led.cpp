#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include "esp-now.h"
#include "pins.h"

Adafruit_NeoPixel ws2812b(LED_NB, LED_STRIP, NEO_GRB + NEO_KHZ800); // Define object for adafruit neopixel

void setup_led()
{
    ws2812b.begin(); // Init leds
    ws2812b.clear(); // Clears LED buffer
    ws2812b.show();
}

void led_welcome_animation()
{
    digitalWrite(ONBOARD_LED, HIGH);

    ws2812b.clear();

    for (int j = 0; j < 250; j = j + 10)
    {
        for (int i = 0; i < LED_NB; i++)
        {
            ws2812b.setPixelColor(i, ws2812b.Color(j, 0, j));
        }

        ws2812b.show();
        delay(10);
    }

    for (int j = 250; j > 0; j = j - 10)
    {
        for (int i = 0; i < LED_NB; i++)
        {
            ws2812b.setPixelColor(i, ws2812b.Color(j, 0, j));
        }

        ws2812b.show();
        delay(10);
    }

    ws2812b.clear();
    ws2812b.show();

    digitalWrite(ONBOARD_LED, LOW);
}

void led_bluetooth_connect()
{
    digitalWrite(ONBOARD_LED, HIGH);

    ws2812b.clear();

    for (int j = 0; j < 2; j++)
    {
        ws2812b.clear();
        for (int i = 0; i < LED_NB; i++)
        {
            ws2812b.setPixelColor(i, ws2812b.Color(0, 0, 255));
        }
        ws2812b.show();
        delay(125);

        ws2812b.clear();
        ws2812b.show();
        delay(125);
    }

    digitalWrite(ONBOARD_LED, LOW);
}

void led_bluetooth_disconnect()
{
    digitalWrite(ONBOARD_LED, HIGH);

    ws2812b.clear();

    for (int j = 0; j < 2; j++)
    {
        ws2812b.clear();
        for (int i = 0; i < LED_NB; i++)
        {
            ws2812b.setPixelColor(i, ws2812b.Color(255, 0, 0));
        }
        ws2812b.show();
        delay(125);

        ws2812b.clear();
        ws2812b.show();
        delay(125);
    }

    digitalWrite(ONBOARD_LED, LOW);
}

void led_master()
{
    digitalWrite(ONBOARD_LED, HIGH);

    ws2812b.clear();

    for (int i = 0; i < LED_NB; i++)
    {
        ws2812b.setPixelColor(i, ws2812b.Color(255, 0, 255));
    }
    ws2812b.show();
    delay(500);

    ws2812b.clear();
    ws2812b.show();

    digitalWrite(ONBOARD_LED, LOW);
}

void set_led_cmd(ESPNowMessage msg)
{
    // Message format: 3 bytes per LED (RGB)

    uint8_t color[3];

#ifdef DEBUG
    char print[200];
    memset(print, 0, sizeof(print));

    memcpy(print, "[LED] SETTING:", 14);
#endif

    for (int i = 0; i < LED_NB; i++)
    {
        memcpy(color, &(msg.data[5 + (i * 3)]), 3);

        ws2812b.setPixelColor(i, ws2812b.Color(color[0], color[1], color[2]));

#ifdef DEBUG
        sprintf(&(print[14 + i * 7]), " %02X%02X%02X", color[0], color[1], color[2]);
#endif
    }

#ifdef DEBUG
    Serial.println(print);
#endif

    ws2812b.show();
}

void clear_led_cmd(ESPNowMessage msg)
{
    ws2812b.clear();
    ws2812b.show();
}

void get_led_nb_cmd(ESPNowMessage msg)
{
    ESPNowMessage res;
    snprintf(res.data, sizeof(res.data), "%d", LED_NB);
    memset(&res.target, 0, sizeof(res.target));

    res.fwd_ble = 1;
    esp_now_send_message(&res);
}
