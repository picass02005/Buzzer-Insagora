#include "ble.h"

#define BUTTON 32     // Button is normally closed
#define ONBOARD_LED 2 // Onboard led

void setup()
{
  // DEBUG
  Serial.begin(115200);

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
}

void loop()
{
}
