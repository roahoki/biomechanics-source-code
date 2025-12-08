# Sistema de Grabación de Datos de Meditación

## 📊 Descripción

El script ahora incluye la capacidad de grabar todas las variables de sensores en un archivo CSV para reproducir y analizar sesiones de meditación completas.

## 🎯 Características

### Grabación Automática
- ✅ Datos grabados cada **1 segundo** post-baseline
- ✅ Timestamps ISO 8601 para precisión temporal
- ✅ Información del baseline incluida como metadatos
- ✅ Nombres de archivo con timestamp: `meditacion_YYYYMMDD_HHMMSS.csv`

### Datos Capturados

#### Bandas EEG (si está habilitado)
```
delta_rms, delta_env, delta_cc
theta_rms, theta_env, theta_cc
alpha_rms, alpha_env, alpha_cc
beta_rms, beta_env, beta_cc
gamma_rms, gamma_env, gamma_cc
```

#### Acelerómetro (si está habilitado)
```
acc_x, acc_y, acc_z          # Valores crudos
acc_x_dev, acc_y_dev, acc_z_dev  # Desviaciones del baseline
```

#### PPG/Heartbeat (si está habilitado)
```
ppg_bpm      # BPM estimado
ppg_cc       # Control Change MIDI (0-127)
```

### Metadatos del Baseline
Al inicio del CSV, se incluyen comentarios con los datos del baseline:

```csv
# BASELINE DATA
# DELTA: μ=167.85 σ=3.25
# THETA: μ=46.12 σ=1.14
# ALPHA: μ=28.84 σ=0.67
# BETA: μ=32.87 σ=1.13
# GAMMA: μ=18.89 σ=1.28
# ACC_X: baseline=0.0835 range=[0.0197, 0.2460]
# ACC_Y: baseline=0.1606 range=[-0.4900, 0.6605]
# ACC_Z: baseline=0.9800 range=[0.7846, 0.9875]
# DATA START
timestamp,time_sec,delta_rms,delta_env,delta_cc,theta_rms,theta_env,theta_cc,...
```

## 🎬 Cómo Usar

### 1. Habilitar Grabación
```
=== SELECCIÓN DE FUENTE DE DATOS ===
0. Modo Simulador (Datos Falsos)
1. Solo Sensor Cerebral (Muse)
2. Salir
Selecciona una opción (0-2): 1

==================================================
    CONFIG OSC
    ► App Muse -> IP: 192.168.100.112 | Puerto: 5001
==================================================

--- Config Sensor Cerebral ---
¿Ondas? (s/n): s
¿Accel? (s/n): s
¿Heartbeat/PPG? (s/n): s
¿Guardar datos? (s/n): s   ← AQUÍ HABILITAR GRABACIÓN
⏱️  ¿Duración del baseline en segundos? (recomendado 10-30s, default=10): 10
```

### 2. Ejecutar Meditación
- El archivo se crea automáticamente al iniciarse la grabación
- Se graban datos cada 1 segundo después del baseline
- Al presionar Ctrl+C, el archivo se guarda automáticamente

### 3. Localizar Archivo
```
📁 Grabando datos en: meditacion_20251208_143050.csv
```

## 📈 Análisis de Datos

### Con Python/Pandas
```python
import pandas as pd

# Cargar datos
df = pd.read_csv('meditacion_20251208_143050.csv', comment='#')

# Información básica
print(df.head())
print(df.info())

# Estadísticas
print(df[['delta_rms', 'theta_rms', 'ppg_bpm']].describe())

# Gráficos
import matplotlib.pyplot as plt
df.plot(x='time_sec', y=['delta_env', 'theta_env', 'alpha_env'], figsize=(12, 6))
plt.show()
```

### Con Excel/Sheets
1. Abrir el CSV en Excel
2. Usar el timestamp para gráficos temporales
3. Análisis de correlación entre bandas EEG y PPG

## 🔧 Personalización

### Cambiar Intervalo de Grabación
En `DataRecorder.write_data()`, modificar:
```python
if now - self.last_write_time < 1.0:  # Cambiar 1.0 a otro valor en segundos
    return
```

### Agregar Nuevas Variables
En `DataRecorder._get_fieldnames()`, agregar campos:
```python
fields.extend(['nueva_var_1', 'nueva_var_2'])
```

Luego en `DataRecorder.write_data()`:
```python
row['nueva_var_1'] = variable.get('value', '')
```

### Cambiar Formato de Nombre
En `DataRecorder.__init__()`:
```python
filename = f"mi_nombre_{timestamp}.csv"  # Cambiar formato
```

## 📝 Estructura de Archivo

```
meditacion_20251208_143050.csv
├─ Líneas 1-10: Metadatos de baseline (comentarios)
├─ Línea 11: Header con nombres de columnas
├─ Línea 12+: Datos grabados cada 1 segundo
└─ Último registro: Al presionar Ctrl+C
```

## ⚠️ Notas Importantes

1. **Sin Baseline**: Si se deshabilita el baseline EEG, la grabación igual se inicia pero sin metadatos del baseline
2. **Sensor Desconectado**: Si el sensor se desconecta, las celdas vacías se guardan como vacías
3. **Archivo Abierto**: No intentar abrir el CSV mientras está siendo grabado
4. **Precisión Temporal**: Los timestamps son ISO 8601 con resolución de microsegundos

## 🐛 Troubleshooting

### "Error iniciando DataRecorder"
- Verificar permisos de escritura en el directorio actual
- Verificar espacio en disco disponible

### Archivo vacío o solo con headers
- Verificar que el baseline se completó correctamente
- Revisar que `baseline_done = True` después del baseline

### Columnas faltantes
- Verificar que los sensores están habilitados (s a las preguntas)
- Revisar que los datos llegan desde Muse

## 📊 Ejemplo de CSV Generado

```csv
# BASELINE DATA
# DELTA: μ=167.85 σ=3.25
# DATA START
timestamp,time_sec,delta_rms,delta_env,delta_cc,theta_rms,theta_env,theta_cc,acc_x,acc_y,acc_z,ppg_bpm,ppg_cc
2025-12-08T14:31:15.234567,0.0,171.215,0.0,0,47.122,0.0,0,0.0835,0.1606,0.98,70.0,64
2025-12-08T14:31:16.245123,1.0,169.426,0.15,6,47.718,0.42,18,0.0920,0.1750,0.97,71.5,65
2025-12-08T14:31:17.256789,2.0,168.834,0.19,8,46.494,0.39,17,0.0780,0.1480,0.99,69.8,63
...
```

---

**Estado**: ✅ Implementado y listo para usar
**Próximos pasos**: Ejecutar con grabación habilitada y analizar CSV generado
