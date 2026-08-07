#include <Arduino.h>
#include <WiFi.h>

const char* ssid = "TELUS0086";
const char* pw = "R27c2LvncKT3";

WiFiServer server(80);

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, 16, 17);

  WiFi.begin(ssid, pw);
  Serial.print("Connecting to WiFi");
  while(WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.println("Connecting...");
  }
  Serial.println();
  Serial.println("Connected!");
  Serial.print(" IP address: ");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if(client){
    Serial.println("Client connected");
    while(client.connected()){
      if(client.available()){
        String cmd = client.readStringUntil('\n');
        cmd.trim();
        Serial2.println(cmd);
        Serial.println("Relayed: " + cmd);
      }
    }
    client.stop();
    Serial.println("Client disconnected");
  }
}

