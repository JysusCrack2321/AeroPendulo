#include <Arduino.h>
#include <Wire.h>

constexpr uint8_t AnalogPin = 34; // GPIO34: AS5600 OUT
constexpr uint8_t Mpu6050Address = 0x68;
constexpr uint32_t Period = 50;
int offset = 0;
uint32_t lastRead = 0;
ulong degrees = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22); // SDA, SCL
  Wire.beginTransmission(Mpu6050Address);
  Wire.write(0x6B); // PWR_MGMT_1
  Wire.write(0);    // Wake up
  Wire.endTransmission();

  pinMode(AnalogPin, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(AnalogPin, ADC_11db);
  offset = analogRead(AnalogPin);
}

void readMpu6050() {
  Wire.beginTransmission(Mpu6050Address);
  Wire.write(0x3B); // ACCEL_XOUT_H
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(Mpu6050Address, 14) != 14) {
    return;
  }

  const int16_t ax = (Wire.read() << 8) | Wire.read();
  const int16_t ay = (Wire.read() << 8) | Wire.read();
  const int16_t az = (Wire.read() << 8) | Wire.read();
  const int16_t temperature = (Wire.read() << 8) | Wire.read();
  const int16_t gx = (Wire.read() << 8) | Wire.read();
  const int16_t gy = (Wire.read() << 8) | Wire.read();
  const int16_t gz = (Wire.read() << 8) | Wire.read();

  Serial.print(">accel_x:");
  Serial.println(ax / 16384.0f);
  Serial.print(">accel_y:");
  Serial.println(ay / 16384.0f);
  Serial.print(">accel_z:");
  Serial.println(az / 16384.0f);
  Serial.print(">temperature:");
  Serial.println(temperature / 340.0f + 36.53f);
  Serial.print(">gyro_x:");
  Serial.println(gx / 131.0f);
  Serial.print(">gyro_y:");
  Serial.println(gy / 131.0f);
  Serial.print(">gyro_z:");
  Serial.println(gz / 131.0f);
}

void readAnalogValue() {
  const int rawValue = analogRead(AnalogPin);
  degrees = map(rawValue-offset, 0, 4095, 0, 360);
  Serial.print(">raw:");
  Serial.println(rawValue - offset);
  Serial.print(">degrees:");
  Serial.println(degrees);
}

void loop() {
  const uint32_t now = millis();
  if (now - lastRead >= Period) {
    lastRead = now;
    readAnalogValue();
    readMpu6050();
  }
}