// Prueba rapida del motor del aeropendulo. Pin: D25 (GPIO25).
//
// Dos modos, se elige abajo con MOTOR_ESC:
//   1 = ESC de brushless: pulso de 1000-2000 us a 50 Hz (como un servo)
//   0 = motor DC con MOSFET: PWM de 20 kHz y duty en % (0-100)
//
// Comandos por el monitor serial (115200):
//   a          armar el ESC (manda 1000 us durante 3 s)   [solo modo ESC]
//   v1500      fijar valor: us si es ESC, % si es DC
//   s          barrido lento de subida y bajada
//   p          parar (ESC: 1000 us, DC: 0 %)
//   ?          mostrar estado
//
// Cada 200 ms imprime tambien el angulo del AS5600 (A34) para ver si el brazo
// se mueve. Nada de esto toca el firmware bueno: es un sketch aparte.

#include <Arduino.h>

#define MOTOR_ESC 1          // <-- cambialo a 0 para motor DC con MOSFET

constexpr uint8_t PIN_MOTOR = 25;
constexpr uint8_t PIN_AS5600 = 34;
constexpr uint32_t PERIODO_MS = 200;

constexpr int ESC_MIN_US = 1000;
constexpr int ESC_MAX_US = 2000;
constexpr int DC_MAX_PCT = 100;

int offset = 0;
uint32_t ultimoMs = 0;
char comando[16];
byte lenComando = 0;
bool barriendo = false;

// ---------------------------------------------------------------- salida PWM
void pwmInit() {
#if MOTOR_ESC
  constexpr uint32_t FREQ = 50;          // ESC: 50 Hz
  constexpr uint8_t RES = 16;            // 16 bits -> 20000 us de periodo
#else
  constexpr uint32_t FREQ = 20000;       // DC: fuera del audible
  constexpr uint8_t RES = 10;            // 0-1023
#endif
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_MOTOR, FREQ, RES);
#else
  ledcSetup(0, FREQ, RES);
  ledcAttachPin(PIN_MOTOR, 0);
#endif
}

void pwmEscribir(uint32_t duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(PIN_MOTOR, duty);
#else
  ledcWrite(0, duty);
#endif
}

// valor fisico -> duty del timer
uint32_t aDuty(int valor) {
#if MOTOR_ESC
  valor = constrain(valor, ESC_MIN_US, ESC_MAX_US);
  // periodo = 1e6/50 = 20000 us; duty de 16 bits = valor/20000 * 65535
  return (uint32_t)((float)valor / 20000.0f * 65535.0f);
#else
  valor = constrain(valor, 0, DC_MAX_PCT);
  return (uint32_t)((float)valor / 100.0f * 1023.0f);
#endif
}

void aplicar(int valor) {
  pwmEscribir(aDuty(valor));
}

void parar() {
  barriendo = false;
#if MOTOR_ESC
  aplicar(ESC_MIN_US);
#else
  aplicar(0);
#endif
}

// ---------------------------------------------------------------- AS5600
void imprimirAngulo() {
  int raw = analogRead(PIN_AS5600) - offset;
  long grados = map(raw, 0, 4095, 0, 360);
  if (grados < 0) grados += 360;      // el map puede dar negativo
  Serial.print("  angulo=");
  Serial.print(grados);
  Serial.print(" raw=");
  Serial.println(raw);
}

// ---------------------------------------------------------------- comandos
void leerComandos() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      comando[lenComando] = '\0';
      if (lenComando > 0) {
        if (comando[0] == 'v' || comando[0] == 'V') {
          int v = atoi(comando + 1);
          barriendo = false;
          aplicar(v);
          Serial.print("fijado en ");
          Serial.println(v);
        } else if (comando[0] == 's' || comando[0] == 'S') {
          barriendo = true;
          Serial.println("barrido");
        } else if (comando[0] == 'p' || comando[0] == 'P') {
          parar();
          Serial.println("parado");
        } else if (comando[0] == 'a' || comando[0] == 'A') {
#if MOTOR_ESC
          Serial.println("armando ESC (1000 us, 3 s)");
          aplicar(ESC_MIN_US);
          delay(3000);
          Serial.println("ESC armado");
#else
          Serial.println("modo DC: no hace falta armar");
#endif
        } else if (comando[0] == '?') {
          Serial.print("modo=");
#if MOTOR_ESC
          Serial.println("ESC 50 Hz 1000-2000 us");
#else
          Serial.println("DC 20 kHz 0-100 %");
#endif
        } else {
          Serial.println("comandos: a v<solo> s p ?");
        }
      }
      lenComando = 0;
      continue;
    }
    if (lenComando < sizeof(comando) - 1) comando[lenComando++] = c;
    else lenComando = 0;
  }
}

// ---------------------------------------------------------------- barrido
void barrido() {
  static uint32_t t0 = 0;
  static bool iniciado = false;
  if (!barriendo) { iniciado = false; return; }
  if (!iniciado) { t0 = millis(); iniciado = true; }

  const uint32_t periodo = 8000;               // 8 s de subida y 8 de bajada
  float fase = (float)((millis() - t0) % (2 * periodo)) / periodo;   // 0..2
  float x = fase < 1.0f ? fase : 2.0f - fase;                        // 0..1..0
#if MOTOR_ESC
  int valor = ESC_MIN_US + (int)(x * (ESC_MAX_US - ESC_MIN_US));
#else
  int valor = (int)(x * DC_MAX_PCT);
#endif
  aplicar(valor);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_AS5600, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_AS5600, ADC_11db);
  offset = analogRead(PIN_AS5600);

  pwmInit();
  parar();

  Serial.println("\nprueba de motor - D25");
  Serial.print("modo: ");
#if MOTOR_ESC
  Serial.println("ESC (1000-2000 us, 50 Hz)");
#else
  Serial.println("DC con MOSFET (0-100 %, 20 kHz)");
#endif
  Serial.println("a=armar  v<valor>=fijar  s=barrido  p=parar  ?=estado");
  ultimoMs = millis();
}

void loop() {
  leerComandos();
  barrido();

  if (millis() - ultimoMs >= PERIODO_MS) {
    ultimoMs = millis();
    imprimirAngulo();
  }
}
