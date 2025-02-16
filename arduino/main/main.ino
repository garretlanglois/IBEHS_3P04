#include <ArduinoWebsockets.h>
using namespace websockets;

WebsocketsClient client;

void setup() {
  // Initialize serial and WiFi here
  Serial.begin(115200);
  // Connect to WiFi...
  
  // Connect to the Flask WebSocket server
  client.connect("ws://192.168.x.x:5000/socket.io/?EIO=4&transport=websocket");
}

void loop() {
  // Send fake sensor data periodically
  int fakeData = random(0, 100);
  client.send("data:" + String(fakeData));
  delay(1000);
  
  // Handle incoming messages if necessary
  client.poll();
}
