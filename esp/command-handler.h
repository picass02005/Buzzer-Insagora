#include "esp-now.h"

#ifndef COMMAND_HANDLER_H
#define COMMAND_HANDLER_H

typedef struct
{
    void (*func)(ESPNowMessage);
    ESPNowMessage msg;
} CommandTaskParams;

void commands_handler(ESPNowMessage *msg);

void command_task(CommandTaskParams *params);
void command_task_maker(void (*func)(ESPNowMessage), ESPNowMessage *message);
void command_task_maker(void (*func)(ESPNowMessage), ESPNowMessage *message, int priority);

void ping_cmd(ESPNowMessage msg);

#endif
