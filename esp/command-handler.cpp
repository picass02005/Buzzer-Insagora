/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 * 
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#include <Arduino.h>
#include <stdlib.h>
#include <FreeRTOSConfig.h>
#include "esp-now.h"
#include "command-handler.h"
#include "pins.h"

#include "cmd-ping.h"
#include "cmd-led.h"
#include "cmd-clock.h"

void commands_handler(ESPNowMessage *msg)
{
    if (memcmp(msg->data, "PING", 4) == 0)
        command_task_maker(ping_cmd, msg);
    else if (memcmp(msg->data, "SLED", 4) == 0) // Set LED
        command_task_maker(set_led_cmd, msg);
    else if (memcmp(msg->data, "CLED", 4) == 0) // Clear LED
        command_task_maker(clear_led_cmd, msg);
    else if (memcmp(msg->data, "GLED", 4) == 0) // Get LED (number)
        command_task_maker(get_led_nb_cmd, msg);
    else if (memcmp(msg->data, "GCLK", 4) == 0) // Get clock
        command_task_maker(get_clock_cmd, msg);
    else if (memcmp(msg->data, "RCLK", 4) == 0) // Reset clock
        command_task_maker(reset_clock_cmd, msg);
    else if (memcmp(msg->data, "SCLK", 4) == 0)                           // Set clock
        command_task_maker(set_clock_cmd, msg, configMAX_PRIORITIES - 1); // High priority command
    else if (memcmp(msg->data, "ACLK", 4) == 0)                           // Automatic set clock based on master
        command_task_maker(auto_set_clock_cmd, msg);
}

void command_task(void *pvParameters)
{
    CommandTaskParams *params = (CommandTaskParams *)pvParameters;

    params->func(params->msg);

    free(params);
    vTaskDelete(NULL); // Clear task stack
}

void command_task_maker(void (*func)(ESPNowMessage), ESPNowMessage *message, int priority)
{
    CommandTaskParams *params = (CommandTaskParams *)malloc(sizeof(CommandTaskParams));
    params->func = func;
    params->msg = *message;

    xTaskCreatePinnedToCore(
        command_task,  // Function
        "CommandTask", // Name
        4096,          // Stack size (safe default)
        params,        // Parameters
        priority,      // Priority
        NULL,          // Handle
        1              // Core (0 or 1)
    );
}

void command_task_maker(void (*func)(ESPNowMessage), ESPNowMessage *message)
{
    command_task_maker(func, message, 1);
}
