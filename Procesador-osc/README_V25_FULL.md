# 🧠 py-v25-full: Biomechanics OSC Processor

**Version 25-full** | Python 3.7+ | macOS/Linux/Windows | Production Ready ✅

---

## 🎯 ¿Qué es?

**py-v25-full.py** es un procesador integrado de datos biomecánicos que:

- 📊 **Reproduces** grabaciones previas de datos cerebrales/movimiento
- 🧠 **Procesa** señales EEG del sensor Muse en tiempo real
- 🎲 **Simula** datos para testing sin hardware
- 📡 **Envía** datos automáticamente a Processing/TouchDesigner
- ⚡ **Calibra** baselines automáticamente

---

## 🚀 Inicio Rápido (30 segundos)

### 1. Abre terminal
```bash
cd /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc
```

### 2. Ejecuta el script
```bash
python3 py-v25-full.py
```

### 3. Selecciona modo
```
=== SELECCIÓN DE FUENTE DE DATOS ===
0. Modo Simulador (Datos Falsos)
1. Sensor Cerebral en Vivo (Muse)
2. Reproducir desde CSV          ← Elige ESTO
3. Salir

Selecciona una opción (0-3): 2
```

### 4. Elige archivo
```
📊 Archivos CSV disponibles:

1. meditacion_20251219_194323.csv
   📅 2025-12-19 19:43:23 | 📈 2560 líneas | ⏱️ 4m 16s

Selecciona archivo (0-4): 1
```

### 5. Presiona Enter
```
Presiona Enter para iniciar...
▶️ Reproducción iniciada (Ctrl+C para detener)
Progreso: [████████████      ] 65%
```

**¡Listo!** Los datos se envían automáticamente a Processing.

---

## 📋 Documentación

### Para Empezar
- 📘 **[QUICKSTART.md](QUICKSTART.md)** - Guía en 30 segundos
- 🎓 **[EXAMPLES.md](EXAMPLES.md)** - 9 ejemplos prácticos

### Para Entender
- 📖 **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Descripción completa
- 🔍 **[INTEGRATION_MATRIX.md](INTEGRATION_MATRIX.md)** - Matriz detallada
- 📝 **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios

### Este Documento
- 📌 **[README.md](README.md)** - Visión general

---

## 🎛️ Tres Modos de Operación

### 🎲 Modo 0: Simulador
```
Genera datos sintéticos sin hardware
↓
Útil para: Testing, desarrollo, demo
```

### 🧠 Modo 1: Muse en Vivo
```
Conecta sensor cerebral en tiempo real
↓
Requiere: Muse + app enviando OSC
↓
Útil para: Producción, mediciones reales
```

### ⭐ Modo 2: Reproducir CSV
```
Reproduce datos grabados previamente
↓
Requiere: Archivo meditacion_*.csv
↓
Útil para: Testing, comparativas, análisis
```

---

## 📊 Funcionalidades Principales

### ✅ Reproducción de CSV
- Auto-detección de archivos
- Menú con metadatos (fecha, duración, tamaño)
- Control de velocidad (0.5x a 5.0x)
- Barra de progreso
- Auto-detección de sensores disponibles

### ✅ Procesamiento de Señal
- Filtros Butterworth para 5 bandas EEG
- Cálculo de RMS (amplitud)
- Detector de envelope con z-score
- Escalado automático a 0-127

### ✅ Baseline Calibración
- EEG: Captura 10-30 segundos de actividad base
- ACC: 2 fases (neutral 5s + movimiento 10s)
- Cálculo automático de μ (media) y σ (desviación)
- Recalibración en tiempo real (Ctrl+B)

### ✅ Comunicación OSC
- Envía automáticamente a Processing/TouchDesigner
- IP: 127.0.0.1, Puerto: 5002
- Mensajes: `/py/bands_env`, `/py/acc`, `/py/ppg/bpm`

---

## 🔧 Requisitos

### Software
- Python 3.7+
- pip (gestor de paquetes)

### Dependencias Python
```bash
pip install numpy scipy python-osc pandas
```

### Hardware (Opcional)
- Muse (para modo en vivo)
- Processing o TouchDesigner (para visualizar)
- Arduino (para datos adicionales)

---

## 📡 Integración con Processing

### Setup en Processing
```java
import oscP5.*;

OscP5 oscP5;

void setup() {
  size(800, 600);
  // Escuchar en puerto 5002
  oscP5 = new OscP5(this, 5002);
}

void oscEvent(OscMessage msg) {
  if (msg.checkAddrPattern("/py/bands_env")) {
    float[] bands = new float[5];
    for (int i = 0; i < 5; i++) {
      bands[i] = msg.get(i).floatValue();
    }
    println("EEG: " + java.util.Arrays.toString(bands));
  }
}
```

### Mensajes OSC Disponibles
```
/py/bands_env [float, float, float, float, float]    5 bandas EEG
/py/bands_raw [float, float, float, float, float]    RMS sin procesar
/py/acc [float, float, float]                         Acelerómetro X,Y,Z
/py/ppg/bpm float                                     BPM (opcional)
```

---

## 📁 Archivos en Este Directorio

```
Procesador-osc/
├── py-v25-full.py              ← SCRIPT PRINCIPAL (1174 líneas)
├── py-v24.py                   ← Referencia (v24 original)
├── py-v25-csv-replay.py        ← Referencia (v25 original)
│
├── README.md                   ← Este archivo
├── QUICKSTART.md               ← Guía rápida (30s)
├── INTEGRATION_SUMMARY.md      ← Descripción completa
├── INTEGRATION_MATRIX.md       ← Matriz detallada
├── INTEGRATION_COMPLETE.md     ← Resumen de integración
├── EXAMPLES.md                 ← 9 ejemplos prácticos
├── CHANGELOG.md                ← Historial de cambios
│
├── meditacion_20251219_194323.csv    ← 2560 líneas (4m 16s)
├── meditacion_20251217_215911.csv    ← 1800 líneas (3m)
├── meditacion_20251216_084530.csv    ← 950 líneas (1m 35s)
└── ... (10+ archivos más)
```

---

## 💻 Uso en Terminal

### Opción 1: Interactivo (Recomendado)
```bash
python3 py-v25-full.py
# Te pide seleccionar opciones interactivamente
```

### Opción 2: Con Script (Automatizado)
```bash
echo -e "2\n1\n1.0\n" | python3 py-v25-full.py
# Reproducir archivo 1 a velocidad 1.0x
```

### Opción 3: En Background
```bash
python3 py-v25-full.py > output.log 2>&1 &
```

---

## 🧠 Estructura de Datos EEG

Cada banda se procesa con 3 valores:

| Banda | Rango | Significado |
|-------|-------|------------|
| **Delta** | 0.5-4 Hz | Ondas lentes, sueño profundo |
| **Theta** | 4-8 Hz | Meditación, creatividad |
| **Alpha** | 8-13 Hz | Relajación, calma |
| **Beta** | 13-30 Hz | Concentración, alerta |
| **Gamma** | 30-45 Hz | Procesamiento cognitivo |

Valores calculados:
- **RMS**: Amplitud bruta (sin procesar)
- **ENV**: Envelope (amplitud normalizada)
- **CC**: Control Change 0-127 (para MIDI/osc)

---

## 🔍 Debugging

### Activar modo debug
```python
# En py-v25-full.py, cambiar:
debug_mode = True  # Línea ~400
```

### Ver mensajes OSC
```
[OSC RECEIVED] /muse/eeg: (array(...))
[OSC RECEIVED] /muse/acc: (0.05, -0.02, 0.98)
[OSC RECEIVED] /py/bands_env: [0.5, 0.8, 1.2, 0.9, 0.4]
```

### Verificar archivos CSV
```bash
# Ver estructura
head -3 meditacion_20251219_194323.csv

# Contar líneas
wc -l meditacion_20251219_194323.csv

# Ver tamaño
ls -lh meditacion_20251219_194323.csv
```

---

## 🚨 Troubleshooting

### "No se encuentran archivos CSV"
✓ Ejecuta desde el directorio correcto:
```bash
cd /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc
```

### "Error de importación: No module named 'numpy'"
✓ Instala dependencias:
```bash
pip install numpy scipy python-osc pandas
```

### "OSC no llega a Processing"
✓ Verifica puerto:
```bash
lsof -i :5002
```
✓ Verifica IP en Processing:
```
OSCin recibe en: 127.0.0.1:5002
```

### "CSV no se abre"
✓ Verifica que existe:
```bash
ls -la meditacion_*.csv
```
✓ Verifica que no está en uso:
```bash
lsof | grep meditacion
```

---

## 📊 Estadísticas del Proyecto

```
Líneas de código:
  py-v24.py              1,646 líneas
  py-v25-csv-replay.py     634 líneas
  py-v25-full.py         1,174 líneas (integrado, -49% duplicados)

Funciones:
  Handlers OSC:            5
  Baseline closers:        4
  Signal processing:       5
  CSV/replay:              5
  Control/utility:        13
  ────────────────────────────
  Total:                  37 funciones

Documentación:
  QUICKSTART.md           6.2 KB
  INTEGRATION_SUMMARY.md  9.6 KB
  INTEGRATION_MATRIX.md   8.8 KB
  INTEGRATION_COMPLETE.md 7.7 KB
  EXAMPLES.md             10 KB
  CHANGELOG.md           12 KB
  ────────────────────────────
  Total:                ~55 KB
```

---

## 🎓 Ejemplos de Uso

### Ejemplo 1: Reproducir CSV Normal
```bash
python3 py-v25-full.py
# Selecciona 2 → archivo 1 → velocidad 1.0
```

### Ejemplo 2: Reproducir a 2x Velocidad
```bash
python3 py-v25-full.py
# Selecciona 2 → archivo 1 → velocidad 2.0
```

### Ejemplo 3: Simular Sin Hardware
```bash
python3 py-v25-full.py
# Selecciona 0
```

### Ejemplo 4: Conectar Muse
```bash
python3 py-v25-full.py
# Selecciona 1 → responde preguntas
```

Más ejemplos en [EXAMPLES.md](EXAMPLES.md)

---

## 🎯 Próximos Pasos

### Próximas Características
- [ ] Soporte de atajos de teclado en macOS
- [ ] Web UI para selección de archivos
- [ ] Batch processing (múltiples CSV)
- [ ] Real-time visualization
- [ ] Cloud storage

### Mejoras Propuestas
- [ ] Implementar MIDI completamente
- [ ] Agregar soporte para más sensores
- [ ] Integración con machine learning
- [ ] Plugin system

---

## 📞 Contacto & Soporte

**Versión**: 25-full  
**Última Actualización**: 2025-12-22  
**Status**: ✅ Production Ready  

Para preguntas o reportar bugs:
1. Consulta [QUICKSTART.md](QUICKSTART.md)
2. Revisa [EXAMPLES.md](EXAMPLES.md)
3. Habilita modo debug
4. Mira [CHANGELOG.md](CHANGELOG.md)

---

## 📄 Licencia

[Tu licencia aquí]

---

## 🎉 Conclusión

**py-v25-full.py** es un procesador completo y listo para usar que:

✅ Reproduce CSV grabados  
✅ Conecta Muse en vivo  
✅ Simula datos para testing  
✅ Envía a Processing/TouchDesigner  
✅ Calibra automáticamente  

**¡Listo para usar en producción!**

---

**Comienza ahora:**
```bash
cd /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc
python3 py-v25-full.py
```
