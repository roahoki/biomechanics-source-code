#include <WiFi.h>
#include <MQTT.h>
#include "DHT.h"

// wifi credentials
const char ssid[] = "@&*#!^*&";
const char pass[] = "!@OIU#O!@U#";

// Shiftr.io credentials / MQTT en Touchdesigner
const char mqtt_client_id[] = "123)(*!@)#(*";
const char mqtt_user[]      = "!#!@I#!@*#-!@()#*!";
const char mqtt_pass[]      = "*#^&!*!"; // Tus credenciales de Shiftr. Privado

// Configuración del Sensor
#define DHTPIN 4     // El cable amarillo va al Pin D4
#define DHTTYPE DHT21 // El AM2301A funciona como un DHT21 (AM2301)

DHT dht(DHTPIN, DHTTYPE);
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
  while (!client.connect(mqtt_client_id, mqtt_user, mqtt_pass)) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("\n¡Conectado a Shiftr.io!");
}

void setup() {
  Serial.begin(115200);
  
  // Estabilidad WiFi
  WiFi.mode(WIFI_STA);
  WiFi.setTxPower(WIFI_POWER_11dBm);

  // Iniciar Sensor
  dht.begin();

  WiFi.begin(ssid, pass);
  client.begin("biomechanics-home.cloud.shiftr.io", net);
  
  connect();
}

void loop() {
  client.loop();
  delay(10);

  if (!client.connected()) {
    connect();
  }

  // Enviar datos cada 2 segundos
  if (millis() - lastMillis > 2000) {
    lastMillis = millis();

    // LEER EL SENSOR REAL
    float humedad = dht.readHumidity();
    float temperatura = dht.readTemperature();

    // Chequeo de errores
    if (isnan(humedad) || isnan(temperatura)) {
      Serial.println("¡Error leyendo el sensor!");
      return;
    }

    // PUBLICAR A SHIFTR
    client.publish("/casa/planta1/humedad", String(humedad));
    client.publish("/casa/planta1/temperatura", String(temperatura));
    
    Serial.print("Humedad: ");
    Serial.print(humedad);
    Serial.print("%  |  Temp: ");
    Serial.println(temperatura);
  }
}
