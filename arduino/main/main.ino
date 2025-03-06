#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// Create the sensor object using a unique ID (e.g., 55)
// The default I²C address is 0x28. If your sensor uses the alternate
// address, you can set it here.
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for Serial port to be available (for boards like Leonardo)
  }

  Serial.println("BNO055 Sensor Test");

  // Initialize the sensor
  if (!bno.begin()) {
    Serial.println("Failed to initialize the BNO055! Check your wiring or I2C address.");
    while (1);
  }
  delay(1000);
  
  // Use external crystal if available for better accuracy
  bno.setExtCrystalUse(true);
}

void loop() {
  // Read Euler angles (orientation) from the sensor
  imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
  
  // Read acceleration data (in m/s²)
  imu::Vector<3> acceleration =
      bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);
      
  // Read temperature data (in °C)
  float temperature = bno.getTemp();

  // Print Euler angles (orientation)
  Serial.print("Orientation (Euler angles in °): ");
  Serial.print("X: ");
  Serial.print(euler.x());
  Serial.print("  Y: ");
  Serial.print(euler.y());
  Serial.print("  Z: ");
  Serial.println(euler.z());

  // Print acceleration data
  Serial.print("Acceleration (m/s²): ");
  Serial.print("X: ");
  Serial.print(acceleration.x());
  Serial.print("  Y: ");
  Serial.print(acceleration.y());
  Serial.print("  Z: ");
  Serial.println(acceleration.z());

  // Print temperature data
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.println(" °C");

  Serial.println("-----------------------------------");

  // Wait for a second before the next reading.
  delay(1000);
}
