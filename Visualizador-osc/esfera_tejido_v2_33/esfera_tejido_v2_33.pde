// CONCEPTO 1.33: "Superficie Sólida Deformada" (v33)
//
// CAMBIOS:
// 1. (SUPERFICIE SÓLIDA): La función 'drawWireframeSphere' se reemplaza
//    por 'drawDeformedSphereSolid', que usa beginShape(TRIANGLE_STRIP)
//    y fill() para crear una superficie opaca.
// 2. (ILUMINACIÓN): Se añade 'lights()' para dar volumen y
//    curvatura a la superficie.
// 3. (NORMALES): Se calculan los vectores normales para cada vértice
//    de la esfera deformada para que la iluminación funcione correctamente.
// 4. (ESTILO): La esfera sólida usa 'noStroke()' y el color (hue)
//    es controlado por s_avgAlpha.

import oscP5.*;
import controlP5.*;

OscP5 oscP5;
ControlP5 cp5;

// Variables Globales OSC
float avgDelta=0, avgTheta=0, avgAlpha=0, avgBeta=0, avgGamma=0;
public float muDelta=1.2, muTheta=1.0, muAlpha=1.0, muBeta=0.8, muGamma=0.5;
float s_avgDelta=0, s_avgTheta=0, s_avgAlpha=0, s_avgBeta=0, s_avgGamma=0;
float accX=0, accY=0, accZ=0;

// Variables Visualización
// float t_noise = 0; // No se usa con ruido 3D
public float deformationFactor = 0.7;
ArrayList<Particle> particles;
public float maxParticleLife = 1.0;
public int numNewParticlesPerFrame = 50;
public float infAlphaAmp = 0.5;
public float infThetaScale = 0.5;
public float sensitivity = 2.25;

// Auto-Reset y Heartbeat
long nextResetTime; long randomInterval; boolean autoResetActive = false;
long lastDataTime; long dataTimeout = 1000; boolean isConnected = false;

void setup() {
  fullScreen(P3D, 2);

  oscP5 = new OscP5(this, 5002);
  cp5 = new ControlP5(this);
  println("Iniciado: Escuchando en el puerto 5002...");
  println("--- CONTROLES ---"); // ... (mensajes setup)
  println("  Sliders: Ajustan Baseline MU, Parámetros Visuales");
  println("  'r': Resetear Visualización");
  println("  '+/-': Ajustar Deformación General");
  println("  'a': Activar/Desactivar Auto-Reset");

  particles = new ArrayList<Particle>();

  // --- Sliders (Layout v31) ---
  int sliderX = 20; int sliderY = 20; int sliderW = 180; int sliderH = 20; int sliderSpacingY = 30; int currentY = sliderY;
  PFont sliderFont = createFont("Arial", 14); ControlFont cf = new ControlFont(sliderFont); cp5.setFont(cf);
  cp5.addSlider("muDelta").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.1, 3.0).setValue(muDelta).setLabel("Mu Delta"); currentY += sliderSpacingY;
  cp5.addSlider("muTheta").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.1, 2.5).setValue(muTheta).setLabel("Mu Theta"); currentY += sliderSpacingY;
  cp5.addSlider("muAlpha").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.1, 2.5).setValue(muAlpha).setLabel("Mu Alpha"); currentY += sliderSpacingY;
  cp5.addSlider("muBeta").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.1, 2.0).setValue(muBeta).setLabel("Mu Beta"); currentY += sliderSpacingY;
  cp5.addSlider("muGamma").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.1, 1.5).setValue(muGamma).setLabel("Mu Gamma"); currentY += sliderSpacingY * 1.5;
  cp5.addSlider("maxParticleLife").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.1, 2.0).setValue(maxParticleLife).setLabel("Vida Partícula (s)"); currentY += sliderSpacingY;
  cp5.addSlider("numNewParticlesPerFrame").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(10, 200).setValue(numNewParticlesPerFrame).setNumberOfTickMarks(191).setLabel("Nuevas Partículas/Frame"); currentY += sliderSpacingY;
  cp5.addSlider("deformationFactor").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.1, 2.0).setValue(deformationFactor).setLabel("Deformación General"); currentY += sliderSpacingY;
  cp5.addSlider("sensitivity").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.1, 4.0).setValue(sensitivity).setLabel("Sensibilidad Rotación"); currentY += sliderSpacingY * 1.5;
  cp5.addSlider("infAlphaAmp").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.0, 1.0).setValue(infAlphaAmp).setLabel("Inf. Alpha -> Amplitud"); currentY += sliderSpacingY;
  cp5.addSlider("infThetaScale").setPosition(sliderX, currentY).setSize(sliderW,sliderH).setRange(0.0, 1.0).setValue(infThetaScale).setLabel("Inf. Theta -> Escala Esp.");
  cp5.setAutoDraw(false);
  // --------------------------------------

  colorMode(HSB, 360, 100, 100, 100);
  background(0);
  // strokeWeight(2); // Se define localmente ahora

  randomInterval = (long)random(3000, 7000);
  nextResetTime = millis() + randomInterval;
  lastDataTime = millis();
}

void draw() {
  // Comprobación Heartbeat
  if (!isConnected ) { background(0); fill(0,0,100,60);textSize(24);textAlign(CENTER,CENTER);text("ESPERANDO CONEXIÓN...",width/2,height/2);nextResetTime=millis()+randomInterval;return;}
  if (millis() - lastDataTime > dataTimeout) { println("!!! CONEXIÓN PERDIDA !!!"); isConnected = false; return; }

  background(0); // Borrado total

  // Validar valores OSC
  float safe_sAvgAlpha = validateFloat(s_avgAlpha, 0.0f);
  float safe_sAvgBeta = validateFloat(s_avgBeta, 0.0f);
  float safe_sAvgTheta = validateFloat(s_avgTheta, 0.0f);
  float safe_sAvgGamma = validateFloat(s_avgGamma, 0.0f);
  float safe_avgAlpha = validateFloat(avgAlpha, 1.0f);
  float safe_avgDelta = validateFloat(avgDelta, 0.0f);
  float safe_accX = validateFloat(accX, 0.0f);
  float safe_accY = validateFloat(accY, 0.0f);
  float safe_accZ = validateFloat(accZ, 0.0f);

  // Calcular parámetros Ruido 3D
  float noiseBaseScale = 1.0;
  float thetaScaleFactor = map(safe_sAvgTheta, -2.0, 2.0, 0.5, 1.5);
  float currentNoiseScale = noiseBaseScale * lerp(1.0, thetaScaleFactor, infThetaScale);
  float safeNoiseScale = max(0.01, currentNoiseScale);

  float alphaAmpFactor = map(safe_sAvgAlpha, -2.0, 2.0, 0.5, 1.5);
  float currentAmplitude = deformationFactor * lerp(1.0, alphaAmpFactor, infAlphaAmp);

  float orden = map(safe_avgAlpha, 0, 3.0, 8, 2);
  noiseDetail(max(1, int(orden)));

  // --- Mundo 3D ---
  pushMatrix();
  translate(width/2, height/2);
  float rotX = map(safe_accY, -1.0, 1.0, PI * sensitivity, -PI * sensitivity); // Pitch
  float rotY = map(safe_accZ, -1.0, 1.0, -PI * sensitivity, PI * sensitivity); // Yaw
  float rotZ = map(safe_accX, -1.0, 1.0, -PI * sensitivity, PI * sensitivity); // Roll
  rotateX(rotX); rotateY(rotY); rotateZ(rotZ);

  // --- CAMBIO 2: Añadir Iluminación ---
  lights();
  // -----------------------------------

  // --- DIBUJO DE LA SUPERFICIE SÓLIDA ---
  float radioPerfecto = map(muAlpha, 0.1, 2.5, height * 0.25, height * 0.40);
  int sphereSegments = 24;
  
  // Calcular color base para la esfera sólida
  float alphaColorFactor = constrain(map(safe_sAvgAlpha, -2.0, 2.0, 0.0, 1.0), 0.0, 1.0);
  float sphereHue = lerp(120, 240, alphaColorFactor); // Verde-Azul
  
  // --- CAMBIO 1 y 4: Estilo Sólido ---
  fill(sphereHue, 50, 80, 100); // HSB: Color dinámico, Sat 50, Bri 80, Op 100
  noStroke(); // Sin malla de alambre
  // ---------------------------------

  drawDeformedSphereSolid(radioPerfecto, sphereSegments, safeNoiseScale, currentAmplitude);
  // -------------------------------------

  noLights(); // Apagar luces para que no afecten a las partículas

  // --- Crear Nuevas Partículas ---
  for (int i = 0; i < numNewParticlesPerFrame; i++) {
    float u = random(TWO_PI); float v = random(-1.0, 1.0);
    float angleTheta = acos(v); float anglePhi = u;

    float xBase = radioPerfecto * sin(angleTheta) * cos(anglePhi);
    float yBase = radioPerfecto * sin(angleTheta) * sin(anglePhi);
    float zBase = radioPerfecto * cos(angleTheta);

    float noiseInputX = validateFloat(xBase * safeNoiseScale, 0.0f);
    float noiseInputY = validateFloat(yBase * safeNoiseScale, 0.0f);
    float noiseInputZ = validateFloat(zBase * safeNoiseScale, 0.0f);

    float n = noise(noiseInputX, noiseInputY, noiseInputZ); // Ruido 3D
    float safeN = validateFloat(n, 0.5f);

    float deformacion = map(safeN, 0, 1, -radioPerfecto * currentAmplitude, radioPerfecto * currentAmplitude);
    float radioDinamico = radioPerfecto + deformacion; // Radio para la partícula

    float xPos = radioDinamico * sin(angleTheta) * cos(anglePhi);
    float yPos = radioDinamico * sin(angleTheta) * sin(anglePhi);
    float zPos = radioDinamico * cos(angleTheta);

    if (isValidPosition(xPos, yPos, zPos)) {
      float p_alphaColorFactor = constrain(map(safe_sAvgAlpha, -2.0, 2.0, 0.0, 1.0), 0.0, 1.0);
      float p_hueBase = lerp(120, 240, p_alphaColorFactor);
      float p_saturation = constrain(map(safe_sAvgBeta, -2.0, 2.0, 20, 100), 0, 100);
      float p_brightness = constrain(map(safe_sAvgTheta, -2.0, 2.0, 40, 100), 0, 100);
      float p_gammaRedFactor = constrain(map(safe_sAvgGamma, -1.0, 2.0, 0.0, 1.0), 0.0, 1.0);
      float p_particleSize = map(safe_avgDelta, 0, 3.0, 1, 5);
      p_particleSize = max(1.0, p_particleSize);
      float p_lifeFrames = max(1.0, maxParticleLife * frameRate);

      if (isValidColor(p_hueBase, p_saturation, p_brightness, 100)){
         particles.add(new Particle(xPos, yPos, zPos, p_hueBase, p_saturation, p_brightness, p_gammaRedFactor, p_particleSize, p_lifeFrames));
      }
    }
  }

  // --- Dibujar y Envejecer Partículas ---
  // (Sin cambios)
  for (int i = particles.size() - 1; i >= 0; i--) {
    Particle p = particles.get(i);
    if (p == null || p.pos == null) { particles.remove(i); continue; }
    p.update();
    if (p.isDead()) { particles.remove(i); }
    else { p.display(); }
  }

  popMatrix(); // --- Fin mundo 3D ---

  // --- DIBUJAR HUD y SLIDERS ---
  hint(DISABLE_DEPTH_TEST);
  fill(0, 0, 100, 80); textSize(16); textAlign(RIGHT, BOTTOM);
  // ... (código HUD igual que v31) ...
  String fsDelta = String.format("%+.2f", s_avgDelta); String fsTheta = String.format("%+.2f", s_avgTheta);
  String fsAlpha = String.format("%+.2f", s_avgAlpha); String fsBeta = String.format("%+.2f", s_avgBeta);
  String fsGamma = String.format("%+.2f", s_avgGamma); String fmuDelta = String.format("%.2f", muDelta);
  String fmuTheta = String.format("%.2f", muTheta); String fmuAlpha = String.format("%.2f", muAlpha);
  String fmuBeta = String.format("%.2f", muBeta); String fmuGamma = String.format("%.2f", muGamma);
  String fAccX = String.format("%.2f", accX); String fAccY = String.format("%.2f", accY);
  String fAccZ = String.format("%.2f", accZ); String fDeform = String.format("%.1f", deformationFactor * 100);
  int x_hud = width - 20; int y_hud_base = height - 20; int hudSpacing = 25;
  text("Deform: "+fDeform + "%", x_hud, y_hud_base); y_hud_base -= hudSpacing * 1.5;
  text("sDELTA: "+fsDelta, x_hud, y_hud_base); y_hud_base -= hudSpacing; text("sTHETA: "+fsTheta, x_hud, y_hud_base); y_hud_base -= hudSpacing;
  text("sALPHA: "+fsAlpha, x_hud, y_hud_base); y_hud_base -= hudSpacing; text("sBETA: "+fsBeta, x_hud, y_hud_base); y_hud_base -= hudSpacing;
  text("sGAMMA: "+fsGamma, x_hud, y_hud_base); y_hud_base -= hudSpacing * 1.5;
  text("AccX: "+fAccX, x_hud, y_hud_base); y_hud_base -= hudSpacing; text("AccY: "+fAccY, x_hud, y_hud_base); y_hud_base -= hudSpacing;
  text("AccZ: "+fAccZ, x_hud, y_hud_base); y_hud_base -= hudSpacing * 1.5;
  text("muDEL: "+fmuDelta, x_hud, y_hud_base); y_hud_base -= hudSpacing; text("muTHE: "+fmuTheta, x_hud, y_hud_base); y_hud_base -= hudSpacing;
  text("muALP: "+fmuAlpha, x_hud, y_hud_base); y_hud_base -= hudSpacing; text("muBET: "+fmuBeta, x_hud, y_hud_base); y_hud_base -= hudSpacing;
  text("muGAM: "+fmuGamma, x_hud, y_hud_base);

  cp5.draw(); // Dibuja Sliders
  hint(ENABLE_DEPTH_TEST);

  // Auto-Reset
  if (autoResetActive && millis() > nextResetTime) {
    resetVisuals();
    randomInterval = (long)random(3000, 7000); nextResetTime = millis() + randomInterval;
  }
}

// --- oscEvent (sin cambios) ---
void oscEvent(OscMessage theOscMessage) { /* ... */ lastDataTime = millis(); String addr = theOscMessage.addrPattern(); if (!isConnected && addr.startsWith("/py/")) {println(">>> CONEXIÓN ESTABLECIDA <<<"); isConnected = true;} try { if (addr.equals("/py/bands_env")) { if(theOscMessage.arguments().length==5){avgDelta=validateFloat(theOscMessage.get(0).floatValue(), avgDelta); avgTheta=validateFloat(theOscMessage.get(1).floatValue(), avgTheta); avgAlpha=validateFloat(theOscMessage.get(2).floatValue(), avgAlpha); avgBeta=validateFloat(theOscMessage.get(3).floatValue(), avgBeta); avgGamma=validateFloat(theOscMessage.get(4).floatValue(), avgGamma);}} else if (addr.equals("/py/bands_signed_env")) { if(theOscMessage.arguments().length==5){s_avgDelta = validateFloat(theOscMessage.get(0).floatValue(), s_avgDelta); s_avgTheta = validateFloat(theOscMessage.get(1).floatValue(), s_avgTheta); s_avgAlpha = validateFloat(theOscMessage.get(2).floatValue(), s_avgAlpha); s_avgBeta  = validateFloat(theOscMessage.get(3).floatValue(), s_avgBeta); s_avgGamma = validateFloat(theOscMessage.get(4).floatValue(), s_avgGamma);}} else if (addr.equals("/py/acc")) { if(theOscMessage.arguments().length==3){accX=validateFloat(theOscMessage.get(0).floatValue(), accX); accY=validateFloat(theOscMessage.get(1).floatValue(), accZ); accZ=validateFloat(theOscMessage.get(2).floatValue(), accZ);}} else if (addr.startsWith("/py/")) { } else if (addr.startsWith("/desdemuse/")) { } else { }} catch (Exception e) { println("!!! ERROR procesando OSC: " + addr + " - " + e); } }

// --- Funciones de Validación (sin cambios) ---
float validateFloat(float value, float defaultValue) { return (Float.isNaN(value) || Float.isInfinite(value)) ? defaultValue : value; }
boolean isValidPosition(float x, float y, float z) { return !(Float.isNaN(x) || Float.isNaN(y) || Float.isNaN(z) || Float.isInfinite(x) || Float.isInfinite(y) || Float.isInfinite(z)); }
boolean isValidColor(float h, float s, float b, float a) { return !(Float.isNaN(h) || Float.isNaN(s) || Float.isNaN(b) || Float.isNaN(a) || Float.isInfinite(h) || Float.isInfinite(s) || Float.isInfinite(b) || Float.isInfinite(a)); }

// Función resetVisuals (sin cambios)
void resetVisuals() { background(0); particles.clear(); println("--- VISUALIZACIÓN RESETEADA ---"); }

// Función keyPressed (sin cambios)
void keyPressed() {
  if (key == 'r' || key == 'R') { resetVisuals(); }
  if (key == '+') { deformationFactor=constrain(deformationFactor+0.1,0.1,2.0); println("Deform:"+String.format("%.1f",deformationFactor)); cp5.getController("deformationFactor").setValue(deformationFactor);}
  if (key == '-') { deformationFactor=constrain(deformationFactor-0.1,0.1,2.0); println("Deform:"+String.format("%.1f",deformationFactor)); cp5.getController("deformationFactor").setValue(deformationFactor);}
  if (key == 'a' || key == 'A') {
    autoResetActive = !autoResetActive; println("Auto-Reset " + (autoResetActive?"ACTIVADO":"DESACTIVADO"));
    if(autoResetActive){randomInterval = (long)random(3000, 7000); nextResetTime = millis() + randomInterval;}
  }
}

// Función vacía para ControlP5
void controlEvent(ControlEvent theEvent) {}

// --- CLASE Particle (sin cambios) ---
class Particle {
  PVector pos; float h_base, s, b, gammaFactor, size; float maxLife; float age;
  Particle(float x, float y, float z, float hueBase, float sat, float br, float gFactor, float pSize, float lifeInFrames) {
    pos = new PVector(x, y, z); h_base = hueBase; s = sat; b = br; gammaFactor = gFactor; size = pSize; maxLife = max(1.0, lifeInFrames); age = 0;
  }
  void update() { age++; }
  boolean isDead() { return age >= maxLife; }
  void display() {
    if (pos == null) return;
    float alpha = map(age, 0, maxLife, 100, 0);
    color baseColor = color(h_base, s, b); color redColor = color(0, 100, 100); color finalColor = lerpColor(baseColor, redColor, gammaFactor);
    float finalH = hue(finalColor); float finalS = saturation(finalColor); float finalB = brightness(finalColor);
    if (isValidColor(finalH, finalS, finalB, alpha) && alpha > 0) {
        strokeWeight(size); stroke(finalColor, alpha);
        if (isValidPosition(pos.x, pos.y, pos.z)) { point(pos.x, pos.y, pos.z); }
    }
  }
}

// --- CAMBIO 1: NUEVA FUNCIÓN drawDeformedSphereSolid ---
// (Reemplaza a drawWireframeSphere)
void drawDeformedSphereSolid(float radius, int segments, float noiseScale, float noiseAmplitude) {
  // Almacenar vértices y normales
  PVector[][] globe = new PVector[segments + 1][segments + 1];
  PVector[][] globeNormals = new PVector[segments + 1][segments + 1];

  for (int i = 0; i <= segments; i++) {
    float lat = map(i, 0, segments, 0, PI); // Latitud (theta)

    for (int j = 0; j <= segments; j++) {
      float lon = map(j, 0, segments, 0, TWO_PI); // Longitud (phi)

      // Calcular posición base
      float xBase = radius * sin(lat) * cos(lon);
      float yBase = radius * sin(lat) * sin(lon);
      float zBase = radius * cos(lat);

      // Calcular ruido 3D
      float noiseInputX = validateFloat(xBase * noiseScale, 0.0f);
      float noiseInputY = validateFloat(yBase * noiseScale, 0.0f);
      float noiseInputZ = validateFloat(zBase * noiseScale, 0.0f);
      float n = noise(noiseInputX, noiseInputY, noiseInputZ);
      float safeN = validateFloat(n, 0.5f);

      // Calcular deformación
      float deformacion = map(safeN, 0, 1, -radius * noiseAmplitude, radius * noiseAmplitude);
      float radioDinamico = max(0.1, radius + deformacion); // Asegurar radio positivo

      // Calcular posición deformada
      float xDef = radioDinamico * sin(lat) * cos(lon);
      float yDef = radioDinamico * sin(lat) * sin(lon);
      float zDef = radioDinamico * cos(lat);
      
      // Validar posición
      if (isValidPosition(xDef, yDef, zDef)) {
          globe[i][j] = new PVector(xDef, yDef, zDef);
      } else {
          globe[i][j] = new PVector(xBase, yBase, zBase); // Fallback a pos base
      }
      
      // --- CAMBIO 3: Calcular Normal ---
      // La normal es el vector desde el centro (0,0,0) al punto de la
      // superficie, normalizado (longitud 1).
      PVector normal = globe[i][j].copy();
      normal.normalize();
      globeNormals[i][j] = normal;
      // -------------------------------
    }
  }

  // Dibujar la superficie usando TRIANGLE_STRIP
  for (int i = 0; i < segments; i++) {
    beginShape(TRIANGLE_STRIP);
    for (int j = 0; j <= segments; j++) {
      PVector p1 = globe[i][j];
      PVector n1 = globeNormals[i][j];
      PVector p2 = globe[i+1][j];
      PVector n2 = globeNormals[i+1][j];
      
      // Vértice 1 (de la tira actual)
      normal(n1.x, n1.y, n1.z); // Aplicar normal para iluminación
      vertex(p1.x, p1.y, p1.z);
      
      // Vértice 2 (de la siguiente tira)
      normal(n2.x, n2.y, n2.z);
      vertex(p2.x, p2.y, p2.z);
    }
    endShape();
  }
}
// ----------------------------------------------------
