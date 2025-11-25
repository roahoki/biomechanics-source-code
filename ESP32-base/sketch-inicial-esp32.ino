#include <WiFi.h>
#include <MQTT.h>

// wifi credentials
const char ssid[] = "Depto 701";
const char pass[] = "Dperalta92";

// Shiftr.io credentials / MQTT en Touchdesigner
const char mqtt_client_id[] = "ESP32_Bioplant"; // device name
const char mqtt_user[]      = "biomechanics-home";     // username or key
const char mqtt_pass[]      = "//";      // secret password. Solicitar en shiftr.io

WiFiClient net;
MQTTClient client;

unsigned long lastMillis = 0;

void connect() {
  Serial.print("Conectando a WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("\n¡WiFi Conectado!");

  Serial.print("Conectando a Shiftr...");
  // Connect to biomechanics-home.cloud.shiftr.io
  while (!client.connect(mqtt_client_id, mqtt_user, mqtt_pass)) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("\n¡Conectado a Shiftr.io!");
}

void setup() {
  
  Serial.begin(115200);
  WiFi.setTxPower(WIFI_POWER_11dBm); // disminuir potencia de transmisión WiFi
  WiFi.mode(WIFI_STA); // Forzar modo Estación (Cliente) solamente
  WiFi.begin(ssid, pass);

  // Configuracion Shiftr
  client.begin("biomechanics-home.cloud.shiftr.io", net);
  
  connect();
}

void loop() {
  client.loop();
  delay(10); // Estabilidad

  if (!client.connected()) {
    connect();
  }

  // mensaje 2 segundos
  if (millis() - lastMillis > 2000) {
    lastMillis = millis();
    
    // Simucion sensor humedad (rand 0-100%)
    int fakeSensorData = random(0, 100);
    
    // cloud publish
    client.publish("/casa/planta1/humedad", String(fakeSensorData));
    
    Serial.print("Enviado: ");
    Serial.println(fakeSensorData);
  }
}