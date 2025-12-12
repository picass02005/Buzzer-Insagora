#include <Arduino.h>
#include "ble.h"
#include "esp-now.h"
#include "cmd-led.h"
#include "pins.h"

void setup()
{
    #ifdef DEBUG
    Serial.begin(9600);
    #endif

    // Set pin mode
    pinMode(BUTTON, INPUT_PULLUP);
    pinMode(ONBOARD_LED, OUTPUT);

    // Setup LED
    setup_led();
    led_welcome_animation();

    // Set master if button pressed
    if (digitalRead(BUTTON))
    {
        is_master = false;
    }
    else
    {
        is_master = true;

        activate_ble();

        led_master();
    }

    activate_esp_now();
}

void loop()
{
}
