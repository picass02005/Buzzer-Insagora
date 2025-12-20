/*
 * Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

#ifndef BUTTON_INTERRUPT_H
#define BUTTON_INTERRUPT_H

#include "esp-now.h"

void IRAM_ATTR button_callback();
void button_task(int64_t *clock);
void init_button_interrupt();

#endif