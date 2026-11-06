// Prueba del motor: sube y baja la potencia en bucle. Pin D25.
#include <Arduino.h>

const uint8_t PIN_MOTOR = 25;
const uint32_t FRECUENCIA = 20000;   // 20 kHz, fuera del audible
const uint8_t BITS = 10;             // 0 a 1023

void setup() {
  ledcAttach(PIN_MOTOR, FRECUENCIA, BITS);
}

void loop() {
  for (int d = 0; d <= 1023; d += 5) {      // sube en ~4 s
    ledcWrite(PIN_MOTOR, d);
    delay(20);
  }
  for (int d = 1023; d >= 0; d -= 5) {      // baja en ~4 s
    ledcWrite(PIN_MOTOR, d);
    delay(20);
  }
}
