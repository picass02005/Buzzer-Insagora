#define ONBOARD_LED 2  // Onboard led

void setup() {
  // Set pin mode
  pinMode(ONBOARD_LED, OUTPUT);

  // Welcome blink
  for (int i=0; i<3; i++) {
    digitalWrite(ONBOARD_LED,HIGH);
    delay(50);
    digitalWrite(ONBOARD_LED,LOW);
    delay(50);
  }
}

void loop() {
}