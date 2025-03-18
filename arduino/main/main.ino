#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

#include <ESP8266WiFi.h>

#include <ESP8266WiFiMulti.h>

#include <WebSocketsClient.h>

#include <Hash.h>

ESP8266WiFiMulti WiFiMulti;
WebSocketsClient webSocket; 

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
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

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; 
  }

  Serial.println("BNO055 Sensor Test");

  if (!bno.begin()) {
    Serial.println("Failed to initialize the BNO055! Check your wiring or I2C address.");
    while (1);
  }
  delay(1000);
  

  bno.setExtCrystalUse(true);

  Serial.setDebugOutput(true);

  
	Serial.println();
	Serial.println();
	Serial.println();

  WiFiMulti.addAP("Router? I hardly know her!", "DromoreBoys");

  while(WiFiMulti.run() != WL_CONNECTED) {
    delay(100);
  }

  webSocket.begin("192.168.2.93", 8000, "/");

  webSocket.onEvent(webSocketEvent);

  webSocket.setReconnectInterval(5000);

}

void loop() {

  webSocket.loop();

  imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);

  
  imu::Vector<3> acceleration = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);

 
  float x = (float)acceleration.x();
  float y = (float)acceleration.y();
  float z = (float)acceleration.z();

  const size_t packetSize = sizeof(float) * 3;
  uint8_t payload[packetSize];

  memcpy(payload, &x, sizeof(float));
  memcpy(payload + sizeof(float), &y, sizeof(float));
  memcpy(payload + 2*sizeof(float), &z, sizeof(float));

  webSocket.sendBIN(payload, packetSize);

  delay(10);


}
