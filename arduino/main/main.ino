#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

// Create a BNO055 sensor object (ID = 55, default I2C address 0x28)
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28, &Wire);

// Wi‑Fi credentials
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

// Create an instance of the ESP8266 web server on port 80
ESP8266WebServer server(80);

// This function is called whenever a client requests the root URL
void handleRoot() {
  // Read sensor events from the sensor
  sensors_event_t event;
  bno.getEvent(&event);

  // Build an HTML page to display sensor data.
  // A meta refresh tag is included to refresh the page every 1 second.
  String output = "<!DOCTYPE html><html><head><meta http-equiv='refresh' "
                  "content='1'>";
  output += "<title>BNO055 Sensor Data</title></head><body>";
  output += "<h1>BNO055 Sensor Data</h1>";

  // Accelerometer data
  output += "<p><strong>Accelerometer:</strong><br />";
  output += "X: " + String(event.acceleration.x, 2) + " m/s<sup>2</sup><br />";
  output += "Y: " + String(event.acceleration.y, 2) + " m/s<sup>2</sup><br />";
  output += "Z: " + String(event.acceleration.z, 2) + " m/s<sup>2</sup></p>";

  // Gyroscope data
  output += "<p><strong>Gyroscope:</strong><br />";
  output += "X: " + String(event.gyro.x, 2) + " °/s<br />";
  output += "Y: " + String(event.gyro.y, 2) + " °/s<br />";
  output += "Z: " + String(event.gyro.z, 2) + " °/s</p>";

  // Magnetometer data
  output += "<p><strong>Magnetometer:</strong><br />";
  output += "X: " + String(event.magnetic.x, 2) + " μT<br />";
  output += "Y: " + String(event.magnetic.y, 2) + " μT<br />";
  output += "Z: " + String(event.magnetic.z, 2) + " μT</p>";

  // Temperature reading from the sensor
  output += "<p><strong>Temperature:</strong> " + String(bno.getTemp()) +
            " °C</p>";
  output += "</body></html>";

  // Send the HTML page to the client
  server.send(200, "text/html", output);
}

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("Initializing BNO055 sensor...");

  // Initialize the BNO055 sensor
  if (!bno.begin()) {
    Serial.println("No BNO055 detected. Please check wiring!");
    while (1) {
      delay(100);
    }
  }

  // Optionally use an external crystal for better accuracy
  bno.setExtCrystalUse(true);

  // Connect to Wi‑Fi network
  Serial.print("Connecting to Wi‑Fi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  // Set up the root URL routing
  server.on("/", handleRoot);

  // Start the HTTP server
  server.begin();
  Serial.println("HTTP server started.");
}

void loop() {
  // Handle incoming client requests
  server.handleClient();
}
