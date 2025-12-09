#include <Arduino.h>
#include <stdlib.h>
#include "esp-now.h"
#include "commands.h"
#include "pins.h"


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

void ping_cmd(ESPNowMessage msg) {
    char mac_str[18];

    for (int i = 0; i < 6; i++)
    {
        sprintf(mac_str + i * 3, "%02X%s", macAddress[i], (i < 5) ? ":" : "");
    }

    mac_str[17] = '\0';

    ESPNowMessage res;
    snprintf(res.data, sizeof(res.data), "PONG %s", mac_str);
    memset(&res.target, 0, sizeof(res.target));

    res.fwd_ble = 1;
    esp_now_send_message(&res);
}
