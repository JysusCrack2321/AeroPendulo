#include <Arduino.h>
#include <Wire.h>

constexpr uint8_t AnalogPin = 34;      // GPIO34: AS5600 OUT
constexpr uint8_t pwmPin = 25;         // GPIO25
constexpr float TS = 0.01f;            // periodo de control [s]
constexpr uint32_t TS_US = 10000;
constexpr int SOBREMUESTREO = 16;
constexpr float GRADOS_POR_CUENTA = 360.0f / 4095.0f;
constexpr int SENTIDO = 1;             // +1 si subir el brazo a mano hace crecer theta
constexpr float THETA_COLGADO = 0.0f;     // theta medido desde la posicion colgada: 90 horizontal, 180 arriba
constexpr float THETA_CORTE = 190.0f;
constexpr float U_MAX = 255.0f;

constexpr uint8_t SCL_PIN = 22;
constexpr uint8_t SDA_PIN = 21;
constexpr uint8_t MPU = 0x68;
constexpr float LSB_G = 16384.0f;        // +-2 g
constexpr float LSB_GRADOS_S = 131.0f;   // +-250 grados/s
// ejes del MPU en el plano de giro del brazo: colgando, la gravedad cae sobre EJE_ABAJO
constexpr int EJE_ABAJO = 1;
constexpr int EJE_AVANCE = 0;
constexpr float SIGNO_ABAJO = -1.0f;
constexpr float SIGNO_AVANCE = 1.0f;
constexpr int EJE_GIRO = 2;
constexpr float SIGNO_GIRO = 1.0f;       // +1 si subir el brazo a mano da omega positiva
constexpr float ALFA_IMU = 0.98f;        // filtro complementario: peso del giroscopio

float Kp = 1.0f;      // duty/grado
float Ki = 1.0f;      // duty/(grado*s)
float Kd = 0.2f;      // duty*s/grado
float Tf = 0.02f;     // filtro de la derivada [s]
float beta = 0.0f;    // peso de la referencia en la accion P: la referencia entra por el integrador

struct Paso {
  float ref;          // grados desde la horizontal
  uint32_t ms;
};

const Paso SECUENCIA[] = {
  { 45.0f, 10000},
  { 90.0f, 10000},
  {105.0f, 10000},
  {120.0f, 10000},
  {135.0f, 10000},
  {150.0f, 10000},
  {135.0f, 10000},
  {120.0f, 10000},
  {105.0f, 10000},
  { 90.0f, 10000},
  { 45.0f, 10000},
};
constexpr int N_PASOS = sizeof(SECUENCIA) / sizeof(SECUENCIA[0]);

enum Modo { REPOSO, SECUENCIA_ESC, FIJA };
Modo modo = REPOSO;

int offset = 0;
float cuentaCont = 0.0f;   // cuenta desenvuelta: sigue contando al pasar de 180 grados
float ref = THETA_COLGADO;
float integral = 0.0f;
float derivada = 0.0f;
float eAnt = 0.0f;
float yAnt = THETA_COLGADO;
float pAccion = 0.0f;
bool imuOk = false;
float sesgoGiro = 0.0f;
float thetaAccCero = 0.0f;
float thetaImu = NAN;
float omegaImu = NAN;
uint32_t tImu = 0;
int paso = 0;
uint32_t tPaso = 0;
uint32_t tInicio = 0;
uint32_t tSiguiente = 0;
uint32_t tReposo = 0;
char linea[48];
int nLinea = 0;

int deltaEnvuelto(int raw, int base) {
  int d = raw - base;
  if (d > 2047) d -= 4096;
  if (d < -2048) d += 4096;
  return d;
}

void capturarCero() {
  const int base = analogRead(AnalogPin);
  long suma = 0;
  for (int i = 0; i < 64; i++) {
    suma += deltaEnvuelto(analogRead(AnalogPin), base);
  }
  offset = (base + (int)lround(suma / 64.0) + 4096) % 4096;
  cuentaCont = offset;
}

// desenvuelve respecto a la lectura anterior: valido mientras el brazo gire < 180 grados entre lecturas
float leerTheta() {
  const long base = lroundf(cuentaCont);
  const int baseMod = (int)(((base % 4096) + 4096) % 4096);
  long suma = 0;
  for (int i = 0; i < SOBREMUESTREO; i++) {
    suma += deltaEnvuelto(analogRead(AnalogPin), baseMod);
  }
  cuentaCont = base + (float)suma / SOBREMUESTREO;
  return THETA_COLGADO + SENTIDO * GRADOS_POR_CUENTA * (cuentaCont - offset);
}

bool escribirRegistro(uint8_t reg, uint8_t valor) {
  Wire.beginTransmission(MPU);
  Wire.write(reg);
  Wire.write(valor);
  return Wire.endTransmission() == 0;
}

bool leerImuCrudo(float acc[3], float giro[3]) {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(MPU, (uint8_t)14) != 14) return false;
  int16_t crudo[7];
  for (int i = 0; i < 7; i++) {
    const uint8_t alto = Wire.read();
    const uint8_t bajo = Wire.read();
    crudo[i] = (int16_t)((alto << 8) | bajo);
  }
  for (int i = 0; i < 3; i++) {
    acc[i] = crudo[i] / LSB_G;
    giro[i] = crudo[4 + i] / LSB_GRADOS_S;
  }
  return true;
}

float anguloAcc(const float acc[3]) {
  return atan2f(SIGNO_AVANCE * acc[EJE_AVANCE], SIGNO_ABAJO * acc[EJE_ABAJO]) * RAD_TO_DEG;
}

// colgando y quieto: sesgo del giroscopio y cero del angulo por acelerometro
void calibrarImu() {
  if (!imuOk) return;
  float acc[3], giro[3];
  float sumaGiro = 0.0f, sumaSen = 0.0f, sumaCos = 0.0f;
  int n = 0;
  for (int i = 0; i < 200; i++) {
    if (leerImuCrudo(acc, giro)) {
      sumaGiro += giro[EJE_GIRO];
      const float a = anguloAcc(acc) * DEG_TO_RAD;
      sumaSen += sinf(a);
      sumaCos += cosf(a);
      n++;
    }
    delay(2);
  }
  if (n == 0) {
    imuOk = false;
    return;
  }
  sesgoGiro = sumaGiro / n;
  thetaAccCero = atan2f(sumaSen, sumaCos) * RAD_TO_DEG;
  thetaImu = THETA_COLGADO;
  omegaImu = 0.0f;
  tImu = micros();
}

void iniciarImu() {
  Wire.begin(SDA_PIN, SCL_PIN, 400000);
  imuOk = escribirRegistro(0x6B, 0x00)   // despierta
       && escribirRegistro(0x1A, 0x03)   // DLPF 44 Hz
       && escribirRegistro(0x1B, 0x00)
       && escribirRegistro(0x1C, 0x00);
  delay(100);
  calibrarImu();
}

// filtro complementario; el acelerometro se desenvuelve alrededor del estimado para seguir pasando 180
void actualizarImu() {
  if (!imuOk) return;
  float acc[3], giro[3];
  if (!leerImuCrudo(acc, giro)) return;
  const uint32_t ahora = micros();
  const float dt = (ahora - tImu) * 1e-6f;
  tImu = ahora;
  omegaImu = SIGNO_GIRO * (giro[EJE_GIRO] - sesgoGiro);
  float thetaAcc = THETA_COLGADO + anguloAcc(acc) - thetaAccCero;
  const float prediccion = thetaImu + omegaImu * dt;
  thetaAcc += 360.0f * lroundf((prediccion - thetaAcc) / 360.0f);
  thetaImu = ALFA_IMU * prediccion + (1.0f - ALFA_IMU) * thetaAcc;
}

void motor(float u) {
  ledcWrite(pwmPin, (uint32_t)lroundf(u));
}

void imprimirGanancias() {
  Serial.printf("#K Kp=%.4f Ki=%.4f Kd=%.4f Tf=%.4f beta=%.3f Ts=%.3f\n", Kp, Ki, Kd, Tf, beta, TS);
}

void arrancar(Modo m, float r0) {
  const float y = leerTheta();
  integral = Kp * (1.0f - beta) * y;   // arranque sin salto: u0 = Kp*beta*(r - y)
  derivada = 0.0f;
  yAnt = y;
  ref = r0;
  eAnt = ref - y;
  paso = 0;
  modo = m;
  tInicio = millis();
  tPaso = tInicio;
  tSiguiente = micros();
  imprimirGanancias();
  Serial.println("#INICIO");
  Serial.println("t_ms,ref,theta,u,p,i,d,theta_imu,omega_imu");
}

void detener(const char *motivo) {
  motor(0);
  if (modo != REPOSO) {
    Serial.printf("#FIN %s\n", motivo);
  }
  modo = REPOSO;
}

void procesarComando(char *c) {
  switch (c[0]) {
    case 'S':
      arrancar(SECUENCIA_ESC, SECUENCIA[0].ref);
      break;
    case 'R':
      arrancar(FIJA, atof(c + 1));
      break;
    case 'T': {
      // cambia la referencia sin reiniciar el controlador; en reposo arranca con referencia fija
      const float r = constrain(atof(c + 1), 0.0f, 160.0f);
      if (modo == REPOSO) {
        arrancar(FIJA, r);
      } else {
        modo = FIJA;
        ref = r;
      }
      Serial.printf("#ref %.1f\n", ref);
      break;
    }
    case 'P':
      detener("parada");
      break;
    case 'Z':
      if (modo == REPOSO) {
        capturarCero();
        calibrarImu();
        Serial.println("#cero capturado");
      }
      break;
    case 'K': {
      float k[5];
      if (modo == REPOSO && sscanf(c + 1, "%f %f %f %f %f", &k[0], &k[1], &k[2], &k[3], &k[4]) == 5 && k[3] > 0) {
        Kp = k[0]; Ki = k[1]; Kd = k[2]; Tf = k[3]; beta = k[4];
      }
      imprimirGanancias();
      break;
    }
    case '?':
      imprimirGanancias();
      Serial.printf("#theta=%.2f modo=%d\n", leerTheta(), modo);
      break;
  }
}

void leerSerial() {
  while (Serial.available()) {
    const char ch = Serial.read();
    if (ch == '\n' || ch == '\r') {
      if (nLinea > 0) {
        linea[nLinea] = '\0';
        procesarComando(linea);
        nLinea = 0;
      }
    } else if (nLinea < (int)sizeof(linea) - 1) {
      linea[nLinea++] = ch;
    }
  }
}

void setup() {
  Serial.begin(115200);
  ledcAttach(pwmPin, 20000, 8);
  motor(0);
  pinMode(AnalogPin, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(AnalogPin, ADC_11db);
  delay(500);
  capturarCero();   // el brazo debe estar colgando quieto al encender
  iniciarImu();
  Serial.println(imuOk ? "#imu ok" : "#imu no responde: revisar SDA 21, SCL 22 y 3V3");
  Serial.println("#listo: S=secuencia de escalones, R <grados>=referencia fija, T <grados>=cambiar referencia en marcha, P=parar, Z=cero, K kp ki kd tf beta, ?");
}

void loop() {
  leerSerial();

  if (modo == REPOSO) {
    if ((int32_t)(micros() - tSiguiente) >= 0) {
      tSiguiente += TS_US;
      if ((int32_t)(micros() - tSiguiente) > 0) tSiguiente = micros();
      actualizarImu();
    }
    if (millis() - tReposo >= 200) {
      tReposo = millis();
      Serial.printf("#reposo theta=%.2f adc=%d mv=%u imu=%.2f omega=%.1f\n", leerTheta(), analogRead(AnalogPin), analogReadMilliVolts(AnalogPin), thetaImu, omegaImu);
    }
    return;
  }

  if ((int32_t)(micros() - tSiguiente) < 0) return;
  tSiguiente += TS_US;

  const uint32_t ahora = millis();
  if (modo == SECUENCIA_ESC && ahora - tPaso >= SECUENCIA[paso].ms) {
    paso++;
    if (paso >= N_PASOS) {
      detener("secuencia");
      return;
    }
    tPaso = ahora;
    ref = SECUENCIA[paso].ref;
  }

  const float y = leerTheta();
  actualizarImu();
  if (y > THETA_CORTE || y < -THETA_CORTE) {
    detener("corte");
    return;
  }

  const float e = ref - y;
  derivada = (2.0f * Tf - TS) / (2.0f * Tf + TS) * derivada - 2.0f * Kd / (2.0f * Tf + TS) * (y - yAnt);
  const float integralNueva = integral + Ki * TS * 0.5f * (e + eAnt);
  const float uLibre = Kp * (beta * ref - y) + integralNueva + derivada;

  // anti-windup por integracion condicional: no integra si empuja mas alla de la saturacion
  if (!((uLibre > U_MAX && e > 0) || (uLibre < 0 && e < 0))) {
    integral = integralNueva;
  }
  pAccion = Kp * (beta * ref - y);
  const float u = constrain(pAccion + integral + derivada, 0.0f, U_MAX);

  motor(u);
  eAnt = e;
  yAnt = y;

  Serial.printf("%lu,%.1f,%.2f,%d,%.1f,%.1f,%.1f,%.2f,%.1f\n", (unsigned long)(ahora - tInicio), ref, y, (int)lroundf(u),
                pAccion, integral, derivada, thetaImu, omegaImu);
}
