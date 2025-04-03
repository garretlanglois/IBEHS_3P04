#include <SPI.h>
#include <ESP8266WiFi.h>

// Define pins for SPI
#define CS_PIN 15 // D8 on ESP8266

// ADXL342 Register Addresses
#define DEVID          0x00
#define THRESH_TAP     0x1D
#define OFSX           0x1E
#define OFSY           0x1F
#define OFSZ           0x20
#define DUR            0x21
#define POWER_CTL      0x2D
#define DATA_FORMAT    0x31
#define DATAX0         0x32
#define DATAX1         0x33
#define DATAY0         0x34
#define DATAY1         0x35
#define DATAZ0         0x36
#define DATAZ1         0x37

void setup() {
  Serial.begin(115200);
  Serial.println("\nADXL342 SPI Test on ESP8266");
  
  // Initialize SPI
  SPI.begin();
  SPI.setDataMode(SPI_MODE3); // ADXL3xx uses SPI mode 3
  SPI.setFrequency(1000000); // 1MHz
  
  // Set up CS pin
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);
  
  delay(100); // Give sensor time to start up
  
  // Check device ID
  byte deviceID = readRegister(DEVID);
  Serial.print("Device ID: 0x");
  Serial.println(deviceID, HEX);
  
  // Expected IDs: 0xE5 (ADXL345), 0xE6 (ADXL346), etc.
  // ADXL342 might return a different ID - check your datasheet
  if (deviceID != 0) {
    Serial.println("ADXL342 detected via SPI");
    
    // Configure the accelerometer
    writeRegister(POWER_CTL, 0); // Reset
    delay(10);
    writeRegister(DATA_FORMAT, 0x0B); // Full resolution, +/-16g
    writeRegister(POWER_CTL, 0x08); // Measurement mode
    
    Serial.println("ADXL342 initialized and ready");
  } else {
    Serial.println("ADXL342 not found! Check wiring");
  }
}

void loop() {
  // Read acceleration data
  int16_t x = (readRegister(DATAX1) << 8) | readRegister(DATAX0);
  int16_t y = (readRegister(DATAY1) << 8) | readRegister(DATAY0);
  int16_t z = (readRegister(DATAZ1) << 8) | readRegister(DATAZ0);
  
  // Convert to g (scale factor may need adjustment for ADXL342)
  float gx = x * 0.0039;
  float gy = y * 0.0039;
  float gz = z * 0.0039;
  
  Serial.print("X: "); Serial.print(x);
  Serial.print("\tY: "); Serial.print(y);
  Serial.print("\tZ: "); Serial.print(z);
  
  Serial.print("\tX(g): "); Serial.print(gx);
  Serial.print("\tY(g): "); Serial.print(gy);
  Serial.print("\tZ(g): "); Serial.println(gz);
  
  delay(100);
}

// Function to read from a register
byte readRegister(byte reg) {
  byte value;
  
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(reg | 0x80); // Set read bit (bit 7)
  value = SPI.transfer(0x00);
  digitalWrite(CS_PIN, HIGH);
  
  return value;
}

// Function to write to a register
void writeRegister(byte reg, byte value) {
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(reg); // Write bit is 0
  SPI.transfer(value);
  digitalWrite(CS_PIN, HIGH);
}
