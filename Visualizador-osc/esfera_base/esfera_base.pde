// ESFERA BASE - Punto de partida limpio
// Visualización simple con OSC para datos EEG

import oscP5.*;
import controlP5.*;

OscP5 oscP5;
ControlP5 cp5;

// Variables OSC - Ondas cerebrales
float avgDelta = 0, avgTheta = 0, avgAlpha = 0, avgBeta = 0, avgGamma = 0;
float s_avgDelta = 0, s_avgTheta = 0, s_avgAlpha = 0, s_avgBeta = 0, s_avgGamma = 0;

// Acelerómetro
float accX = 0, accY = 0, accZ = 0;

// Conexión
long lastDataTime;
long dataTimeout = 2000;
boolean isConnected = false;

// Visualización
float sphereRadius = 200;
int sphereSegments = 64;

void setup() {
  size(1400, 900, P3D);
  
  // Iniciar OSC en puerto 5002
  oscP5 = new OscP5(this, 5002);
  cp5 = new ControlP5(this);
  
  colorMode(HSB, 360, 100, 100, 100);
  
  lastDataTime = millis();
  
  println("=== ESFERA BASE INICIADA ===");
  println("Escuchando OSC en puerto 5002");
  println("Esperando conexión...");
}

void draw() {
  background(0);
  
  // Verificar conexión
  if (!isConnected) {
    fill(0, 0, 100);
    textAlign(CENTER, CENTER);
    textSize(24);
    text("ESPERANDO CONEXIÓN...", width/2, height/2);
    return;
  }
  
  if (millis() - lastDataTime > dataTimeout) {
    println("CONEXIÓN PERDIDA");
    isConnected = false;
    return;
  }
  
  // Mundo 3D
  pushMatrix();
  translate(width/2, height/2);
  
  // Rotación básica con acelerómetro
  rotateX(accY);
  rotateY(accZ);
  rotateZ(accX);
  
  // Iluminación
  lights();
  
  // Esfera básica
  fill(180, 50, 80); // Azul celeste
  noStroke();
  sphere(sphereRadius);
  
  popMatrix();
  
  // HUD simple
  drawHUD();
}

void drawHUD() {
  fill(0, 0, 100);
  textAlign(LEFT, TOP);
  textSize(14);
  
  int x = 20;
  int y = 20;
  int spacing = 25;
  
  text("=== ONDAS CEREBRALES ===", x, y); y += spacing * 1.5;
  text("Delta: " + nf(avgDelta, 1, 2), x, y); y += spacing;
  text("Theta: " + nf(avgTheta, 1, 2), x, y); y += spacing;
  text("Alpha: " + nf(avgAlpha, 1, 2), x, y); y += spacing;
  text("Beta: " + nf(avgBeta, 1, 2), x, y); y += spacing;
  text("Gamma: " + nf(avgGamma, 1, 2), x, y); y += spacing * 1.5;
  
  text("=== ACELERÓMETRO ===", x, y); y += spacing * 1.5;
  text("X: " + nf(accX, 1, 2), x, y); y += spacing;
  text("Y: " + nf(accY, 1, 2), x, y); y += spacing;
  text("Z: " + nf(accZ, 1, 2), x, y);
}

void oscEvent(OscMessage msg) {
  lastDataTime = millis();
  String addr = msg.addrPattern();
  
  // Detectar primera conexión
  if (!isConnected && addr.startsWith("/py/")) {
    println(">>> CONEXIÓN ESTABLECIDA <<<");
    isConnected = true;
  }
  
  try {
    // Ondas cerebrales (valores absolutos)
    if (addr.equals("/py/bands_env")) {
      if (msg.arguments().length == 5) {
        avgDelta = msg.get(0).floatValue();
        avgTheta = msg.get(1).floatValue();
        avgAlpha = msg.get(2).floatValue();
        avgBeta = msg.get(3).floatValue();
        avgGamma = msg.get(4).floatValue();
      }
    }
    // Ondas cerebrales (valores relativos/firmados)
    else if (addr.equals("/py/bands_signed_env")) {
      if (msg.arguments().length == 5) {
        s_avgDelta = msg.get(0).floatValue();
        s_avgTheta = msg.get(1).floatValue();
        s_avgAlpha = msg.get(2).floatValue();
        s_avgBeta = msg.get(3).floatValue();
        s_avgGamma = msg.get(4).floatValue();
      }
    }
    // Acelerómetro
    else if (addr.equals("/py/acc")) {
      if (msg.arguments().length == 3) {
        accX = msg.get(0).floatValue();
        accY = msg.get(1).floatValue();
        accZ = msg.get(2).floatValue();
      }
    }
  } catch (Exception e) {
    println("Error procesando OSC: " + addr);
  }
}

void keyPressed() {
  if (key == 'r' || key == 'R') {
    println("Reset visual");
    background(0);
  }
}
