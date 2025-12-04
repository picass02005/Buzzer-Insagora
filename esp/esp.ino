#include "ble.h"
#include "esp-now.h"
#include "pins.h"

void setup()
{
  // DEBUG
  Serial.begin(9600);

  // Set pin mode
  pinMode(BUTTON, INPUT_PULLUP);
  pinMode(ONBOARD_LED, OUTPUT);

  // Welcome blink
  for (int i = 0; i < 3; i++)
  {
    digitalWrite(ONBOARD_LED, HIGH);
    delay(50);
    digitalWrite(ONBOARD_LED, LOW);
    delay(50);
  }

  // Set master if button pressed
  if (digitalRead(BUTTON))
  {
    is_master = false;
  }
  else
  {
    is_master = true;

    digitalWrite(ONBOARD_LED, HIGH);
    delay(500);
    digitalWrite(ONBOARD_LED, LOW);

    activate_ble();
  }

  activate_esp_now();
}

void loop()
{
}
