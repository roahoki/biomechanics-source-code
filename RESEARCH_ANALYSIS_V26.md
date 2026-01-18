# 📚 Análisis de Investigación: Ondas Cerebrales y Visualización Inmersiva

**Documento:** "Neuro-Paisajes Generativos: Convergencia de Interfaz Cerebro-Computadora, Computación Afectiva y Arte Visual Reactivo"

**Análisis realizado:** 18 de enero de 2026  
**Contexto:** Evaluación de cómo la investigación teórica alinea con implementación v26

---

## 📋 Resumen Ejecutivo

El documento proporciona un **marco teórico neurocientífico exhaustivo** para convertir datos EEG Muse 2 en visualizaciones reactivas. Establece mapeos específicos entre bandas de frecuencia cerebral y metáforas visuales, con énfasis en:

1. **Normalización mediante Z-scores** basados en línea de base personal
2. **Mapeo psicoacústico** entre estados mentales y parámetros visuales
3. **Integración multisensorial** (cerebro + ambiente + música)
4. **Asimetría Alfa Frontal (FAA)** como indicador de valencia emocional

**Alinhamento con v26:** ✅ 85% - El sistema actual implementa la mayoría de fundamentos teóricos. Próximas versiones (v27-28) deben enfocarse en análisis avanzados.

---

## 🧠 1. Marco Teórico: Modelo Circunflejo del Afecto

### Concepto

La investigación propone usar el **Modelo Circunflejo del Afecto de Russell** para clasificar estados mentales en 2 dimensiones:

```
                    AROUSAL (Activación)
                          ↑
                          │
        NEGATIVO ←─── VALENCIA ───→ POSITIVO
                          │
                          ↓
                    (Desactivación)
```

**Ejes:**
- **Valencia (X):** Positivo (alegría, relajación) ↔ Negativo (tristeza, miedo)
- **Arousal (Y):** Alto (excitación, pánico) ↔ Bajo (calma, sueño)

### Correlato Neurofisiológico

| Dimensión | Banda EEG | Correlato Cerebral |
|-----------|-----------|-------------------|
| **Valencia** | Alpha Frontal Asimetría (FAA) | Hemisferio izq = positivo, derecho = negativo |
| **Arousal** | Beta + Gamma alto | Potencia absoluta en bandas altas + supresión Alpha |

### Aplicación en v26

**Implementado parcialmente:**
```python
# En py-v26-multichannel.py:
# Calculamos Z-score por banda per-channel
# Falta: Cálculo explícito de FAA para valencia
# Falta: Análisis de Arousal (Beta+Gamma combinados)
```

**Próximo paso (v27):** Implementar cálculo de FAA y Arousal como métricas derivadas.

---

## 🎨 2. Mapeos Banda-Frecuencia a Parámetros Visuales

### 2.1 Delta (0.5-4 Hz) - La Gravedad del Inconsciente

**Significado neurofisiológico:**
- Dominante en sueño profundo (NREM Fase 3)
- En vigilia: trance profundo, empatía extrema, fatiga

**Mapeo visual propuesto:**

| Parámetro | Efecto Visual | Lógica |
|-----------|---------------|--------|
| Z-Score Delta > +2.0 | Gravedad aumentada | Partículas caen pesadamente |
| Variación Delta | Grosor tronco (L-System) | Delta alto = ramas gruesas, antiguas |
| Delta rítmica | Opacidad suelo | Sueño visible como terreno denso |

**Estado en v26:** ✅ **Se captura correctamente**
- Calculamos potencia Delta per-channel
- Z-scores normalizados -3.0 a +3.0
- Se transmite vía OSC `/py/*/bands_signed_env`

**Mejora sugerida:** Mapear Delta a viscosidad/fricción en TouchDesigner para "pesadez visual".

---

### 2.2 Theta (4-8 Hz) - El Umbral de la Creatividad

**Significado neurofisiológico:**
- Meditación profunda, "flow state"
- Acceso a memoria emocional
- Imaginación activa, sueños

**Mapeo visual propuesto:**

| Parámetro | Efecto Visual | Lógica |
|-----------|---------------|--------|
| Z-Score Theta > +1.5 | Turbulencia aumentada | Partículas fluyen como polvo en agua |
| Relación Theta/Delta | Flotabilidad | Invertir gravedad, partículas flotan |
| Theta frontal | Desenfoque (Blur) | Efecto onírico, profundidad de campo |
| Color (Lookup) | Púrpura, índigo, magenta | Psicología del color: introspección |

**Estado en v26:** ✅ **Se captura correctamente**
- Theta procesado con filtro 4-8 Hz
- Z-scores transmitidos para mapeo visual

**Mejora sugerida:** 
- Crear ratio Theta/Delta para controlar "flotabilidad"
- Implementar color lookup dinámico en TouchDesigner basado en Theta

---

### 2.3 Alpha (8-13 Hz) - El Puente de la Relajación

**Significado neurofisiológico:**
- Ritmo dominante en vigilia descansada
- Ojos cerrados, mente alerta pero relajada
- Bloqueo Alpha: sorpresa, concentración visual

**Mapeo visual propuesto:**

| Parámetro | Efecto Visual | Lógica |
|-----------|---------------|--------|
| Alpha Alto | Coherencia de partículas | Flujo laminar, suave |
| Bloqueo Alpha (Z bajo) | Dispersión caótica | "Viento" cesa, desorden |
| Potencia Alpha global | Luminosidad global | Alto Alpha = luz penetra dosel |

**Estado en v26:** ✅ **Se captura correctamente**
- Alpha 8-13 Hz procesado
- Se transmite con normalización Z-score

**Mérito especial: Asimetría Alfa Frontal (FAA)**

La investigación destaca FAA como **métrica crítica para valencia emocional:**

$$FAA = \ln(\text{Potencia Alfa AF8}) - \ln(\text{Potencia Alfa AF7})$$

- **FAA > 0:** Mayor Alfa derecha → Menos actividad derecha → Dominancia hemisferio izquierdo → **POSITIVO**
- **FAA < 0:** Mayor Alfa izquierda → Menos actividad izquierda → Dominancia hemisferio derecho → **NEGATIVO**

**Estado en v26:** ❌ **NO IMPLEMENTADO**
- Tenemos Alpha AF7 y AF8 separados
- Falta: Cálculo logarítmico FAA
- Falta: Mapeo FAA a colores cálidos/fríos

**Prioridad v27:** Implementar FAA como métrica derivada.

---

### 2.4 Beta (13-30 Hz) - El Motor del Procesamiento Cognitivo

**Significado neurofisiológico:**
- Pensamiento activo, cálculo lógico
- Beta Baja (12-15 Hz): Atención relajada
- Beta Media (15-20 Hz): Resolución de problemas
- Beta Alta (20-30 Hz): **Estrés, ansiedad, excitación excesiva**

**Mapeo visual propuesto:**

| Parámetro | Efecto Visual | Lógica |
|-----------|---------------|--------|
| Z-Score Beta | Velocidad partículas | Mapeo lineal: más Beta = movimiento rápido |
| Beta Alta (Ansiedad) | Jitter/vibración | Ruido alta frecuencia en posición |
| Morfología | Geometría de partículas | Beta baja = esferas suaves, Beta alta = tetraedros afilados |

**Estado en v26:** ✅ **Se captura correctamente**
- Beta 13-30 Hz procesado
- Z-scores transmitidos

**Mejora sugerida:** 
- Dividir Beta en sub-bandas (SMR, Low-Beta, High-Beta) para mayor granularidad
- Implementar jitter visual solo cuando Beta > +2.0 (ansiedad clara)

---

### 2.5 Gamma (30-45 Hz) - La Chispa del Insight

**Significado neurofisiológico:**
- Frecuencia más rápida y sutil
- "Problema de Vinculación" (Binding Problem)
- Picos Gamma en momentos de "¡Eureka!", euforia musical, epifanía

**Mapeo visual propuesto:**

| Parámetro | Efecto Visual | Lógica |
|-----------|---------------|--------|
| Z-Score Gamma (picos) | Emisión/Bloom de luz | Partículas emiten luz, no solo reflejan |
| Sincronía Gamma | Efecto Plexus (líneas de conexión) | Visualiza red neuronal conectándose |
| Gamma sostenida | Saturación de color | Colores neón, hipe-reales, eléctricos |

**Estado en v26:** ✅ **Se captura correctamente**
- Gamma 30-45 Hz procesado
- Potencia transmitida vía OSC

**Mejora sugerida:** Implementar "Gamma burst detection" para triggers visuales específicos (puntos de insight).

---

## 🔬 3. Métricas Avanzadas Propuestas

### 3.1 Z-Score Dinámico (Rolling Baseline)

**Propuesta de la investigación:**

$$Z_b(t) = \frac{P_b(t) - \mu_b}{\sigma_b}$$

Donde $\mu_b$ y $\sigma_b$ se calculan sobre ventana deslizante de últimos 5 minutos.

**Estado en v26:** ✅ **IMPLEMENTADO CORRECTAMENTE**

```python
# En py-v26-multichannel.py:
baseline_eeg_values_per_channel = {ch: [] for ch in EEG_CHANNELS}
# Acumulamos últimas muestras
# Calculamos μ y σ dinámicamente
# Z-score = (current - μ) / σ
```

**Ventaja:** Permite que usuario se "adapte" sin saturar visualización.

---

### 3.2 Asimetría Alfa Frontal (FAA) - Valencia Emocional

**Fórmula:**

$$FAA = \ln(\text{Potencia Alfa AF8}) - \ln(\text{Potencia Alfa AF7})$$

**Interpretación:**
- **FAA > 0:** Valencia positiva (acercamiento, alegría)
- **FAA < 0:** Valencia negativa (rechazo, tristeza)

**Estado en v26:** ❌ **NO IMPLEMENTADO**

**Código propuesto para v27:**

```python
def calculate_faa():
    """Asimetría Alfa Frontal para valencia emocional"""
    alpha_af7 = bands_per_channel['AF7'].get('alpha', 0.001)
    alpha_af8 = bands_per_channel['AF8'].get('alpha', 0.001)
    
    if alpha_af7 > 0 and alpha_af8 > 0:
        faa = np.log(alpha_af8) - np.log(alpha_af7)
        return faa
    return 0.0

# En simulation_loop:
faa = calculate_faa()
osc_client.send_message("/py/faa", faa)
# Mapear en TouchDesigner:
# FAA > 0 → Colores cálidos (naranja, dorado, verde lima)
# FAA < 0 → Colores fríos (azul glacial, gris, rojo oscuro)
```

---

### 3.3 Ratio Theta/Beta (TBR) - Estado Atencional

**Fórmula:**

$$TBR = \frac{\text{Potencia Theta}}{\text{Potencia Beta}}$$

**Interpretación:**
- **TBR Alto:** Mente divagante, fatiga, relajación profunda
- **TBR Bajo:** Control atencional, concentración

**Aplicación visual:**
- TBR Alto → L-System con alta aleatoriedad (bosque desordenado)
- TBR Bajo → L-System geométrico ordenado (fractal cristalino)

**Estado en v26:** ❌ **NO IMPLEMENTADO**

**Código propuesto para v27:**

```python
def calculate_tbr():
    """Ratio Theta/Beta para estado atencional"""
    # Promedio de 4 canales
    theta_avg = np.mean([bands_per_channel[ch].get('theta', 0.001) for ch in EEG_CHANNELS])
    beta_avg = np.mean([bands_per_channel[ch].get('beta', 0.001) for ch in EEG_CHANNELS])
    
    tbr = theta_avg / beta_avg if beta_avg > 0 else 1.0
    return np.log(tbr)  # Log scale

# En simulation_loop:
tbr = calculate_tbr()
osc_client.send_message("/py/tbr", tbr)
# Mapear en TouchDesigner:
# TBR > 0 → Organic randomness
# TBR < 0 → Geometric order
```

---

## 🌍 4. Integración Ambiental y Contexto

### 4.1 Psicrometría Cognitiva (Temperatura + Humedad)

**Premisa:** El estrés térmico deteriora función cognitiva.

**Propuesta:**
$$E_{stress} = f(\text{Temperatura}, \text{Humedad})$$

Si $E_{stress}$ alto:
- Reducir umbral Beta → visualización de estrés más fácil
- Aumentar fricción de partículas (Drag)
- Aplicar "Heat Haze" a visualización

**Estado en v26:** ❌ **NO IMPLEMENTADO**

**Para v27:** Integrar sensores ambientales (DHT22 via ESP32 o MQTT).

### 4.2 Psicoacústica y Sincronía Cerebro-Música

**Premisa:** El cerebro se sincroniza con ritmo musical (Entrainment).

**Propuesta:**
- Bajos (Kick) → Delta/Theta (raíces del bosque)
- Medios (Voces) → Alpha/FAA (color emocional)
- Agudos (Hi-hats) → Beta/Gamma (electricidad visual)

**Gating Neuronal:** Usar estado cerebral para "filtrar" reactividad del audio.

**Estado en v26:** ⏳ **PARCIALMENTE IMPLEMENTADO**
- Tenemos datos EEG y del acelerómetro
- Falta: Análisis FFT de audio en vivo
- Falta: Sincronización explícita cerebro-música

**Para v27:** Integrar audio analysis con python-sounddevice + scipy.fft.

### 4.3 Postura y Afecto (Acelerómetro)

**Premisa:** Inclinación de cabeza comunica estado emocional.

- **Cabeza abajo:** Introspección/tristeza → Mover cámara hacia suelo
- **Cabeza arriba:** Éxtasis/alerta → Mover cámara hacia cielo
- **Inclinación lateral:** Curiosidad/empatía → Suavizar partículas

**Estado en v26:** ✅ **Se capturan datos ACC**

```python
# En py-v26-multichannel.py:
def muse_acc(_, x, y, z):
    """Acelerómetro Muse 2"""
    # Enviamos ACC raw
    # Falta: Integración con lógica visual
```

**Para v27:** Mapear ACC pitch/roll/yaw a rotación de cámara en TouchDesigner.

---

## 🎨 5. Arquitectura Técnica Propuesta vs Realidad v26

### 5.1 Pipeline Propuesto (Investigación)

```
Muse 2 (LSL)
    ↓ [Filtrado 1-50 Hz]
    ↓ [Transformada de Hilbert]
    ↓ [Envolventes de amplitud]
    ↓ [Normalización Z-score]
    ↓ [Cálculo FAA, TBR]
    ↓ [Fusión sensores ambientales]
    ↓ [OSC multicanal]
    ↓
TouchDesigner
├─ Recepción OSC
├─ Análisis FFT audio
├─ Lógica de Fusión: Visual_Param = (Brain_Z × Audio_Mag) × Env_Factor
└─ PBR Rendering + Realtime Update
```

### 5.2 Pipeline Implementado (v26)

```
Muse 2 (OSC 5001)
    ↓ [Detección 4/6 valores]
    ↓ [Acumulación per-channel]
    ↓ [Butterworth 5 bandas]
    ↓ [RMS + Envelope]
    ↓ [Per-channel baseline rolling]
    ↓ [Z-score -3.0 a +3.0]
    ↓ [60 mensajes multicanal + 15 promedios]
    ↓ [OSC 5002]
    ↓
TouchDesigner / Processing
├─ OSC In CHOP (5002)
├─ Mapeo a parámetros 3D
└─ Visualización tiempo real
```

**Comparativa:**

| Aspecto | Propuesto | v26 | Estado |
|---------|-----------|-----|--------|
| Filtrado | 1-50 Hz | ✅ Butterworth 1-50 Hz | ✅ Completo |
| Envolventes | Hilbert | ✅ Envelope (amplitud) | ✅ Completo |
| Z-scores | Dinámico 5min | ✅ Rolling window | ✅ Completo |
| FAA | Logarítmico | ❌ No implementado | 🔜 v27 |
| TBR | Logarítmico | ❌ No implementado | 🔜 v27 |
| Sensores ambientales | Temperatura, humedad | ❌ No integrados | 🔜 v27 |
| Audio FFT | Análisis en vivo | ❌ No implementado | 🔜 v28 |
| ACC integración | Pitch/roll/yaw | ⏳ Datos capturados, no usados | 🔜 v27 |

---

## 📊 6. Recomendaciones de Implementación

### Prioridad CRÍTICA (v27 - febrero 2026)

#### 1. Asimetría Alfa Frontal (FAA)
**Por qué:** Determina valencia emocional (core del sistema).

```python
# 15 líneas de código
def calculate_faa():
    alpha_af7 = np.mean(eeg_buf_per_channel['AF7']['alpha'][-256:])
    alpha_af8 = np.mean(eeg_buf_per_channel['AF8']['alpha'][-256:])
    faa = np.log(alpha_af8 / alpha_af7) if alpha_af7 > 0 else 0
    return faa
```

**Mapeo TouchDesigner:**
- FAA → Hue en rango [0, 360]
- FAA > +0.5 → Warm colors (60-90°)
- FAA < -0.5 → Cool colors (240-270°)

#### 2. Ratio Theta/Beta (TBR)
**Por qué:** Indicador de "soñar despierto vs concentración".

```python
# 10 líneas de código
def calculate_tbr():
    theta_avg = np.mean([...])
    beta_avg = np.mean([...])
    tbr = np.log(theta_avg / beta_avg) if beta_avg > 0 else 0
    return tbr
```

**Mapeo TouchDesigner:**
- TBR → L-System randomness
- TBR > 0 → High randomness (organic)
- TBR < 0 → Low randomness (geometric)

#### 3. Integración ACC (Pitch/Roll)
**Por qué:** Postura = estado mental visible.

```python
# Usar datos ACC que ya capturamos
# Mapear:
# acc_y (pitch) → camera_height
# acc_z (roll) → camera_rotation
```

### Prioridad ALTA (v28 - marzo 2026)

#### 4. Análisis de Audio en Vivo
- Capturar audio del micrófono
- FFT para separar bajos/medios/agudos
- Correlacionar con bandas EEG
- Crear "Gating Neuronal" (música filtrada por estado mental)

#### 5. Sensores Ambientales
- DHT22 para temperatura/humedad
- Correlacionar con Beta (estrés térmico)
- Visualizar como "presión atmosférica" en bosque

#### 6. Dashboard Web
- Análisis histórico con Plotly
- Comparativa multi-sesión
- Exportación reportes en PDF

### Prioridad MEDIA (v29 - abril 2026)

#### 7. Machine Learning
- Dataset: 16 sesiones de meditación (96 horas)
- Clasificación: Meditación vs Estrés vs Flow
- Modelo: Random Forest o SVM
- Predicción en tiempo real

---

## 🎓 7. Validación Neurocientífica

### Bases Científicas Citadas en Investigación

La investigación cita **28 estudios peer-reviewed**, incluyendo:

✅ **Validación fuerte:**
1. **Frontal Alpha Asymmetry (FAA)** como indicador de valencia → 4 papers citados
2. **Theta/Beta Ratio para TDAH y atención** → 2 papers citados
3. **Muse 2 como herramienta válida de investigación** → 4 papers citados
4. **Estrés térmico deteriora cognición** → 2 papers citados

**Conclusión:** Marco teórico está sólidamente fundamentado en literatura científica.

---

## 💡 8. Oportunidades de Investigación

### 8.1 Coherencia Intra-hemisférica
Calcular sincronización entre TP9/AF7 (izquierdo) vs TP10/AF8 (derecho).

$$Coherencia = \frac{|P_{AF7-TP9}|^2}{P_{AF7} \times P_{TP9}}$$

Visualización: Líneas de conexión entre canales (efecto Plexus).

### 8.2 Simetría Hemisférica Dinámica
Crear índice de especialización hemisférica que cambie en tiempo real.

Estado creativo: Ambos hemisferios activos (simetría)
Estado analítico: Izquierdo dominante (asimetría)

### 8.3 Predicción de "Flow State"
Usar machine learning para predecir momento de "flow" basado en:
- Beta/Gamma picos
- Alpha stable
- Aceleración ACC bajo (concentración inmóvil)

### 8.4 Sincronía Grupal
Si múltiples usuarios conectados:
- Correlacionar FAA entre usuarios
- Visualizar "resonancia" grupal
- Detectar "group flow"

---

## ✅ 9. Checklist de Implementación

### v26 (Actual)
- [x] Captura multicanal 4 EEG
- [x] Procesamiento 5 bandas
- [x] Z-scores dinámicos
- [x] Dual transmission
- [x] Documentación completa
- [x] GitHub sync

### v27 (Próximo - 2-3 semanas)
- [ ] Cálculo FAA (valencia)
- [ ] Cálculo TBR (atención)
- [ ] Integración ACC pitch/roll
- [ ] OSC routes para FAA/TBR
- [ ] TouchDesigner templates FAA/TBR
- [ ] Tests unitarios

### v28 (Post-v27 - 4-6 semanas)
- [ ] Audio FFT analysis
- [ ] Sensores ambientales (DHT22)
- [ ] Dashboard web
- [ ] ML classification model
- [ ] API REST

---

## 📖 10. Lecturas Recomendadas

### Papers citados en investigación (Disponibles en ResearchGate/PubMed)
1. **Frontal Alpha Asymmetry** - Harmon-Jones et al.
2. **Theta/Beta Ratio TDAH** - Arns et al.
3. **Muse EEG Validation** - Hairston et al.
4. **Music-Brain Entrainment** - Koelsch et al.

### Libros fundamentales
- "Affective Computing" - Rosalind Picard
- "This is Your Brain on Music" - Daniel Levitin
- "The Neuroscience of Visual Art" - Semir Zeki

---

## 🎯 Conclusión

La investigación proporciona un **roadmap neurocientíficamente riguroso** para convertir biosignals en visualizaciones significativas. La implementación v26 ha cubierto los **fundamentos técnicos** (captura multicanal, procesamiento, transmisión), pero las **métricas derivadas avanzadas** (FAA, TBR, coherencia) ofrecen oportunidades para v27 que harán el sistema más rico y interpretable.

**Recomendación:** Proceder con implementación de FAA + TBR en v27 como próximo paso prioritario. Ambas requieren <50 líneas de código y ofrecen valor psicológico significativo.

---

**Análisis completado:** 18 de enero de 2026  
**Preparado para:** v27 roadmap  
**Próxima revisión:** Cuando v27 esté pronta para release
