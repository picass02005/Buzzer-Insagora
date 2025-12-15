#ifndef BUTTON_INTERRUPT_H
#define BUTTON_INTERRUPT_H

#include "esp-now.h"

void IRAM_ATTR button_callback();
void button_task(int64_t *clock);
void init_button_interrupt();

#endif