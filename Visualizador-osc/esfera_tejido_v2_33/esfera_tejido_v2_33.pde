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
public float deformationFactor = 0.45; // Reducido para superficie más suave
ArrayList<Particle> particles;
public float maxParticleLife = 1.0;
public int numNewParticlesPerFrame = 50;
public float infAlphaAmp = 0.5;
public float infThetaScale = 0.5;
public float sensitivity = 2.25;

// Auto-Reset y Heartbeat
long nextResetTime; long randomInterval; boolean autoResetActive = false;
long lastDataTime; long dataTimeout = 2000; boolean isConnected = false;

// Estética y exportación para póster vertical
boolean posterMode = true; // Activa formato póster vertical
boolean saveFrames = false; // Activar para exportar PNG
String framePath = "frames/frame-####.png";
int posterWidth = 3600;  // Relación 2:3
int posterHeight = 5400;
float bgHue = 210; float bgSat = 10; float bgBrightTop = 16; float bgBrightBottom = 6; // Más contraste
float vignetteStrength = 0.0; // 0-1 (0 para sin viñeta)
int sphereSegments = 128; // Más detalle para impresión (aumentado para suavidad)
float solidAlpha = 100; float wireAlpha = 70; float wireStroke = 0.9;
float cameraOrbitAmp = 0.08; // Giro leve de cámara
boolean showUI = true; // Mostrar sliders y HUD incluso en modo póster
boolean showWireframe = true; // Mostrar/ocultar líneas blancas (toggle con 'w')

// Tipografía
String jetFontPath = "/Users/tomas/Downloads/JetBrainsMono-2.304/fonts/ttf/JetBrainsMono-Regular.ttf";
PFont uiFont; PFont hudFont;
int textSizeUI = 12; // Tamaño uniforme para UI y HUD

// Límite de partículas para evitar memory leak
public int maxParticlesAllowed = 5000;

void settings() {
  if (posterMode) {
    float aspect = posterWidth / (float)posterHeight;
    int hFit = displayHeight; // ocupar el alto de la pantalla
    int wFit = (int)(hFit * aspect); // respetar relación 2:3
    size(wFit, hFit, P3D);
  } else {
    size(1400, 900, P3D); // Vista cómoda en pantalla estándar
  }
}

void setup() {

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
  uiFont = createFont(jetFontPath, 8);
  hudFont = createFont(jetFontPath, 8);

  int sliderX = 20; int sliderY = 20; int sliderW = 220; int sliderH = 18; int sliderSpacingY = 28; int currentY = sliderY;
  ControlFont cf = new ControlFont(uiFont); cp5.setFont(cf);
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

  if (posterMode) {
    randomSeed(1); noiseSeed(1); // Consistencia entre renders
  }
}

void draw() {
  // Comprobación Heartbeat
  if (!isConnected ) { background(0); textFont(hudFont); fill(0,0,100,60);textSize(textSizeUI);textAlign(CENTER,CENTER);text("ESPERANDO CONEXIÓN...",width/2,height/2);nextResetTime=millis()+randomInterval;return;}
  if (millis() - lastDataTime > dataTimeout) { println("!!! CONEXIÓN PERDIDA !!!"); isConnected = false; return; }

  background(bgHue, bgSat, bgBrightTop); // Limpiar frame anterior

  // Validar valores OSC
  float safe_sAvgAlpha = validateFloat(s_avgAlpha, 0.0f);
  float safe_sAvgBeta = validateFloat(s_avgBeta, 0.0f);
  float safe_sAvgTheta = validateFloat(s_avgTheta, 0.0f);
  float safe_sAvgGamma = validateFloat(s_avgGamma, 0.0f);
  float safe_avgAlpha = validateFloat(avgAlpha, 1.0f);
  float safe_avgDelta = validateFloat(avgDelta, 0.0f);
  float safe_avgBeta = validateFloat(avgBeta, 0.0f); // Para offset de radio de partículas
  float safe_accX = validateFloat(accX, 0.0f);
  float safe_accY = validateFloat(accY, 0.0f);
  float safe_accZ = validateFloat(accZ, 0.0f);

  // Calcular parámetros Ruido 3D
  float noiseBaseScale = 1.0;
  float thetaScaleFactor = map(safe_sAvgTheta, -2.0, 2.0, 0.5, 1.5);
  float currentNoiseScale = noiseBaseScale * lerp(1.0, thetaScaleFactor, infThetaScale);
  float safeNoiseScale = constrain(currentNoiseScale, 0.01, 0.5); // Limitar para deformación controlada

  float alphaAmpFactor = map(safe_sAvgAlpha, -2.0, 2.0, 0.5, 1.5);
  float currentAmplitude = deformationFactor * lerp(1.0, alphaAmpFactor, infAlphaAmp);

  // Fijar detalle de ruido para evitar parpadeos y suavizar deformación
  noiseDetail(7, 0.70);

  // --- Mundo 3D ---
  pushMatrix();
  translate(width/2, height/2);
  float rotX = map(safe_accY, -1.0, 1.0, PI * sensitivity, -PI * sensitivity); // Pitch
  float rotY = map(safe_accZ, -1.0, 1.0, -PI * sensitivity, PI * sensitivity); // Yaw
  float rotZ = map(safe_accX, -1.0, 1.0, -PI * sensitivity, PI * sensitivity); // Roll
  float orbit = sin(frameCount * 0.0025) * cameraOrbitAmp;
  rotateY(orbit);
  rotateX(rotX); rotateY(rotY); rotateZ(rotZ);

  // --- CAMBIO 2: Añadir Iluminación ---
  lights();
  // -----------------------------------

  // --- DIBUJO DE LA SUPERFICIE SÓLIDA ---
  float baseDim = min(width, height);
  float radioPerfecto = map(muAlpha, 0.1, 2.5, baseDim * 0.25, baseDim * 0.45);
  
  // Calcular color base para la esfera sólida
  float alphaColorFactor = constrain(map(safe_sAvgAlpha, -2.0, 2.0, 0.0, 1.0), 0.0, 1.0);
  float sphereHue = lerp(120, 240, alphaColorFactor); // Verde-Azul
  
  // --- CAMBIO 1 y 4: Estilo Sólido ---
  fill(sphereHue, 50, 80, solidAlpha); // Mantener saturación/brillo originales
  noStroke();
  drawDeformedSphereSolid(radioPerfecto, sphereSegments, safeNoiseScale, currentAmplitude);

  // Capa wireframe blanca (opcional)
  if (showWireframe) {
    stroke(0, 0, 100, wireAlpha);
    strokeWeight(wireStroke);
    noFill();
    drawDeformedSphereWire(radioPerfecto, sphereSegments, safeNoiseScale, currentAmplitude);
  }

  noLights(); // Apagar luces para que no afecten a las partículas

  // --- Crear Nuevas Partículas ---
  // Limitar el total de partículas para evitar memory leak
  if (particles.size() < maxParticlesAllowed) {
    for (int i = 0; i < numNewParticlesPerFrame; i++) {
      if (particles.size() >= maxParticlesAllowed) break; // Detener si se alcanza el límite
      
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
      
      // Offset variable basado en avgBeta: partículas pueden nacer más lejos/cerca de superficie
      float betaOffset = map(safe_avgBeta, 0, 3.0, -radioPerfecto * 0.1, radioPerfecto * 0.15);
      radioDinamico += betaOffset;

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
  }

  // --- Dibujar y Envejecer Partículas ---
  for (int i = particles.size() - 1; i >= 0; i--) {
    Particle p = particles.get(i);
    if (p == null || p.pos == null) { particles.remove(i); continue; }
    p.update();
    if (p.isDead()) { particles.remove(i); }
    else { p.display(); }
  }

  popMatrix(); // --- Fin mundo 3D ---

  // --- DIBUJAR HUD y SLIDERS ---
  if (showUI) {
    hint(DISABLE_DEPTH_TEST);
    textFont(hudFont);
    fill(0, 0, 100, 85); textSize(textSizeUI); textAlign(RIGHT, BOTTOM);
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
  }

  applyVignette();
  if (saveFrames) { saveFrame(framePath); }

  // Auto-Reset
  if (autoResetActive && millis() > nextResetTime) {
    resetVisuals();
    randomInterval = (long)random(3000, 7000); nextResetTime = millis() + randomInterval;
  }
}

// --- Fondo degradado monocromo frío ---
void drawBackgroundGradient() {
  hint(DISABLE_DEPTH_TEST);
  noStroke();
  for (int y = 0; y < height; y++) {
    float t = map(y, 0, height, 0, 1);
    float b = lerp(bgBrightTop, bgBrightBottom, t);
    fill(bgHue, bgSat, b, 0); // sin opacidad
    rect(0, y, width, 1);
  }
  hint(ENABLE_DEPTH_TEST);
}

// --- oscEvent (sin cambios) ---
void oscEvent(OscMessage theOscMessage) { /* ... */ lastDataTime = millis(); String addr = theOscMessage.addrPattern(); if (!isConnected && addr.startsWith("/py/")) {println(">>> CONEXIÓN ESTABLECIDA <<<"); isConnected = true;} try { if (addr.equals("/py/bands_env")) { if(theOscMessage.arguments().length==5){avgDelta=validateFloat(theOscMessage.get(0).floatValue(), avgDelta); avgTheta=validateFloat(theOscMessage.get(1).floatValue(), avgTheta); avgAlpha=validateFloat(theOscMessage.get(2).floatValue(), avgAlpha); avgBeta=validateFloat(theOscMessage.get(3).floatValue(), avgBeta); avgGamma=validateFloat(theOscMessage.get(4).floatValue(), avgGamma);}} else if (addr.equals("/py/bands_signed_env")) { if(theOscMessage.arguments().length==5){s_avgDelta = validateFloat(theOscMessage.get(0).floatValue(), s_avgDelta); s_avgTheta = validateFloat(theOscMessage.get(1).floatValue(), s_avgTheta); s_avgAlpha = validateFloat(theOscMessage.get(2).floatValue(), s_avgAlpha); s_avgBeta  = validateFloat(theOscMessage.get(3).floatValue(), s_avgBeta); s_avgGamma = validateFloat(theOscMessage.get(4).floatValue(), s_avgGamma);}} else if (addr.equals("/py/acc")) { if(theOscMessage.arguments().length==3){accX=validateFloat(theOscMessage.get(0).floatValue(), accX); accY=validateFloat(theOscMessage.get(1).floatValue(), accY); accZ=validateFloat(theOscMessage.get(2).floatValue(), accZ);}} else if (addr.startsWith("/py/")) { } else if (addr.startsWith("/desdemuse/")) { } else { }} catch (Exception e) { println("!!! ERROR procesando OSC: " + addr + " - " + e); } }

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
  if (key == 'w' || key == 'W') { showWireframe = !showWireframe; println("Wireframe " + (showWireframe?"VISIBLE":"OCULTO")); }
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

// --- Wireframe compartiendo deformación ---
void drawDeformedSphereWire(float radius, int segments, float noiseScale, float noiseAmplitude) {
  for (int i = 0; i < segments; i++) {
    float lat1 = map(i, 0, segments, 0, PI);
    float lat2 = map(i+1, 0, segments, 0, PI);
    beginShape(TRIANGLE_STRIP);
    for (int j = 0; j <= segments; j++) {
      float lon = map(j, 0, segments, 0, TWO_PI);
      PVector p1 = deformPoint(radius, lat1, lon, noiseScale, noiseAmplitude);
      PVector p2 = deformPoint(radius, lat2, lon, noiseScale, noiseAmplitude);
      vertex(p1.x, p1.y, p1.z);
      vertex(p2.x, p2.y, p2.z);
    }
    endShape();
  }
}

// --- Helper para deformar un punto con ruido compartido ---
PVector deformPoint(float radius, float lat, float lon, float noiseScale, float noiseAmplitude) {
  float xBase = radius * sin(lat) * cos(lon);
  float yBase = radius * sin(lat) * sin(lon);
  float zBase = radius * cos(lat);
  float n = noise(xBase * noiseScale, yBase * noiseScale, zBase * noiseScale);
  float safeN = validateFloat(n, 0.5f);
  float deformacion = map(safeN, 0, 1, -radius * noiseAmplitude, radius * noiseAmplitude);
  float r = max(0.1, radius + deformacion);
  return new PVector(r * sin(lat) * cos(lon), r * sin(lat) * sin(lon), r * cos(lat));
}

// --- Viñeta suave para enmarcar la esfera ---
void applyVignette() {
  hint(DISABLE_DEPTH_TEST);
  noStroke();
  int steps = 8;
  for (int i = 0; i < steps; i++) {
    float t = map(i, 0, steps-1, 0, 1);
    fill(0, 0, 0, vignetteStrength * 100 * t);
    rect(i, i, width - 2*i, height - 2*i);
  }
  hint(ENABLE_DEPTH_TEST);
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

  // --- SUAVIZADO LAPLACIANO ---
  // Suavizar vértices promediando con vecinos para eliminar picos
  for (int iter = 0; iter < 2; iter++) { // 2 iteraciones de suavizado
    PVector[][] smoothGlobe = new PVector[segments + 1][segments + 1];
    for (int i = 1; i < segments; i++) { // No suavizar polos
      for (int j = 0; j <= segments; j++) {
        PVector avg = new PVector(0, 0, 0);
        // Promediar con 4 vecinos
        avg.add(globe[i-1][j]);
        avg.add(globe[i+1][j]);
        avg.add(globe[i][(j-1+segments+1) % (segments+1)]);
        avg.add(globe[i][(j+1) % (segments+1)]);
        avg.div(4);
        smoothGlobe[i][j] = PVector.lerp(globe[i][j], avg, 0.4); // Mezcla 40% suavizado
      }
    }
    // Copiar polos sin suavizar
    for (int j = 0; j <= segments; j++) {
      smoothGlobe[0][j] = globe[0][j];
      smoothGlobe[segments][j] = globe[segments][j];
    }
    globe = smoothGlobe;
  }
  // -------------------------

  // Recalcular normales después del suavizado usando diferencias finitas
  for (int i = 0; i <= segments; i++) {
    for (int j = 0; j <= segments; j++) {
      // Calcular normales con diferencias finitas entre vértices vecinos
      PVector p_lat_plus = globe[min(i+1, segments)][j];
      PVector p_lat_minus = globe[max(i-1, 0)][j];
      PVector p_lon_plus = globe[i][(j+1) % (segments+1)];
      PVector p_lon_minus = globe[i][j > 0 ? j-1 : segments];
      
      PVector dLat = PVector.sub(p_lat_plus, p_lat_minus);
      PVector dLon = PVector.sub(p_lon_plus, p_lon_minus);
      PVector normal = dLat.cross(dLon);
      normal.normalize();
      globeNormals[i][j] = normal;
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
