/*
 * Verification.cpp
 * Purpose: Verify sampling rate and delay for BNO055 sensor with ESP8266
 */

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// Create BNO055 sensor object
Adafruit_BNO055 bno = Adafruit_BNO055(55);

// Test parameters
const unsigned long TEST_DURATION_MS = 20000; // 20 seconds
const unsigned int MIN_SAMPLE_FREQ = 10000;   // 10 kHz
const unsigned long MAX_DELAY_US = 100000;    // 100 ms in microseconds

// Variables for timing
unsigned long startTimeMs = 0;
unsigned long totalSamples = 0;
unsigned long maxDelayUs = 0;
unsigned long totalDelayUs = 0;

// Function to measure time between samples
unsigned long measureSampleInterval() {
  static unsigned long previousTimeUs = 0;
  unsigned long currentTimeUs = micros();
  unsigned long intervalUs = 0;
  
  if (previousTimeUs != 0) {
    intervalUs = currentTimeUs - previousTimeUs;
  }
  
  previousTimeUs = currentTimeUs;
  return intervalUs;
}

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }
  
  Serial.println("\n=== BNO055 Sampling Rate and Delay Verification Test ===");
  
  // Initialize I2C
  Wire.begin();
  
  // Initialize BNO055 sensor
  if (!bno.begin()) {
    Serial.println("Failed to initialize BNO055 sensor! Check your connections.");
    while (1);
  }
  
  Serial.println("BNO055 sensor initialized successfully.");
  
  // Use external crystal for better accuracy
  bno.setExtCrystalUse(true);
  
  Serial.println("Test starting in 3 seconds...");
  delay(3000);
  
  // Reset timing variables
  startTimeMs = millis();
  totalSamples = 0;
  maxDelayUs = 0;
  totalDelayUs = 0;
  
  // Initialize the interval measurement
  measureSampleInterval();
  
  Serial.println("Test started. Running for 20 seconds...");
}

void loop() {
  // Get the current time
  unsigned long currentTimeMs = millis();
  
  // Check if test duration has elapsed
  if (currentTimeMs - startTimeMs >= TEST_DURATION_MS) {
    // Test completed, show results
    printResults();
    
    // Stop execution
    while (1) {
      delay(1000);
    }
  }
  
  // Read data from BNO055 sensor
  sensors_event_t event;
  bno.getEvent(&event);
  
  // Measure the time interval between samples
  unsigned long intervalUs = measureSampleInterval();
  
  // Update statistics
  totalSamples++;
  
  if (intervalUs > 0) {
    totalDelayUs += intervalUs;
    if (intervalUs > maxDelayUs) {
      maxDelayUs = intervalUs;
    }
  }
  
  // Optionally print raw data (commented out for performance)
  if (totalSamples % 1000 == 0) {
    Serial.print("Sample: ");
    Serial.print(totalSamples);
    Serial.print(", Delay: ");
    Serial.print(intervalUs);
    Serial.println(" us");
  }
}

void printResults() {
  // Calculate average sampling rate and delay
  float testDurationSec = (float)TEST_DURATION_MS / 1000.0;
  float samplingRate = (float)totalSamples / testDurationSec;
  float averageDelayUs = (totalSamples > 1) ? 
                         (float)totalDelayUs / (float)(totalSamples - 1) : 0;
  float averageDelayMs = averageDelayUs / 1000.0;
  float maxDelayMs = (float)maxDelayUs / 1000.0;
  
  Serial.println("\n=== TEST RESULTS ===");
  Serial.print("Total samples: ");
  Serial.println(totalSamples);
  Serial.print("Test duration: ");
  Serial.print(testDurationSec, 2);
  Serial.println(" seconds");
  
  Serial.print("Sampling rate: ");
  Serial.print(samplingRate, 2);
  Serial.println(" Hz");
  
  Serial.print("Average delay: ");
  Serial.print(averageDelayMs, 3);
  Serial.println(" ms");
  
  Serial.print("Maximum delay: ");
  Serial.print(maxDelayMs, 3);
  Serial.println(" ms");
  
  // Evaluate against requirements
  bool passSamplingRate = (samplingRate >= MIN_SAMPLE_FREQ);
  bool passDelay = (maxDelayMs < (MAX_DELAY_US / 1000.0));
  
  Serial.println("\n=== VERIFICATION RESULT ===");
  Serial.print("Sampling rate requirement (>= ");
  Serial.print(MIN_SAMPLE_FREQ);
  Serial.print(" Hz): ");
  Serial.println(passSamplingRate ? "PASS" : "FAIL");
  
  Serial.print("Delay requirement (< ");
  Serial.print(MAX_DELAY_US / 1000.0);
  Serial.print(" ms): ");
  Serial.println(passDelay ? "PASS" : "FAIL");
  
  Serial.println("\nOverall result: ");
  if (passSamplingRate && passDelay) {
    Serial.println("PASS - All requirements met");
  } else {
    Serial.println("FAIL - One or more requirements not met");
  }
  
  Serial.println("\nPlease run this test 3 times to ensure accurate results.");
}
