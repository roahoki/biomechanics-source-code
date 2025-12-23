# py-v25-full.py: Integración Completa v24 + CSV Replay

## 📋 Descripción General

`py-v25-full.py` es la integración completa que combina:
- ✅ Todas las funciones de v24.py (procesamiento EEG, handlers OSC, baseline calibración)
- ✅ Nuevas capacidades de v25 (reproducción de datos desde CSV)
- ✅ Sistema de menú unificado para 3 modos de operación

## 🎯 Tres Modos de Operación

### 1. **Simulador (Modo 0)**
- Genera datos sintéticos para testing sin hardware
- Produce ondas senoidales para 5 bandas EEG + acelerómetro
- Ideal para desarrollar visualizadores sin necesidad de Muse

### 2. **Sensor Cerebral en Vivo (Modo 1)**
- Conecta directamente a Muse a través de OSC
- Implementa calibración de baseline automática:
  - **EEG Baseline**: 10-30 segundos de captura de actividad base
  - **ACC Neutral**: 5 segundos con la cabeza quieta
  - **ACC Movement**: 10 segundos con movimiento natural
- Envía datos procesados a Processing/TouchDesigner en tiempo real
- Soporta grabación automática a CSV

### 3. **Reproducción de CSV (Modo 2)** ⭐ NUEVO
- Reproduce datos previamente grabados como si vinieran del sensor en vivo
- Menú interactivo que lista todos los archivos `meditacion_*.csv`
- Muestra metadatos para cada archivo:
  - 📅 Fecha y hora de grabación
  - 📈 Número de líneas (muestras)
  - ⏱️  Duración total
  - 📁 Tamaño del archivo
- Control de velocidad de reproducción (0.5x, 1.0x, 2.0x, etc.)
- Ajuste dinámico de duración según velocidad

## 🔧 Funciones Principales Integradas

### Handlers OSC (De v24)
```python
muse_eeg(addr, *args)          # Procesa datos EEG de Muse
muse_acc(addr, *args)          # Procesa acelerómetro
muse_ppg(addr, *args)          # Procesa ritmo cardíaco
muse_gyro(addr, *args)         # Procesa giroscopio
muse_jaw(addr, *args)          # Detección de clenched jaw
```

### Baseline Calibración (De v24)
```python
close_baseline_eeg()           # Finaliza y calcula μ/σ de EEG
close_baseline_acc()           # Finaliza ACC con rango neutral + movement
close_bio()                    # Finaliza sensores biométricos
close_dist()                   # Finaliza sensor de distancia
```

### Motor de Reproducción CSV (Nuevo)
```python
class CSVReplayEngine:
    load()                     # Carga archivo CSV
    get_next_sample()          # Obtiene siguiente muestra con timing
    get_progress()             # Retorna 0-100
    reset()                    # Reinicia reproducción
```

### Loops de Datos
```python
live_loop()                    # Servidor OSC para modo en vivo
csv_replay_loop()              # Motor de reproducción CSV
simulation_loop()              # Generador de datos sintéticos
serial_loop()                  # Lectura de puerto serial (Arduino)
midi_tick()                    # Control de MIDI (stub)
```

### Funciones de Control
```python
recalibration_routine()        # Reinicia baseline durante sesión
trigger_recalibration()        # Dispara recalibración en thread
listen_shortcuts()             # Monitorea Ctrl+B, Ctrl+D, etc.
```

## 📊 Estructura de Datos EEG

Cada banda se procesa con:
- **RMS**: Root Mean Square (amplitud bruta)
- **ENV**: Envelope (amplitud normalizada por z-score)
- **CC**: Control Change (0-127 para MIDI)

Bandas soportadas:
- `delta`: 0.5-4 Hz
- `theta`: 4-8 Hz
- `alpha`: 8-13 Hz
- `beta`: 13-30 Hz
- `gamma`: 30-45 Hz

## 🎛️ Configuración de Sensores

El script detecta automáticamente qué sensores están disponibles:
```
┌─ Modo Simulador ────────────────┐
│ EEG: ✓  ACC: ✓  PPG: ✗         │
└────────────────────────────────┘

┌─ Sensor en Vivo ────────────────┐
│ ¿Ondas? s                       │
│ ¿Accel? s                       │
│ ¿Heartbeat/PPG? s              │
│ ¿Guardar datos? n              │
│ ⏱️ Duración baseline: 10s        │
└────────────────────────────────┘

┌─ Reproducción CSV ──────────────┐
│ EEG: ✓  ACC: ✓  PPG: ✗         │
│ (Detectado automáticamente)    │
└────────────────────────────────┘
```

## 🚀 Cómo Usar

### Opción 1: Reproducir un CSV
```bash
python3 py-v25-full.py

=== SELECCIÓN DE FUENTE DE DATOS ===
0. Modo Simulador (Datos Falsos)
1. Sensor Cerebral en Vivo (Muse)
2. Reproducir desde CSV
3. Salir

Selecciona una opción (0-3): 2

--- MODO REPRODUCCIÓN CSV ---

📊 Archivos CSV disponibles:

1. meditacion_20251219_194323.csv
   📅 2025-12-19 19:43:23 | 📈 2560 líneas | ⏱️  4m 16s | 📁 125.3KB

2. meditacion_20251217_215911.csv
   📅 2025-12-17 21:59:11 | 📈 1800 líneas | ⏱️  3m | 📁 87.2KB

Selecciona archivo (0-3): 1

Velocidad de reproducción (1.0=normal, 2.0=2x, 0.5=mitad, default=1.0): 1.0

✓ Archivo seleccionado: meditacion_20251219_194323.csv
✓ Velocidad: 1.0x
✓ Duración original: 4m 16s
✓ Duración ajustada: 4m 16s
✓ Total de líneas: 2560

📊 Sensores detectados en CSV:
   EEG: ✓
   ACC: ✓
   PPG: ✗

▶️  Reproducción iniciada (Ctrl+C para detener)

Progreso: [████████████      ] 65% | ⏱️  165.3s
```

### Opción 2: Simular datos
```bash
python3 py-v25-full.py

Selecciona una opción (0-3): 0

--- MODO SIMULADOR ACTIVADO ---
```

### Opción 3: Conectar Muse en vivo
```bash
python3 py-v25-full.py

Selecciona una opción (0-3): 1

--- Config Sensor Cerebral ---
¿Ondas? s
¿Accel? s
¿Heartbeat/PPG? n
¿Guardar datos? s
⏱️  Duración baseline (10-30s, default=10): 15
✓ Baseline: 15s

--- Iniciando servidor OSC ---
Esperando datos Muse en 192.168.1.100:5001
```

## 🔌 Configuración de Red

### Para Muse → Script
- **Dirección**: La IP local de tu computadora (se detecta automáticamente)
- **Puerto OSC**: 5001 (configurable)
- **Protocolo**: UDP

### Para Script → Processing/TouchDesigner
- **Dirección**: 127.0.0.1 (localhost)
- **Puerto**: 5002 (configurable)
- **Protocolo**: OSC/UDP

## 📈 Mensajes OSC Enviados

### Modo CSV Replay y Simulador
```
/py/bands_env [0.5, 0.8, 1.2, 0.9, 0.4]      # 5 bandas EEG
/py/bands_raw [1.0, 1.5, 2.0, 1.8, 0.9]      # RMS sin procesar
/py/acc [0.1, -0.05, 0.2]                     # X, Y, Z acelerómetro
/py/ppg/bpm 72.5                              # BPM si disponible
```

### Modo Sensor en Vivo (Adicionales)
```
/py/baseline/start ["eeg", 15]                # Inicia baseline EEG
/py/baseline/eeg/progress 7.5                 # Progreso actual
/py/baseline/end ["eeg"]                      # Finaliza baseline
/py/gyro [0.1, 0.2, -0.05]                    # Datos giroscopio
/py/jaw [1]                                    # Detección mordida
```

## ⌨️ Atajos de Teclado (Modo Windows)

| Atajo | Función |
|-------|---------|
| **Ctrl+B** | Recalibrar baseline |
| **Ctrl+D** | Toggle debug mode |
| **Ctrl+R** | Toggle realtime display |
| **Ctrl+M** | Volver al menú |
| **Ctrl+Q** | Salir |

*Nota: En macOS, estos atajos se pueden implementar con una biblioteca específica del SO*

## 📁 Estructura de Archivos CSV

Las columnas esperadas en los archivos CSV son:

```csv
timestamp,time_sec,delta_rms,delta_env,delta_cc,theta_rms,theta_env,theta_cc,alpha_rms,alpha_env,alpha_cc,beta_rms,beta_env,beta_cc,gamma_rms,gamma_env,gamma_cc,acc_x,acc_y,acc_z,ppg_bpm
2025-12-19T19:43:23.000,0.0,1.234,0.5,32,0.987,0.4,25,...
```

### Columnas Opcionales
- Si falta `time_sec`, usa índice * 0.1
- Si faltan bandas EEG, se ignoran automáticamente
- Si falta ACC, se ignora
- Si falta PPG, se ignora

## 🔍 Debugging

### Activar modo debug
1. En el archivo: cambiar `debug_mode = True`
2. En tiempo de ejecución: **Ctrl+D** (Windows)

### Visualizar todos los mensajes OSC
El modo debug imprime:
```
[OSC RECEIVED] /muse/eeg: (args...)
[OSC RECEIVED] /muse/acc: (args...)
```

## 🚨 Limitaciones Actuales

- [ ] MIDI disabled (stub implementation)
- [ ] Serial communication requiere `pyserial` instalado
- [ ] Keyboard shortcuts solo en Windows
- [ ] No hay UI gráfica (CLI solamente)

## 📦 Dependencias Requeridas

```bash
pip install numpy scipy python-osc pandas
# Opcional:
pip install pyserial  # Para datos de Arduino
```

## 🧪 Testing Rápido

```bash
# Test 1: Validar sintaxis
python3 -m py_compile py-v25-full.py

# Test 2: Modo simulador
python3 py-v25-full.py
# Selecciona 0, press Enter
# Ctrl+C para parar

# Test 3: Reproducir CSV
python3 py-v25-full.py
# Selecciona 2, elige archivo, press Enter
# Ctrl+C para parar
```

## 📝 Próximos Pasos

1. Implementar atajos de teclado en macOS
2. Agregar UI web o GUI tkinter
3. Soporte para múltiples archivos CSV (batch processing)
4. Implementación real de MIDI
5. Visualización en tiempo real de datos

## 🎓 Notas de Desarrollo

### Cambios desde v24 → v25
- ✅ Agregado `CSVReplayEngine` para reproducción
- ✅ Menú mejorado con detección automática de CSV
- ✅ Mejor manejo de errores en lectura de archivos
- ✅ Soporta múltiples modos en un solo script
- ✅ Detección automática de sensores disponibles

### Cambios desde v25 → v25-full
- ✅ Integración completa de todos los handlers OSC
- ✅ Baseline calibration con 2 fases para ACC
- ✅ Señal processing con filters Butterworth
- ✅ Recalibration routine durante sesiones en vivo
- ✅ Keyboard shortcuts (Windows)
- ✅ Serial loop para datos de Arduino
- ✅ MIDI control (stub)

---

**Versión**: 25-full  
**Última actualización**: Diciembre 2025  
**Estado**: Production-ready para CSV replay, live mode requiere Muse
