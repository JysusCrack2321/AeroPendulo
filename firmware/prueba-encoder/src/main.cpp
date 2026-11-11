#include <Arduino.h>
#include <Wire.h>

constexpr uint8_t AnalogPin = 34;      // GPIO34: AS5600 OUT
constexpr uint8_t pwmPin = 25;         // GPIO25
constexpr uint8_t As5600Address = 0x36;
constexpr uint32_t Period = 100;
uint32_t lastRead = 0;

bool leerRegistro(uint8_t reg, uint8_t *datos, uint8_t n) {
  Wire.beginTransmission(As5600Address);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(As5600Address, n) != n) {
    return false;
  }
  for (uint8_t i = 0; i < n; i++) {
    datos[i] = Wire.read();
  }
  return true;
}

void setup() {
  Serial.begin(115200);
  ledcAttach(pwmPin, 20000, 8);
  ledcWrite(pwmPin, 0);                // motor siempre apagado
  Wire.begin(21, 22);                  // SDA, SCL
  pinMode(AnalogPin, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(AnalogPin, ADC_11db);
}

void loop() {
  const uint32_t now = millis();
  if (now - lastRead < Period) return;
  lastRead = now;

  long suma = 0;
  for (int i = 0; i < 16; i++) {
    suma += analogRead(AnalogPin);
  }
  const float cuentas = suma / 16.0f;
  Serial.printf(">adc:%.1f\n", cuentas);
  Serial.printf(">voltios:%.3f\n", analogReadMilliVolts(AnalogPin) / 1000.0f);
  Serial.printf(">grados_adc:%.1f\n", cuentas * 360.0f / 4095.0f);

  // I2C solo responde si SDA/SCL estan cableados a 21/22
  uint8_t d[2];
  if (!leerRegistro(0x0B, d, 1)) {
    Serial.println("#i2c: sin respuesta en 0x36");
    return;
  }
  const uint8_t status = d[0];         // bit5 MD imán detectado, bit4 ML débil, bit3 MH fuerte
  Serial.printf("#iman %s%s%s\n", (status & 0x20) ? "detectado" : "NO detectado",
                (status & 0x10) ? ", muy debil" : "", (status & 0x08) ? ", muy fuerte" : "");
  if (leerRegistro(0x0C, d, 2)) {
    const uint16_t raw = ((d[0] & 0x0F) << 8) | d[1];
    Serial.printf(">raw_i2c:%u\n>grados_i2c:%.1f\n", raw, raw * 360.0f / 4096.0f);
  }
  if (leerRegistro(0x1A, d, 1)) {
    Serial.printf(">agc:%u\n", d[0]);  // 0-255 a 3.3 V; ideal a mitad de escala
  }
  if (leerRegistro(0x08, d, 1)) {
    Serial.printf("#OUTS=%u (0 analogico completo, 1 analogico reducido, 2 PWM)\n", (d[0] >> 4) & 0x03);
  }
}
