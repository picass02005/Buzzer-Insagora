#include <Arduino.h>
#include <stdlib.h>
#include "esp-now.h"
#include "command-handler.h"
#include "pins.h"

#include "cmd-ping.h"


void commands_handler(ESPNowMessage *msg)
{
    #ifdef DEBUG
    Serial.printf("TODO: commands handler: %s\n", msg->data);
    #endif

    if (memcmp(msg->data, "PING", 4) == 0)
        command_task_maker(ping_cmd, msg);
}

void command_task(void* pvParameters)
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

void command_task_maker(void (*func)(ESPNowMessage), ESPNowMessage *message) {
    command_task_maker(func, message, 1);
}
