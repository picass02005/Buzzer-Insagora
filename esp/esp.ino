/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#include <Arduino.h>
#include "ble.h"
#include "esp-now.h"
#include "pins.h"
#include "button-interrupt.h"
#include "cmd-led.h"
#include "cmd-clock.h"

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

    init_button_interrupt();

    // Setup clock
    reset_clock();
}

void loop()
{
}
