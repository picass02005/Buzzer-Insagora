/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#include <Arduino.h>
#include "cmd-clock.h"
#include "esp-now.h"
#include "pins.h"

#define INTERRUPT_PCK_SEND 3
#define INTERRUPT_PCK_DELAY 2
#define INTERRUPT_TASK_DELAY 10

QueueHandle_t buttonQueue;
uint8_t buttonPressId = 0;

void IRAM_ATTR button_callback()
{
    const int64_t clock = get_clock();

    if (uxQueueSpacesAvailable(buttonQueue) > 0)
    {
        xQueueSendFromISR(buttonQueue, &clock, NULL);
    }
}

void button_task(void *params)
{
    int64_t clock;
    char clock_str[22];

    while (true)
    {
        if (xQueueReceive(buttonQueue, &clock, portMAX_DELAY))
        {
#ifdef DEBUG
            Serial.println("[BUTTON] Pressed");
#endif

            lltoa(clock, clock_str);

            ESPNowMessage res;

            memcpy(res.data, "BPRS ", 5);
            memcpy(&(res.data[5]), macStr, sizeof(macStr) - 1);
            res.data[4 + sizeof(macStr)] = ' ';
            memcpy(&(res.data[5 + sizeof(macStr)]), clock_str, sizeof(clock_str));
            res.data[5 + sizeof(macStr) + sizeof(clock_str)] = '\0';

            memset(&res.target, 0, sizeof(res.target));

            res.cmd_id = buttonPressId++;  // Return current value then ++
            res.fwd_ble = 1;

            for (int i = 0; i < INTERRUPT_PCK_SEND; i++)
            {
                esp_now_send_message(&res);
                vTaskDelay(INTERRUPT_PCK_DELAY);
            }

            xQueueReset(buttonQueue); // Reset the queue to avoid bouncing
        }
        vTaskDelay(INTERRUPT_TASK_DELAY);
    }
}

void init_button_interrupt()
{
    buttonQueue = xQueueCreate(1, sizeof(int64_t)); // Queue can take up to 5 elements

    xTaskCreate(
        button_task,
        "Button queue task",
        4096, // Default stack size
        NULL,
        1,
        NULL);

    attachInterrupt(
        digitalPinToInterrupt(BUTTON),
        button_callback,
        FALLING // Trigger when button is pressed
    );

#ifdef DEBUG
    Serial.println("[BUTTON] Callback attached");
#endif
}
