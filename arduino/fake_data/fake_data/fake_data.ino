#include <Arduino.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <WebSocketsClient.h>
#include <Hash.h>

ESP8266WiFiMulti WiFiMulti;
WebSocketsClient webSocket;

// Variables for generating synthetic data
unsigned long startTime;
const float targetFrequency = 5.0; // 5 Hz signal
const float amplitude = 9.8; // Similar to gravity acceleration in m/s²
const float noiseLevel = 0.5; // Small noise component

void webSocketEvent(WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.printf("[WSc] Disconnected!\n");
      break;
    
    case WStype_CONNECTED: {
        Serial.printf("[WSc] Connected to url %s\n", payload);
        webSocket.sendTXT("Connected");
      }
      break;
    
    case WStype_BIN:
      webSocket.sendBIN(payload, length);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for Serial port to be available
  }

  Serial.println("Synthetic 5Hz Data Generator");
  Serial.setDebugOutput(true);
  Serial.println();

  WiFiMulti.addAP("Router? I hardly know her!", "DromoreBoys");

  while(WiFiMulti.run() != WL_CONNECTED) {
    delay(100);
  }

  webSocket.begin("192.168.2.93", 8000, "/");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
  
  startTime = millis(); // Initialize time reference
}

void loop() {
  webSocket.loop();

  // Calculate time in seconds since start
  float currentTime = (millis() - startTime) / 1000.0;
  
  // Generate sine wave with 5Hz frequency
  // Use different phases for x, y, z to make it more interesting
  float x = amplitude * sin(2 * PI * targetFrequency * currentTime) + 
            random(-100, 100) / 100.0 * noiseLevel;
  
  float y = amplitude * sin(2 * PI * targetFrequency * currentTime + PI/3) + 
            random(-100, 100) / 100.0 * noiseLevel;
  
  float z = amplitude * sin(2 * PI * targetFrequency * currentTime + 2*PI/3) + 
            random(-100, 100) / 100.0 * noiseLevel;

  // Print values for debugging
  Serial.printf("Time: %.3f, Data: x=%.2f, y=%.2f, z=%.2f\n", 
                currentTime, x, y, z);

  // Pack the data in the same format as before
  const size_t packetSize = sizeof(float) * 3;
  uint8_t payload[packetSize];

  memcpy(payload, &x, sizeof(float));
  memcpy(payload + sizeof(float), &y, sizeof(float));
  memcpy(payload + 2*sizeof(float), &z, sizeof(float));

  // Send the data over websocket
  webSocket.sendBIN(payload, packetSize);

  // Keep the same delay as your original code
  delay(10);
}
