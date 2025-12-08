# Descripción del Código: py-v24.py

## Resumen General
Script Python para capturar datos biométricos del headset Muse 2 vía OSC, procesarlos en tiempo real y enviarlos a TouchDesigner para control visual/audio. Incluye calibración baseline automática, grabación CSV opcional y soporte para Arduino.

**Versión**: v24  
**Estado**: Producción (con ajustes en progreso)  
**Dependencias**: numpy, scipy, python-osc

---

## Flujo Principal

### 1. Inicialización
- Detección de IP local automática
- Menú de selección: Simulador (0), Muse Real (1), o Salir (2)
- Configuración de sensores: EEG, Acelerómetro (ACC), PPG, Giroscopio, Mandíbula
- Opción de grabación CSV con timestamp automático

### 2. Baseline Calibration (si se habilita EEG)
Secuencia de 3 fases (tiempos configurables):

**Fase 0: EEG Baseline (configurable 10-30s por defecto)**
- Captura señal EEG descompuesta en 5 bandas (Delta, Theta, Alpha, Beta, Gamma)
- Calcula media (μ) y desviación estándar (σ) de cada banda
- Almacena en diccionario global `bands[band]['mu']` y `bands[band]['sd']`

**Fase 1: ACC Neutral (5s)**
- Usuario mantiene cabeza en posición estática
- Registra rango de valores "neutral" por eje (x, y, z)

**Fase 2: ACC Movement (10s)**
- Usuario mueve cabeza en todas direcciones
- Registra rango completo de movimiento

### 3. Captura de Datos en Tiempo Real
OSC handlers mapean datos desde Muse:
- `/desdemuse/eeg` → `muse_eeg()` → 5 bandas de frecuencia
- `/desdemuse/acc` → `muse_acc()` → Aceleración 3D + desviación del baseline
- `/desdemuse/ppg` → `muse_ppg()` → Ritmo cardíaco (BPM) con algoritmo basado en varianza
- `/desdemuse/gyro` → `muse_gyro()` → Velocidad angular (sin implementar)
- `/desdemuse/jaw` → `muse_jaw()` → Detección de movimiento mandíbula (sin implementar)

### 4. Algoritmos Principales

#### PPG → BPM Conversion (Actual)
```python
- Mantiene buffer de 10 últimas muestras PPG
- Calcula desviación estándar del buffer
- Fórmula: BPM = 60 + ((std_dev / 300000) * 80)
- Rango: 60-140 BPM (clamped)
```
**Nota**: No coincide exactamente con ritmo cardiaco real. Requiere calibración futura con cardiómetro de referencia.

#### ACC Deviation Mapping
```python
- Desviación = (valor_actual - posición_neutral) / rango_movimiento
- Normalizado a rango [0-127] para MIDI/OSC
- Enviado como control change (CC)
```

### 5. Envío de Datos a TouchDesigner
Dos interfaces OSC:
- **Entrada**: 0.0.0.0:5001 (desde Muse)
- **Salida**: 127.0.0.1:5002 (hacia TouchDesigner)

Mensajes enviados en tiempo real:
```
/py/bands_raw1-5      → EEG raw (5 bandas)
/py/bands_env1-5      → EEG envelope (suavizado)
/py/bands_cc1-5       → EEG control change (0-127)
/py/baseline_mu1-5    → Baseline EEG (post-calibración)
/py/acc                → Aceleración bruta (x, y, z)
/py/acc_cc_x/y/z      → ACC control change (0-127)
/py/ppg                → PPG raw
/py/ppg/bpm            → BPM calculado
```

### 6. Grabación de Datos (CSV)
**Archivo**: `meditacion_YYYYMMDD_HHMMSS.csv`

**Estructura**:
- Encabezado: nombres de columnas (timestamp, EEG bands, ACC, PPG, etc.)
- Comentarios: Baseline metadata (μ, σ, rangos ACC)
- Datos: 1 fila por segundo durante grabación

**Guardado**: Carpeta raíz del script (./meditacion_*.csv)

---

## Variables Globales Importantes

### Baseline (EEG)
```python
bands[band] = {
    'buf': deque,          # Buffer de muestras
    'mu': float,           # Media (calculada post-baseline)
    'sd': float,           # Desviación estándar
    'raw': float,          # Último valor raw
    'env': float,          # Envelope (suavizado)
    'cc': int              # Control change (0-127)
}
```

### Baseline (ACC) - EN CONSTRUCCIÓN
Pendiente: Variables separadas `baseline_acc_x`, `baseline_acc_y`, `baseline_acc_z` con estructura:
```python
baseline_acc_x = {
    'neutral': float,      # Valor neutral calibrado
    'min': float,          # Mínimo movimiento
    'max': float,          # Máximo movimiento
    'range': float         # Rango total
}
```

### Rangos de Normalización ACC
```python
acc_rng = {
    'x': {'min': float, 'max': float, 'neutral_min': float, 'neutral_max': float},
    'y': {...},
    'z': {...}
}
```

### PPG
```python
ppg_buffer = deque(10)     # Últimas 10 muestras
last_ppg_value = float     # PPG raw
ppg_bpm = float            # BPM calculado
ppg_cc = int               # CC normalizado (0-127)
```

---

## Modo Simulador

Genera datos falsos para testing sin headset Muse:
- EEG: Ondas sinusoidales con ruido aleatorio
- ACC: Valores oscilantes
- PPG: Simulación de latidos cardíacos

Útil para debug de TouchDesigner sin hardware.

---

## Atajos de Teclado

- **Ctrl+B**: Reenviar datos de baseline (μ/σ EEG) a TouchDesigner
- **Ctrl+C**: Parar ejecución, cerrar archivos CSV

---

## Problemas Conocidos / En Desarrollo

### 1. BPM PPG ⚠️ (DOCUMENTADO)
- Algoritmo actual no coincide con ritmo cardiaco real
- Requiere calibración con sensor cardíaco de referencia
- **Status**: Mantener así por ahora; mejora futura
- Ver archivo `PPG_BPM_INTEGRATION.md` para detalles técnicos

### 2. Variables de Baseline ACC ✅ RESUELTO
- ~~No se exportaban `baseline_acc_x/y/z` a TouchDesigner~~
- **Solución**: Agregadas variables globales separadas por eje
- Ahora se envía: `neutral`, `min`, `max`, `range` para cada eje
- Actualizable con Ctrl+B junto con baseline EEG

### 3. Opciones de Sensor Individual ✅ RESUELTO
- ~~Seleccionar solo ACC + PPG (sin EEG) no funcionaba~~
- **Causa**: Lógica de baseline requería `use_eeg and use_acc` simultáneos
- **Solución**:
  - Separado ACC baseline de EEG baseline (línea 650-654)
  - Modificado `baseline_done` para ser True cuando ALL baselines completos (línea 665)
  - Actualizado `muse_acc()` para permitir baseline sin EEG (línea 938-949)

### 4. Error NoneType en CSV Baseline Metadata ✅ RESUELTO
- ~~Al seleccionar solo ACC/PPG (sin EEG), el CSV fallaba~~
- **Causa**: Intento de acceso a `bands[band]['mu']` cuando era None durante baseline
- **Solución**:
  - Agregar `baseline_eeg_values` dict para almacenar valores post-baseline (línea 616)
  - Modificar `write_baseline_metadata()` para usar valores guardados, no acceso directo a `bands` (línea 249-278)
  - Llamar a función solo después de que `baseline_done = True` desde main loop (línea 1552-1554)

---

## Estructura de Archivos

```
Procesador-osc/
├── py-v24.py                      # Script principal
├── meditacion_YYYYMMDD_HHMMSS.csv # Archivos de grabación (generados)
├── DATA_RECORDING.md              # Documentación grabación CSV
├── PPG_BPM_INTEGRATION.md          # Documentación PPG/BPM
└── CODE_DESCRIPTION.md             # Este archivo
```

---

## Siguientes Pasos

1. ✅ Arreglar variables globales baseline ACC
2. ✅ Implementar envío de rangos ACC a TouchDesigner (Ctrl+B)
3. ✅ Arreglar opciones de sensor individual
4. ✅ Documentar cambios en CODE_DESCRIPTION.md
5. ⚠️ Calibración PPG con cardiómetro de referencia (futuro)
6. ⚠️ Implementar giroscopio y mandíbula (futuro)

---

**Última actualización**: 8 de Diciembre de 2025
