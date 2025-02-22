#include <ArduinoWebsockets.h>
using namespace websockets;

WebsocketsClient client;

void setup() {
  Serial.begin(115200);

  client.connect("ws://127.0.0.1:5000/socket.io/?EIO=4&transport=websocket");
}

void loop() {
  int fakeData = random(0, 100);
  client.send("data:" + String(fakeData));
  delay(1000);

  client.poll();
}
