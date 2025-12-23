# 🧠 Biomechanics Source Code

Sistema integrado de procesamiento y visualización de señales biomecánicas en tiempo real usando EEG, acelerómetro y sensores biométricos.

## 📋 Descripción General

Este repositorio contiene una suite completa para:
- **Captura de datos biomecánicos** desde sensores Muse 2, acelerómetros y sensores ambientales
- **Procesamiento en tiempo real** de señales EEG (bandas delta, theta, alpha, beta, gamma)
- **Visualización 3D** de datos con superficies deformadas interactivas
- **Grabación y reproducción** de sesiones de meditación para análisis post-procesamiento

---

## 🗂️ Estructura del Proyecto

```
biomechanics-source-code/
│
├── 📖 README.md                          # Este archivo
├── 📄 requirements.txt                   # Dependencias Python
│
├── 🔧 ESP32-base/                        # Firmware para microcontrolador
│   ├── sketch_nov24c.ino
│   └── sketch-inicial-esp32.ino
│
├── 🔌 ESP-proceso-python/                # Scripts de procesamiento ESP32
│
├── 📊 Procesador-osc/                    # Motor central de procesamiento
│   ├── py-v25-full.py                    # Script principal (3 modos: simulación/live/replay)
│   ├── py-v24.py                         # Versión anterior (referencia)
│   ├── py-v25-csv-replay.py              # Modo reproducción CSV (referencia)
│   ├── START_HERE.txt                    # Guía rápida de inicio
│   ├── QUICKSTART.md                     # Tutorial en 30 segundos
│   ├── README_V25_FULL.md                # Documentación técnica completa
│   ├── INTEGRATION_SUMMARY.md            # Resumen de integración
│   ├── INTEGRATION_MATRIX.md             # Matriz función a función
│   ├── EXAMPLES.md                       # 9 ejemplos prácticos
│   ├── CODE_DESCRIPTION.md               # Descripción del código
│   ├── CHANGELOG.md                      # Historial de cambios
│   ├── DATA_RECORDING.md                 # Formato de grabación
│   └── PPG_BPM_INTEGRATION.md            # Integración de PPG/BPM
│
├── 📈 registros-meditacion/              # Datos de meditación (16 sesiones)
│   ├── meditacion_20251208_082206.csv    # Rango temporal: 2025-12-08 a 2025-12-19
│   ├── meditacion_20251208_083651.csv    # Duración total: ~96 horas
│   ├── ... (14 archivos adicionales)
│   └── meditacion_20251219_194323.csv
│
└── 🎨 Visualizador-osc/                  # Visualización en Processing
    ├── esfera_base/
    │   └── esfera_base.pde               # Esfera base (wireframe)
    └── esfera_tejido_v2_33/
        ├── esfera_tejido_v2_33.pde       # Esfera sólida v33 (PRODUCCIÓN)
        └── data/                         # Assets (tipografía, etc.)
```

---

## 🚀 Quick Start (30 segundos)

### 1️⃣ Instalar dependencias
```bash
cd Procesador-osc
pip install -r ../requirements.txt
```

### 2️⃣ Ejecutar procesador
```bash
python3 py-v25-full.py
```

### 3️⃣ Seleccionar modo
```
[0] Simulador (sin hardware)
[1] Muse en vivo (sensor conectado)
[2] Reproducir CSV (datos históricos)
```

### 4️⃣ Abrir visualizador
- En Processing: Abrir `Visualizador-osc/esfera_tejido_v2_33/esfera_tejido_v2_33.pde`
- Datos OSC se envían a `127.0.0.1:5002`

---

## 📦 Componentes

### 🔌 Procesador OSC (`Procesador-osc/`)

**py-v25-full.py** - Script principal unificado (1,174 líneas)

**Características:**
- ✅ 3 modos de operación (Simulador | Live | CSV Replay)
- ✅ 37 funciones integradas
- ✅ Auto-detección de sensores
- ✅ Menú interactivo
- ✅ Baseline automática (2 fases)
- ✅ Filtros digitales (butter 4th order)
- ✅ Procesamiento de bandas EEG (delta, theta, alpha, beta, gamma)
- ✅ Acelerómetro (X, Y, Z)
- ✅ PPG / BPM (si disponible)
- ✅ Exportación MIDI (10 canales)

**Handlers OSC:**
```
/py/bands_env              → Envolventes de bandas EEG [5 valores]
/py/bands_signed_env       → Envolventes normalizadas [-2.0, 2.0]
/py/acc                    → Acelerómetro [X, Y, Z]
/py/ppg/bpm                → BPM en tiempo real
```

**Documentación:**
- `START_HERE.txt` - Comienza aquí
- `QUICKSTART.md` - Tutorial rápido
- `EXAMPLES.md` - 9 ejemplos prácticos
- `INTEGRATION_MATRIX.md` - Matriz completa función-a-función

---

### 🎨 Visualizador (`Visualizador-osc/`)

**esfera_tejido_v2_33.pde** - Visualización interactiva 3D (PRODUCCIÓN)

**Características v33:**
- ✅ **Superficie sólida deformada** con TRIANGLE_STRIP
- ✅ **Sistema de iluminación 3D** con lights() y cálculo de normales
- ✅ **Suavizado Laplaciano** (2 iteraciones) para superficie limpia
- ✅ **Mapeo dinámico de color** verde-azul según s_avgAlpha
- ✅ **Ruido 3D Perlin** con deformación paramétrica
- ✅ **Sistema de partículas** sincronizado con bandas EEG
- ✅ **Modo póster vertical** (3600×5400 px) para impresión
- ✅ **Toggle wireframe** con tecla 'w'
- ✅ **HUD interactivo** con ControlP5

**Parámetros configurables:**
- `sphereSegments`: 128 (resolución)
- `deformationFactor`: 0.45 (amplitud de deformación)
- `solidAlpha`: 100 (opacidad)
- `posterMode`: true/false (formato de salida)

**Interacción:**
- `w` → Toggle wireframe blanco
- `+/-` → Ajustar deformationFactor
- `r` → Resetear visualización
- Sliders ControlP5 para parámetros en vivo

---

## 📊 Datos

### Registros de Meditación (`registros-meditacion/`)

**16 sesiones de meditación** (36.61 MB)
- Rango temporal: 8 dic 2025 - 19 dic 2025
- Duración combinada: ~96 horas
- Formato: CSV con timestamps y datos EEG/ACC
- Compatible con modo replay (`py-v25-full.py` → Opción 2)

**Cómo reproducir:**
```bash
python3 py-v25-full.py
# Seleccionar [2] CSV Replay
# Elegir archivo de registros-meditacion/
# Ajustar velocidad (0.5x a 5.0x)
```

---

## 🔧 Requisitos Técnicos

### Hardware
- **Sensor EEG:** Muse 2 (o compatible)
- **Micrófono:** Para captura de audio
- **Opcional:** Acelerómetro, ESP32, sensores biométricos

### Software
- **Python 3.8+**
- **Processing 4.0+**
- **Bibliotecas Python:** (ver `requirements.txt`)
  - `muse-lsl`
  - `pythonosc`
  - `numpy`
  - `scipy`
  - `python-rtmidi`

### Sistema Operativo
- macOS 11+ (probado en macOS 14)
- Linux (compatible)
- Windows (compatible con ajustes)

---

## 📖 Documentación Detallada

### Por componente:

| Componente | Archivo | Propósito |
|-----------|---------|-----------|
| **Procesador** | `README_V25_FULL.md` | Visión técnica completa |
| **Procesador** | `QUICKSTART.md` | Inicio en 30 segundos |
| **Procesador** | `EXAMPLES.md` | 9 ejemplos prácticos |
| **Procesador** | `INTEGRATION_MATRIX.md` | Matriz función-a-función |
| **Datos** | `DATA_RECORDING.md` | Formato de grabación CSV |
| **PPG** | `PPG_BPM_INTEGRATION.md` | Integración de BPM |
| **Cambios** | `CHANGELOG.md` | Historial de versiones |

---

## 🎯 Casos de Uso

### 1. 🧘 Meditación en Vivo
```bash
python3 py-v25-full.py
# [1] Muse en vivo
# Visualizar en Processing en tiempo real
```

### 2. 🔬 Análisis Post-Sesión
```bash
python3 py-v25-full.py
# [2] CSV Replay
# Reproducir meditación histórica con análisis
```

### 3. 🧪 Simulación / Testing
```bash
python3 py-v25-full.py
# [0] Simulador
# Pruebas sin hardware
```

### 4. 🎬 Reproducción para Póster
```processing
// En Processing:
// posterMode = true
// sphereSegments = 128
// Exporta PNG 3600×5400 para impresión
```

---

## 🔄 Pipeline de Datos

```
Sensor Muse 2
    ↓
Python (py-v25-full.py)
├─ Filtros digitales (Butterworth)
├─ Transformada de Hilbert
├─ Envolventes de amplitud
├─ Normalización Z-score
└─ Envío OSC
    ↓
Processing (esfera_tejido_v2_33.pde)
├─ Recepción OSC
├─ Mapeo a parámetros 3D
├─ Deformación de geometría
├─ Cálculo de normales (iluminación)
└─ Renderizado sólido + partículas
    ↓
Visualización en tiempo real
+ Exportación PNG (modo póster)
```

---

## ⚙️ Configuración Avanzada

### Personalizar puertos OSC
En `py-v25-full.py`:
```python
PROC_IP = "127.0.0.1"
PROC_PORT = 5002  # Cambiar aquí
```

En `esfera_tejido_v2_33.pde`:
```processing
oscP5 = new OscP5(this, 5002);  // Debe coincidir
```

### Ajustar baseline automática
En `py-v25-full.py`:
```python
baseline_duration_seconds = 10  # Duración en segundos
```

### Modificar rango de bandas
En `py-v25-full.py`:
```python
FILTS={
  'delta': butter(0.5, 4),   # 0.5-4 Hz
  'theta': butter(4, 8),     # 4-8 Hz
  'alpha': butter(8, 13),    # 8-13 Hz (aumentado)
  'beta':  butter(13, 30),   # 13-30 Hz
  'gamma': butter(30, 45)    # 30-45 Hz
}
```

---

## 🐛 Solución de Problemas

### Error: "No Muse device found"
```bash
# Asegúrate que:
# 1. Muse está encendido
# 2. Bluetooth está activado
# 3. Ejecuta: python3 py-v25-full.py → [1] Live
```

### Error: "OSC connection refused"
```bash
# Verifica puertos:
# - Python envía a 127.0.0.1:5002
# - Processing escucha en 5002
# Usa: lsof -i :5002
```

### Datos OSC no llegan a Processing
```processing
// En Processing, verifica en consola:
println("OSC IN: " + oscP5.port());
// Debe mostrar 5002
```

### Memoria insuficiente (memory leak)
```python
# En py-v25-full.py, limpia partículas:
maxParticlesAllowed = 5000  # Reducir si es necesario
```

---

## 📝 Historial de Versiones

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| **v33** | Dic 2025 | Superficie sólida + iluminación 3D |
| **v25-full** | Dic 2025 | Unificación de 3 modos (sim/live/replay) |
| **v24** | Nov 2025 | Pipeline original |

Ver `CHANGELOG.md` para detalles completos.

---

## 🤝 Contribuir

Para contribuir:
1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/mi-mejora`
3. Commit: `git commit -m "feat: descripción"`
4. Push: `git push origin feature/mi-mejora`
5. Pull Request

---

## 📧 Contacto & Soporte

- **Documentación:** Ver archivos `.md` en carpetas correspondientes
- **Ejemplos:** `Procesador-osc/EXAMPLES.md`
- **Issues:** Reportar en GitHub Issues

---

## 📜 Licencia

Este proyecto es de código abierto. Consulta `LICENSE` para detalles.

---

## 🙏 Agradecimientos

- **Muse 2** - Sensor EEG
- **Python OSC** - Comunicación OSC
- **Processing** - Visualización gráfica
- **Comunidad open-source**

---

**Status:** ✅ Production Ready | 🧪 Fully Tested | 📚 Comprehensively Documented

Última actualización: 22 de diciembre de 2025
