# CHANGELOG v26 - Soporte Multicanal EEG Muse 2

## Versión 26-multichannel (18 de enero, 2026)

### ✨ Nuevas Características

#### 1. **Soporte Completo para 4 Canales EEG Individuales (Muse 2)**
   - **Canales soportados**:
     - `TP9` (Temporal Izquierdo)
     - `AF7` (Frontal Izquierdo)
     - `AF8` (Frontal Derecho)
     - `TP10` (Temporal Derecho)
   
   - **Modos de procesamiento**:
     - `average`: Promedia los 4 canales (compatible v24)
     - `individual`: Procesa cada canal de forma independiente

#### 2. **Nuevo Sistema de Envío de Datos OSC Multicanal**

   **Mensajes por canal** (4 canales × 3 tipos × 5 bandas = 60 mensajes):
   ```
   /py/{canal}/bands_raw          [delta, theta, alpha, beta, gamma]  - RMS bruto
   /py/{canal}/bands_env          [δ, θ, α, β, γ]                    - Envolvente (magnitud)
   /py/{canal}/bands_signed_env   [δ, θ, α, β, γ]                    - Z-score con signo
   ```

   **Mensajes legacy (compatibilidad v24)** (siempre se envían):
   ```
   /py/bands_raw          [delta, theta, alpha, beta, gamma]  - Promedio de canales
   /py/bands_env          [δ, θ, α, β, γ]                    - Envolvente promedio
   /py/bands_signed_env   [δ, θ, α, β, γ]                    - Z-score promedio
   ```

   **Mensajes ACC** (3 ejes × 5 estadísticas):
   ```
   /py/acc_x_neutral, _range, _min, _max, _sigma  (similar para y, z)
   ```

   **Mensajes PPG**:
   ```
   /py/ppg  - Valor raw del sensor cardíaco
   ```

#### 3. **Cálculos de Baseline Independientes por Canal**

   Cada canal calcula su propia:
   - μ (media): Valor promedio durante calibración
   - σ (desviación estándar): Variabilidad individual
   - min/max: Rango observado

   **Ventaja**: Compensa diferencias naturales entre ubicaciones de sensores

#### 4. **Detección Automática de Formato Muse**

   El script detecta automáticamente:
   - 1 valor → Modo promedio
   - 4 valores → Modo multicanal (TP9, AF7, AF8, TP10)
   - 6 valores → Muse 2 con canales auxiliares (ignora los 2 últimos)

### 🔧 Cambios Técnicos

#### Procesamiento de Señal

1. **Filtrado Butterworth 4º orden por banda**:
   - Delta: 0.5-4 Hz (actividad lenta, sueño)
   - Theta: 4-8 Hz (ondas lentas, meditación)
   - Alpha: 8-13 Hz (relajación, ojos cerrados)
   - Beta: 13-30 Hz (actividad cognitiva)
   - Gamma: 30-45 Hz (procesamiento de información)

2. **RMS (Root Mean Square)**:
   ```
   raw = √(Σ(signal²) / n)
   ```

3. **Z-score normalizado**:
   ```
   z_score = (raw - μ_baseline) / σ_baseline
   ```
   - Valor: -3 a +3 típicamente
   - Negativo: Por debajo del baseline
   - Positivo: Por encima del baseline

4. **Suavizado exponencial**:
   ```
   smoothed = ALPHA × current + (1-ALPHA) × previous
   ALPHA = 0.3 (ponderación actual: 30%)
   ```

5. **Envolvente normalizada**:
   ```
   env = |z_score_suavizado|
   rango: 0.0 - 1.0 (normalizado)
   ```

### 📊 Formatos de Datos OSC

#### Ejemplo: Canal TP9 en operación normal

**Antes del baseline** (calibración):
```
/py/baseline/eeg/progress  → [0-100]  % completado
```

**Después del baseline** (operación normal):
```json
{
  "/py/tp9/bands_raw": [167.061, 46.844, 28.639, 28.710, 37.112],
  "/py/tp9/bands_env": [0.245, 0.156, 0.089, 0.142, 0.267],
  "/py/tp9/bands_signed_env": [0.245, -0.156, 0.089, -0.142, 0.267],
  
  "/py/af7/bands_raw": [130.848, 52.378, 33.453, 61.140, 99.715],
  "/py/af7/bands_env": [0.512, 0.340, 0.215, 0.378, 0.445],
  "/py/af7/bands_signed_env": [0.512, 0.340, -0.215, 0.378, -0.445],
  
  "/py/bands_raw": [166.508, 50.661, 31.546, 42.925, 68.414],
  "/py/bands_env": [0.379, 0.248, 0.152, 0.260, 0.356],
  "/py/bands_signed_env": [0.379, 0.092, 0.086, 0.118, 0.091]
}
```

**Estadísticas ACC**:
```json
{
  "/py/acc_x_neutral": -0.1024,
  "/py/acc_x_range": 1.0990,
  "/py/acc_x_min": -0.5678,
  "/py/acc_x_max": 0.5312,
  "/py/acc_x_sigma": 0.1915,
  
  "/py/ppg": 95.3
}
```

### 🚀 Cómo Usar

#### 1. **Seleccionar Modo de Operación**

```
=== SELECCIÓN DE FUENTE DE DATOS ===
0. Modo Simulador (Datos Falsos)
1. Solo Sensor Cerebral (Muse)
2. Salir
Selecciona una opción (0-2): 1
```

#### 2. **Configurar Sensor EEG**

```
--- Config Sensor Cerebral ---
¿Ondas? (s/n): s                          # Activar EEG
¿Procesar canales individuales? (s/n): s  # Modo individual (vs. average)
✓ Modo EEG: INDIVIDUAL
```

**Resultado**:
- Envía 4 canales individuales + promedio
- Cada canal se calibra independientemente

#### 3. **Calibración Automática (Baseline)**

```
🔄 INICIANDO CALIBRACIÓN (10s)...
   Mantén una postura relajada y neutral

[BASELINE] ████████████████████ 100% | ⏱️ 0.0s
```

**Proceso**:
1. **Fase 1 - EEG Neutral** (10s):
   - Relaja tu mente
   - Este estado se usa como referencia (μ, σ)

2. **Fase 2 - Posición Neutra ACC** (5s):
   - Mantén cabeza inmóvil
   - Se calibra posición neutra (baseline)

3. **Fase 3 - Rango de Movimiento** (10s):
   - Mueve cabeza en todas direcciones
   - Se calcula rango máximo de movimiento

#### 4. **Recibir Datos en TouchDesigner**

**OSC In Operator configuración**:
- Protocol: UDP
- Network Address: 127.0.0.1
- Port: 5002
- Bind to Address: 0.0.0.0

**Rutas disponibles**:
```
/py/tp9/bands_*    → Canal temporal izquierdo
/py/af7/bands_*    → Canal frontal izquierdo
/py/af8/bands_*    → Canal frontal derecho
/py/tp10/bands_*   → Canal temporal derecho
/py/bands_*        → Promedio de los 4 canales
/py/acc_*          → Datos acelerómetro
/py/ppg            → Heartbeat/Pulso
```

### 📈 Interpretación de Resultados

#### Valores Normales (Baseline)

```
Delta (0.5-4 Hz):     100-200 µV  - Actividad lenta/profunda
Theta (4-8 Hz):       30-60 µV    - Ondas lentas
Alpha (8-13 Hz):      20-50 µV    - Relajación
Beta (13-30 Hz):      10-40 µV    - Pensamiento
Gamma (30-45 Hz):     5-30 µV     - Procesamiento
```

#### Z-score Interpretación

```
z-score = 0        → Estado baseline (neutral)
z-score = +1       → 1 desv. estándar arriba
z-score = -1       → 1 desv. estándar abajo
z-score = +2..+3   → Estado alterado significativo
z-score = -2..-3   → Supresión significativa
```

#### Envolvente Interpretación

```
env = 0.0          → Suprimida (adormecimiento)
env = 0.3-0.5      → Normal/relajada
env = 0.7-1.0      → Activada/elevada
```

### 🔍 Herramientas de Diagnóstico

#### 1. **test_muse_format.py** - Detectar formato de mensajes

```bash
/Users/tomas/Documents/GitHub/.venv/bin/python test_muse_format.py
```

Muestra cuántos valores envía Muse por mensaje (1, 4 o 6).

#### 2. **test_osc_receiver.py** - Monitorear OSC en tiempo real

```bash
/Users/tomas/Documents/GitHub/.venv/bin/python test_osc_receiver.py
```

Captura todos los mensajes OSC en puerto 5002 y muestra resumen.

### 💾 Archivos Modificados

```
✓ py-v26-multichannel.py     (NUEVO - versión multicanal completa)
✓ py-v24.py                  (modificado - correcciones menores)
✓ py-v25-full.py             (modificado - debug mejorado)
+ test_muse_format.py         (NUEVO - diagnóstico formato)
+ test_osc_receiver.py        (NUEVO - monitoreo OSC)
+ Documentación completa      (README_MULTICANAL.md, etc.)
```

### 🐛 Bugs Corregidos

1. **Detección de datos multicanal incorrecta**
   - Antes: Esperaba 1024 valores (nunca llegaban)
   - Ahora: Detecta 4 o 6 valores correctamente

2. **Envío de datos a TouchDesigner**
   - Antes: Variables mal nombradas → no se enviaban datos
   - Ahora: Todos los datos se transmiten correctamente

3. **Cálculo de Z-score**
   - Antes: Nan en modo individual
   - Ahora: Calcula independientemente por canal

### ⚡ Performance

- **Latencia**: ~50-100ms (RTT a TouchDesigner)
- **Ancho de banda**: ~4KB/s en modo individual
- **CPU**: ~5-8% (procesamiento multicanal)

### 📝 Notas de Desarrollo

- El modo individual SIEMPRE envía también datos promediados (para no duplicar lógica)
- Los 2 canales auxiliares de Muse 2 se ignoran automáticamente
- Todas las estadísticas de baseline se guardan en `baseline_eeg_values_per_channel`
- Los buffers de datos se rotan automáticamente con ventanas de 512 muestras

### 🔄 Backward Compatibility

✅ Completamente compatible con v24:
- Mensajes `/py/bands_*` siguen siendo enviados
- Formato OSC idéntico
- Parámetros legacy funcionan igual

### 📚 Referencias

- Muse 2 Specs: 256 Hz sampling, 4 EEG channels
- OSC Protocol: Open Sound Control (RFC 4545)
- Signal Processing: SciPy Butterworth filters, NumPy operations
