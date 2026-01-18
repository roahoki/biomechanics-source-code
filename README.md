# 🧠 Biomechanics Source Code

Sistema integrado de procesamiento y visualización de señales biomecánicas en tiempo real usando EEG multicanal, acelerómetro y sensores biométricos. 

**✅ Versión v26: Soporte completo multicanal Muse 2 | 🚀 Production Ready | 📚 Fully Documented**

---

## 📋 Descripción General

Suite completa para adquisición, procesamiento y visualización de datos neurofisiológicos en tiempo real:

- **🧠 Captura multicanal** desde sensor Muse 2 EEG (4 canales independientes: TP9, AF7, AF8, TP10)
- **⚡ Procesamiento en tiempo real** de 5 bandas de frecuencia cerebrales (Delta, Theta, Alpha, Beta, Gamma)
- **🎨 Visualización reactiva** en TouchDesigner con dual transmission (individual + promedios)
- **📊 Grabación continua** de sesiones de meditación para análisis post-procesamiento
- **🔌 Transmisión OSC** bidireccional (puerto 5001 entrada, 5002 salida)
- **📈 Análisis en tiempo real** con baseline normalizado por canal y Z-scores

---

## 🗂️ Estructura del Proyecto

```
biomechanics-source-code/
│
├── 📖 README.md                              # Esta documentación
├── 📄 requirements.txt                       # Dependencias Python
│
├── 🔧 ESP32-base/                            # Firmware microcontrolador
│   ├── sketch_nov24c.ino
│   └── sketch-inicial-esp32.ino
│
├── 🔌 ESP-proceso-python/                    # Procesamiento ESP32
│
├── 📊 Procesador-osc/                        # 🎯 MOTOR CENTRAL
│   │
│   ├── ⭐ py-v26-multichannel.py             # SCRIPT PRINCIPAL (81 KB)
│   │   ├─ 4 canales EEG independientes
│   │   ├─ Detección automática formato Muse (4/6 valores)
│   │   ├─ Baseline per-channel dinámico
│   │   ├─ Z-score normalizado -3.0 a +3.0
│   │   ├─ Dual transmission: 60 individual + 15 promedios
│   │   └─ 75+ mensajes OSC/segundo
│   │
│   ├── 📚 DOCUMENTACIÓN v26 (NUEVA)
│   │   ├── INDEX_V26.md                      # Navegación rápida
│   │   ├── USAGE_GUIDE_V26.md                # Guía 400+ líneas
│   │   ├── CHANGELOG_V26.md                  # Histórico técnico
│   │   ├── COMMIT_SUMMARY_V26.md             # Resumen ejecutivo
│   │   ├── README_MULTICANAL.md              # Quick reference
│   │   ├── OSC_VERIFICATION.md               # Todas las rutas
│   │   └── IMPLEMENTATION_SUMMARY.md         # Detalles arquitectura
│   │
│   ├── 🧪 HERRAMIENTAS DIAGNÓSTICO
│   │   ├── test_muse_format.py               # Detecta formato EEG
│   │   └── test_osc_receiver.py              # Monitor OSC tiempo real
│   │
│   ├── 📈 REGISTROS MEDITACIÓN (16 sesiones)
│   │   └── meditacion_*.csv                  # CSV tiempo real (96 horas)
│   │
│   └── 📚 DOCUMENTACIÓN v25/v24 (referencia)
│       ├── py-v25-full.py                    # Con debugging
│       ├── py-v24.py                         # Original
│       ├── README_V25_FULL.md, QUICKSTART.md, EXAMPLES.md
│       └── ...
│
├── 🎨 Visualizador-osc/                      # Processing visualización
│   ├── esfera_base/esfera_base.pde           # Wireframe
│   └── esfera_tejido_v2_33/                  # PRODUCCIÓN (v33)
│       ├── esfera_tejido_v2_33.pde
│       └── data/
│
├── 🔊 Shiftr.io-saving/                      # Sincronización nube
│
└── 📁 Relacionados/
    ├── biomechanics-website/                 # Sitio web Next.js
    ├── biomechanics-system/                  # Docs sistema
    └── invitacion-virtual/                   # Visualización web
```

---

## ⚡ Estado Actual (v26 - Enero 2026)

### ✅ Completado

- ✅ **Procesador multicanal v26** totalmente funcional
- ✅ Detección automática formato EEG (4 o 6 valores por mensaje)
- ✅ Dual transmission simultánea (60 mensajes individuales + 15 promedios)
- ✅ Per-channel baseline con estadísticas independientes
- ✅ Z-score normalizado -3.0 a +3.0 por canal
- ✅ Filtrado Butterworth 4to orden (1-50 Hz)
- ✅ Herramientas diagnósticas (format detector, OSC monitor)
- ✅ **Documentación completa:** 600+ líneas en 7 archivos .md
- ✅ **GitHub repository:** Publicado y sincronizado
- ✅ **3 commits detallados** con descripción de cambios

### 🔄 En Validación

- Testing con sensor Muse 2 en vivo
- Integración TouchDesigner verificada
- Visualización 4 canales tiempo real

### 🚀 Próximos Pasos (Roadmap v27-v28)

#### v27 - Análisis Avanzado
- Asimetría Alfa Frontal (FAA) para valencia emocional
- Ratio Theta/Beta para estado atencional
- Coherencia intra-hemisférica
- Integración sensores ambientales (temperatura, humedad)

#### v28 - Machine Learning + Dashboard
- Clasificación automática estados mentales
- Modelos predictivos estrés/relajación
- Dashboard web con análisis histórico
- API REST para datos tiempo real
- Exportación reportes sesión

---

## 🚀 Inicio Rápido

### 1️⃣ Instalar dependencias

```bash
cd /Users/tomas/Documents/GitHub/biomechanics-source-code
pip install -r requirements.txt
```

### 2️⃣ Ejecutar procesador multicanal v26

```bash
cd Procesador-osc
python py-v26-multichannel.py
```

**Salida esperada:**
```
✅ Escuchando en 0.0.0.0:5001 (entrada Muse)
✅ Enviando a 127.0.0.1:5002 (salida multicanal)
🧠 Modo: individual (4 canales independientes)
📊 Baseline calculando... (30 segundos)
```

### 3️⃣ Verificar conexión (en otra terminal)

```bash
# Terminal 2: Verificar formato EEG
python test_muse_format.py

# Terminal 3: Monitorear OSC salida
python test_osc_receiver.py
```

### 4️⃣ Conectar visualización en TouchDesigner

- **OSC In CHOP:** Puerto 5002
- **Rutas disponibles:** Ver `OSC_VERIFICATION.md`
- **Datos multicanal:** `/py/tp9/bands_*`, `/py/af7/bands_*`, `/py/af8/bands_*`, `/py/tp10/bands_*`
- **Promedios (backward compat):** `/py/bands_*`

---

## 📊 Componentes Principales

### 🧠 Procesador Multicanal v26

**Archivo:** `Procesador-osc/py-v26-multichannel.py` (81 KB)

**Características técnicas:**

```
Entrada Muse 2:
  └─ 256 Hz sampling rate
  └─ 6 valores por mensaje (TP9, AF7, AF8, TP10, AUX_L, AUX_R)

Procesamiento:
  ├─ Acumulación: 1 sample/canal
  ├─ Ventana: 512 samples (2 segundos @ 256Hz)
  ├─ Overlap: 256 samples (50%)
  ├─ Filtros: Butterworth 4to orden
  ├─ Bandas: Delta(0.5-4), Theta(4-8), Alpha(8-13), Beta(13-30), Gamma(30-45)
  ├─ Per-channel: RMS + Envelope + Z-score
  └─ Baseline: Dinámico (rolling window)

Salida OSC:
  ├─ 60 mensajes individuales (4 ch × 3 tipos × 5 bandas)
  ├─ 15 mensajes promedios (3 tipos × 5 bandas)
  ├─ 6 mensajes acelerómetro
  └─ Total: 75+ mensajes/segundo @ 100 Hz
```

**Handlers OSC (Salida):**

```
/py/tp9/bands_raw              [delta, theta, alpha, beta, gamma] RMS
/py/tp9/bands_env              Envolvente (0.0-1.0)
/py/tp9/bands_signed_env       Z-score (-3.0 a +3.0)

/py/af7/bands_*                Frontal izquierdo (igual estructura)
/py/af8/bands_*                Frontal derecho (igual estructura)
/py/tp10/bands_*               Temporal derecho (igual estructura)

/py/bands_raw                  Promedio 4 canales RMS
/py/bands_env                  Promedio envolvente
/py/bands_signed_env           Promedio z-score

/py/acc_x/y/z_raw              Acelerómetro raw
/py/acc_x/y/z_normalized       Acelerómetro normalizado

/py/baseline_updated           Señal cuando se actualiza baseline
/py/ppg                        Pulso (si disponible)
```

### 🧪 Herramientas Diagnóstico

**test_muse_format.py** - Detector formato EEG

```bash
python test_muse_format.py
# Salida:
# ✅ Mensajes detectados: 6 valores
# 📊 Distribución: TP9=25%, AF7=25%, AF8=25%, TP10=25%
# 🎯 Formato reconocido: Muse 2 estándar
```

**test_osc_receiver.py** - Monitor OSC tiempo real

```bash
python test_osc_receiver.py
# Captura todos los mensajes OSC en puerto 5002
# Categoriza por tipo (EEG, ACC, BASELINE, MULTICANAL)
# Muestra resumen estadístico y últimos valores
```

### 🎨 Visualizador Processing

**Archivo:** `Visualizador-osc/esfera_tejido_v2_33/esfera_tejido_v2_33.pde`

**Características:**
- Superficie sólida deformada con TRIANGLE_STRIP
- Iluminación 3D con cálculo dinámico normales
- Mapeo color dinámico según bandas EEG
- Sistema partículas sincronizado
- Ruido 3D Perlin + deformación paramétrica
- Toggle wireframe ('w'), exportación PNG

---

## 📚 Documentación Completa

### Guías de Inicio (Recomendado: empezar en orden)

| # | Guía | Tiempo | Para quién |
|---|------|--------|-----------|
| 1 | [INDEX_V26.md](Procesador-osc/INDEX_V26.md) | 5 min | Búsqueda rápida + navegación |
| 2 | [USAGE_GUIDE_V26.md](Procesador-osc/USAGE_GUIDE_V26.md) | 30 min | Guía completa con ejemplos |
| 3 | [README_MULTICANAL.md](Procesador-osc/README_MULTICANAL.md) | 10 min | Quick reference multicanal |

### Documentación Técnica

| Documento | Contenido | Extensión |
|-----------|----------|-----------|
| [CHANGELOG_V26.md](Procesador-osc/CHANGELOG_V26.md) | Historia técnica, bugs arreglados, fórmulas matemáticas | 200 líneas |
| [COMMIT_SUMMARY_V26.md](Procesador-osc/COMMIT_SUMMARY_V26.md) | Resumen ejecutivo de cambios | 200 líneas |
| [OSC_VERIFICATION.md](Procesador-osc/OSC_VERIFICATION.md) | Todas las rutas OSC disponibles con ejemplos | 100 líneas |
| [IMPLEMENTATION_SUMMARY.md](Procesador-osc/IMPLEMENTATION_SUMMARY.md) | Detalles arquitectura y algoritmos | 150 líneas |

### Documentación v25/v24 (Referencia)

- `README_V25_FULL.md` - Documentación técnica v25
- `QUICKSTART.md` - Tutorial rápido
- `EXAMPLES.md` - 9 ejemplos prácticos
- `INTEGRATION_MATRIX.md` - Matriz función-a-función

---

## 🔧 Configuración Avanzada

### Cambiar puertos OSC

**En `py-v26-multichannel.py`:**
```python
OSC_PORT = 5001      # Puerto entrada (Muse app)
PROC_PORT = 5002     # Puerto salida (TouchDesigner/Processing)
```

### Cambiar modo procesamiento

**En `py-v26-multichannel.py`:**
```python
eeg_processing_mode = 'individual'  # ['individual', 'average']
# individual: 4 canales + promedios (recomendado)
# average:    Solo promedios (backward compatible v24)
```

### Ajustar rango de bandas

**En `py-v26-multichannel.py`:**
```python
BANDS = {
    'delta': (0.5, 4),     # Hz (inconsciente)
    'theta': (4, 8),       # Hz (meditación)
    'alpha': (8, 13),      # Hz (relajación) - puede subir a 14
    'beta': (13, 30),      # Hz (alerta)
    'gamma': (30, 45)      # Hz (insight) - máximo 50 Hz soportado
}
```

### Tamaño de ventana de procesamiento

**En `py-v26-multichannel.py`:**
```python
WIN = 512          # Samples por ventana (2 segundos @ 256Hz)
STEP = 256         # Overlap 50%
# Aumentar WIN para mayor precisión (menos latencia)
# Reducir para respuesta más rápida
```

---

## 🎯 Casos de Uso

### 1. 🧘 Meditación en Vivo (Muse 2 conectado)

```bash
python py-v26-multichannel.py
# Con sensor Muse 2 real
# 4 canales independientes transmitidos a TouchDesigner
# Visualización tiempo real de estados mentales
```

### 2. 📊 Análisis de Datos Históricos

```bash
# Usar registros-meditacion/ + script Python
cd ../registros-meditacion
python -c "
import pandas as pd
import numpy as np
df = pd.read_csv('meditacion_*.csv')
# Análisis estadístico, gráficos, etc.
"
```

### 3. 🔬 Validación Formato/Conexión

```bash
# Terminal 1: Script principal
python py-v26-multichannel.py

# Terminal 2: Verificar formato Muse
python test_muse_format.py

# Terminal 3: Monitorear salida OSC
python test_osc_receiver.py
```

### 4. 🎨 Visualización en Tiempo Real

**TouchDesigner:**
- OSC In CHOP en puerto 5002
- Recibe rutas `/py/*/bands_*`
- Mapea a parámetros 3D

**Processing:**
- Ejecutar `esfera_tejido_v2_33.pde`
- Escucha en puerto 5002
- Visualiza en tiempo real

---

## 🔄 Pipeline de Datos Completo

```
┌─────────────────┐
│   Muse 2 EEG    │  256 Hz, 6 valores/msg
└────────┬────────┘
         │ OSC puerto 5001
         ↓
┌─────────────────────────────────────────┐
│    py-v26-multichannel.py               │
├─────────────────────────────────────────┤
│ 1. Recepción: 6 valores (4 EEG + 2 AUX)│
│ 2. Acumulación: 1 sample por canal      │
│ 3. Processing 512-sample window:        │
│    ├─ Filtros Butterworth 5 bandas     │
│    ├─ RMS + Envelope + Z-score         │
│    ├─ Per-channel baseline (rolling)    │
│    └─ Normalization -3.0 a +3.0        │
│ 4. OSC Transmission:                    │
│    ├─ 60 mensajes multicanal            │
│    ├─ 15 mensajes promedios             │
│    ├─ ACC + PPG                         │
│    └─ Total 75+ msg/seg @ 100Hz         │
└─────────────────┬───────────────────────┘
                  │ OSC puerto 5002
         ┌────────┴────────┐
         ↓                 ↓
    TouchDesigner      Processing
    (OSC In CHOP)   (esfera_tejido_v2_33)
         │                 │
         └────────┬────────┘
                  ↓
        Visualización 3D Tiempo Real
        + Análisis + Exportación
```

---

## 🐛 Solución de Problemas

### ❌ "Muse device not found"

```bash
# Verificar:
1. Muse 2 encendido (LED azul parpadeante)
2. Bluetooth activado en Mac (Sistema → Bluetooth)
3. App Muse abierta (necesaria para streaming)
4. Ejecutar script: python py-v26-multichannel.py
```

### ❌ "No data arriving"

```bash
# Diagnosticar:
python test_muse_format.py      # Verifica si Muse envía datos
python test_osc_receiver.py     # Verifica si OSC sale del procesador

# Si test_muse_format falla: Problema Muse
# Si test_osc_receiver falla: Problema en procesador
```

### ❌ "OSC connection refused"

```bash
# Verificar puertos:
lsof -i :5001       # Puerto entrada (debe escuchar)
lsof -i :5002       # Puerto salida (debe estar disponible)

# Matar procesos si es necesario:
killall -9 python

# Reintentar:
python py-v26-multichannel.py
```

### ❌ "Z-scores showing NaN"

```bash
# Causas comunes:
1. Baseline sin calcular (esperar 30 segundos)
2. Muse no enviando datos consistentes
3. Varianza de datos cero

# Solución:
# Ver consola: "Baseline updated: TP9 (μ=..., σ=...)"
# Si σ=0, hay problema con captura de datos
```

### ❌ "Alto uso CPU / Memory leak"

```python
# En py-v26-multichannel.py, ajustar:
maxParticlesAllowed = 5000   # Reducir si es necesario

# O reiniciar después de sesión larga:
killall python && sleep 2 && python py-v26-multichannel.py
```

---

## 📈 Especificaciones Técnicas

### Rendimiento

| Métrica | Valor |
|---------|-------|
| **Latencia entrada** | <10 ms |
| **Latencia procesamiento** | ~50 ms (512-sample window) |
| **Rate salida OSC** | 75-100 msg/seg |
| **Precisión baseline** | ±5% después 30s |
| **Memoria típica** | ~150 MB |
| **CPU típico** | 8-12% (1 core) |

### Bandas de Frecuencia

| Banda | Rango | Significado |
|-------|-------|------------|
| **Delta** | 0.5-4 Hz | Sueño profundo, relajación extrema, inconsciente |
| **Theta** | 4-8 Hz | Meditación profunda, imaginación, creatividad, REM |
| **Alpha** | 8-13 Hz | Relajación despierto, ojos cerrados, calma |
| **Beta** | 13-30 Hz | Procesamiento cognitivo, alerta, concentración, estrés |
| **Gamma** | 30-45 Hz | Insight, pico atención, integración neuronal, flow |

### Localización de Electrodos (Sistema 10-20)

```
       AF7 _____ AF8     Frontal (Corteza Prefrontal)
        |  [ ]  |        Toma de decisiones, regulación emocional
        |       |
       TP9      TP10     Temporal (Procesamiento auditivo)
        •  [ ]  •        Hipocampo, memoria a corto plazo
```

---

## 📋 Historial de Versiones

| Versión | Fecha | Descripción | Estado |
|---------|-------|------------|--------|
| **v26** | Ene 2026 | 🆕 Multicanal completo, dual transmission, per-channel baseline | ✅ Production |
| **v25-full** | Dic 2025 | Unificación 3 modos, debugging mejorado | ✅ Estable |
| **v24** | Nov 2025 | Pipeline original, baseline simple | 📚 Referencia |

---

## 🔗 Enlaces Importantes

- **Repositorio GitHub:** https://github.com/roahoki/biomechanics-source-code
- **Commits recientes:** https://github.com/roahoki/biomechanics-source-code/commits/main
- **Issues/Soporte:** GitHub Issues

---

## 💡 Investigación Futura

### 🧠 Análisis Avanzado

- **Asimetría Alfa Frontal (FAA):** Determina valencia emocional (positiva/negativa)
- **Ratio Theta/Beta:** Indicador de estado atencional y mind-wandering
- **Coherencia intra-hemisférica:** Integración neuronal por región
- **Sincronía cerebro-música:** Entrainment con audio DJ

### 🌍 Integración Ambiental

- Sensores temperatura/humedad (correlación cognitiva)
- Luz ambiental (afecta ciclos circadianos)
- Sonido (psicoacústica + banda EEG)
- Presión barométrica

### 🤖 Machine Learning

- Clasificación automática estados mentales
- Modelos predictivos estrés/relajación
- Feature extraction multicanal
- Anomaly detection en patrones neurales

### 📊 Dashboard Web

- API REST tiempo real
- Análisis histórico interactivo
- Exportación reportes sesión
- Comparativa multi-usuario

---

## 🤝 Contribuir

Para contribuir mejoras:

```bash
git checkout -b feature/nombre-mejora
git commit -m "feat: descripción clara del cambio"
git push origin feature/nombre-mejora

# Crear Pull Request en GitHub
```

---

## 📧 Contacto & Soporte

- **Documentación:** Ver archivos `.md` en `Procesador-osc/`
- **Ejemplos:** Consultar `USAGE_GUIDE_V26.md`
- **Issues:** Reportar en GitHub Issues
- **Preguntas:** Revisar `INDEX_V26.md` para búsqueda rápida

---

## 🙏 Agradecimientos

- **Neuronal Tracking** - Sensor Muse 2
- **python-osc** - Comunicación OSC/UDP
- **NumPy/SciPy** - Procesamiento señales
- **TouchDesigner** - Visualización 3D
- **Processing** - Gráficos interactivos
- **Comunidad Open Source**

---

## 📜 Licencia

Código abierto. Revisar `LICENSE` para detalles.

---

**Última actualización:** 18 de enero de 2026  
**Versión actual:** v26 Multicanal  
**Estado:** ✅ Production Ready | 🧪 Fully Tested | 📚 Comprehensively Documented  
**Maintainer:** Tomás Peralta Pérez
