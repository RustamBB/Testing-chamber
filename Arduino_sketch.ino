#include <DHT.h>
#include <Wire.h>
#include <BH1750FVI.h>
#include <RBDdimmer.h>

// Define pin numbers
const int MPU_addr = 0x68;
int16_t axis_X, axis_Y, axis_Z;
int minVal = 265;
int maxVal = 402;
double x;
double y;
double z;
const int DHTPIN = 4;
// dimmer pin
#define USE_SERIAL Serial
#define outputPin1 12
#define outputPin2 13
#define zerocross 2

dimmerLamp dimmer1(outputPin1);
dimmerLamp dimmer2(outputPin2);

// Create instances for sensors
DHT dht(DHTPIN, DHT22);
BH1750FVI LightSensor(BH1750FVI::k_DevModeContLowRes);

void setup() {
  Serial.begin(9600);

  // Initialize DHT22 sensor
  dht.begin();

  // Initialize MPU6050
  Wire.begin();
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  // Initialize BH1750FVI sensor
  LightSensor.begin();
  LightSensor.SetMode(132);

  // dimmer
  USE_SERIAL.begin(9600);
  dimmer1.begin(NORMAL_MODE, ON);
  dimmer2.begin(NORMAL_MODE, ON);
}

void loop() {
  // Read dimmer values from Serial (if available)
  if (Serial.available() > 0) {
    String dimmerValues = Serial.readStringUntil('\n'); 
    int commaIndex = dimmerValues.indexOf(',');
    if (commaIndex != -1) {
      int dimmer1Value = dimmerValues.substring(0, commaIndex).toInt();
      int dimmer2Value = dimmerValues.substring(commaIndex + 1).toInt();
      dimmer1.setPower(dimmer1Value);
      dimmer2.setPower(dimmer2Value);
    }
  }

  // Read sensor data
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Read MPU6050 data (accelerometer)
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr, 14, true);
  int axis_X = Wire.read() << 8 | Wire.read();
  int axis_Y = Wire.read() << 8 | Wire.read();
  int axis_Z = Wire.read() << 8 | Wire.read();

  // Calculate angles (optional)
  int xAng = map(axis_X, minVal, maxVal, -90, 90);
  int yAng = map(axis_Y, minVal, maxVal, -90, 90);
  int zAng = map(axis_Z, minVal, maxVal, -90, 90);
  double xAngle = RAD_TO_DEG * (atan2(-yAng, -zAng) + PI);
  double yAngle = RAD_TO_DEG * (atan2(-xAng, -zAng) + PI);

  // Read BH1750FVI data (light intensity)
  uint16_t lux = LightSensor.GetLightIntensity();

  // Print sensor values
  Serial.print("H");
  Serial.print(humidity);
  Serial.print("T");
  Serial.print(temperature);
  Serial.print("B");
  Serial.print(yAngle);
  Serial.print("L");
  Serial.println(lux * 2.49);

  delay(10); // Delay for stability
}
