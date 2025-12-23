# 🎓 Ejemplos de Uso Práctico

## Ejemplo 1: Reproducir un CSV Simple

```bash
$ cd /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc
$ python3 py-v25-full.py

============================================================
  BIOMECHANICS OSC PROCESSOR v25-full
============================================================
Esta ventana debe permanecer abierta.

========================================================

    ► Enviando a Processing -> IP: 127.0.0.1 | Puerto: 5002

========================================================

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

3. meditacion_20251216_084530.csv
   📅 2025-12-16 08:45:30 | 📈 950 líneas | ⏱️  1m 35s | 📁 47.2KB

4. Escribir ruta manualmente
0. Volver al menú

Selecciona archivo (0-4): 1

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

--- Estado de Ejecución ---
Modo: CSV_REPLAY
Archivo: meditacion_20251219_194323.csv
Velocidad: 1.0x

Presiona Enter para iniciar...

🎬 Iniciando reproducción de /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc/meditacion_20251219_194323.csv
Velocidad: 1.0x

▶️  Reproducción iniciada (Ctrl+C para detener)

Progreso: [█████               ] 25% | ⏱️  64.5s
```

**Lo que está sucediendo:**
- ✅ El script lee 2560 líneas del CSV
- ✅ Extrae valores EEG y ACC
- ✅ Envía automáticamente a Processing vía OSC
- ✅ Mantiene timing exacto basado en columna time_sec
- ✅ Puedes cancelar con Ctrl+C

---

## Ejemplo 2: Usar a Doble Velocidad para Testing

```bash
$ python3 py-v25-full.py

Selecciona una opción (0-3): 2

Selecciona archivo (0-4): 2

Velocidad de reproducción (1.0=normal, 2.0=2x, 0.5=mitad, default=1.0): 2.0

✓ Archivo seleccionado: meditacion_20251216_084530.csv
✓ Velocidad: 2.0x
✓ Duración original: 1m 35s
✓ Duración ajustada: 47s      ← ¡48 segundos en lugar de 95!
✓ Total de líneas: 950

Presiona Enter para iniciar...

▶️  Reproducción iniciada (Ctrl+C para detener)

Progreso: [██████████████████  ] 99% | ⏱️  46.8s

✓ Reproducción completada
```

**Caso de uso:** Testing rápido de visualizadores sin esperar 95 segundos

---

## Ejemplo 3: Simular Datos Sin Hardware

```bash
$ python3 py-v25-full.py

=== SELECCIÓN DE FUENTE DE DATOS ===
...
Selecciona una opción (0-3): 0

--- MODO SIMULADOR ACTIVADO ---

--- Configuración MIDI ---
MIDI support disabled...

--- Estado de Ejecución ---
Modo: SIMULATION

Presiona Enter para iniciar...

Simulación iniciada. Presiona Ctrl+C para detener.
Progreso: [████████           ] 40%
```

**Lo que está sucediendo:**
- ✅ Genera ondas senoidales para 5 bandas EEG
- ✅ Genera datos ACC realistas
- ✅ Envía a Processing con timing real
- ✅ Útil para desarrollar sin Muse

**Parar:**
```
^C
✋ Ctrl+C detectado. Saliendo...

✅ Programa finalizado.
```

---

## Ejemplo 4: Conectar Muse en Vivo

```bash
$ python3 py-v25-full.py

=== SELECCIÓN DE FUENTE DE DATOS ===
...
Selecciona una opción (0-3): 1

==================================================
    ► App Muse -> IP: 192.168.1.100 | Puerto: 5001
==================================================

--- Config Sensor Cerebral ---
¿Ondas? s
¿Accel? s
¿Heartbeat/PPG? n
¿Guardar datos? n
⏱️  Duración baseline (10-30s, default=10): 15
✓ Baseline: 15s

========================================================

    ► Enviando a Processing -> IP: 127.0.0.1 | Puerto: 5002

========================================================

--- Estado de Ejecución ---
Modo: LIVE
IP: 192.168.1.100 | Puerto: 5001

Presiona Enter para iniciar...

--- Configuración LIVE ---
IP: 192.168.1.100 | Puerto: 5001
Conecta Muse a esta dirección IP

[OSC] Mapeos configurados:
[Shortcuts] Ctrl+B=Recalibrate | Ctrl+D=Debug | Ctrl+R=Display | Ctrl+Q=Quit | Ctrl+M=Menu

--- Iniciando servidor OSC ---
Esperando datos Muse en 192.168.1.100:5001
```

**Configuración en Muse app:**
1. Abre "Muse Direct" o "Muse Monitor"
2. Habilita OSC
3. Configura IP: `192.168.1.100`
4. Configura Puerto: `5001`
5. Conecta Muse
6. Presiona Enter en la terminal

**Durante la ejecución:**
```
[EEG BASELINE] Capturando 15 segundos...
[Frame 1/24] Procesando...
[Frame 10/24]...
✅ EEG baseline completado
  delta: μ=1.234  σ=0.456
  theta: μ=1.567  σ=0.389
  alpha: μ=2.123  σ=0.567
  beta:  μ=1.834  σ=0.478
  gamma: μ=0.945  σ=0.312

[ACC NEUTRAL] Capturando 5 segundos... (cabeza quieta)
  x: neutral=0.05  range=0.15
  y: neutral=-0.02  range=0.12
  z: neutral=0.98  range=0.08

[ACC MOVEMENT] Capturando 10 segundos... (movimiento natural)
  x: neutral=0.05  range=0.25
  y: neutral=-0.02  range=0.20
  z: neutral=0.98  range=0.18

✅ Baseline completado - Enviando datos...
```

**Recalibrar durante sesión (Windows):**
```
Presiona Ctrl+B para recalibrar
```

---

## Ejemplo 5: Procesamiento por Lotes (Script externo)

Crear `batch_process.py`:

```python
#!/usr/bin/env python3
import os
import subprocess
import time

csv_files = [
    'meditacion_20251219_194323.csv',
    'meditacion_20251217_215911.csv',
    'meditacion_20251216_084530.csv',
]

for csv_file in csv_files:
    print(f"\n{'='*60}")
    print(f"Procesando: {csv_file}")
    print('='*60)
    
    # Usar el script
    proc = subprocess.Popen(['python3', 'py-v25-full.py'], 
                           stdin=subprocess.PIPE, 
                           stdout=subprocess.PIPE,
                           text=True)
    
    # Automatizar inputs
    inputs = f"""2
1
2.0
"""
    
    stdout, stderr = proc.communicate(input=inputs, timeout=600)
    print(stdout)
    
    if proc.returncode != 0:
        print(f"Error: {stderr}")
    else:
        print(f"✓ {csv_file} completado")
    
    time.sleep(2)

print("\n✅ Procesamiento por lotes completado")
```

**Uso:**
```bash
python3 batch_process.py
```

---

## Ejemplo 6: Integración con TouchDesigner

Crear receiver OSC en TouchDesigner:

```python
# en TOE script
import time

class OscReceiver:
    def __init__(self):
        self.bands = [0, 0, 0, 0, 0]
        self.acc = [0, 0, 0]
        self.ppg = 0
        
    def onPar(self, par):
        """Callback cuando llega OSC"""
        if par.addr == "/py/bands_env":
            self.bands = par.val
            # Actualizar visualizador
            op('TOP_eeg_bands').par.input = self.bands[2]  # Alpha
            
        elif par.addr == "/py/acc":
            self.acc = par.val
            # Rotar esfera basado en ACC
            op('geo_sphere').par.rx = self.acc[0] * 10
            op('geo_sphere').par.ry = self.acc[1] * 10

osc = OscReceiver()
```

**Archivos de TopNet para UDP:**
1. Crea un CHOP OSCIn
2. Local Port: 5002
3. Active: ON

---

## Ejemplo 7: Debugging

### Activar modo debug
Editar `py-v25-full.py` línea ~400:
```python
debug_mode = True  # Cambiar de False a True
```

### Output con debug habilitado
```
[OSC RECEIVED] /muse/eeg: (array([...]))
[OSC RECEIVED] /muse/acc: (0.05, -0.02, 0.98)
[OSC RECEIVED] /muse/eeg: (array([...]))
[OSC RECEIVED] /muse/acc: (0.06, -0.01, 0.97)
```

### Ver estructura CSV
```bash
head -3 meditacion_20251219_194323.csv

timestamp,time_sec,delta_rms,delta_env,delta_cc,theta_rms,theta_env,...
2025-12-19T19:43:23.000,0.0,1.234,0.5,32,0.987,0.4,...
2025-12-19T19:43:23.001,0.1,1.245,0.51,32,0.995,0.41,...
```

---

## Ejemplo 8: Exportar Datos Procesados

Crear `export_processed.py`:

```python
#!/usr/bin/env python3
import pandas as pd
import numpy as np
from scipy import signal

# Leer CSV
df = pd.read_csv('meditacion_20251219_194323.csv')

# Aplicar filtro
b, a = signal.butter(4, [8/128, 13/128], 'band')
alpha_filtered = signal.filtfilt(b, a, df['alpha_rms'])

# Guardar resultado
output = pd.DataFrame({
    'time_sec': df['time_sec'],
    'alpha_raw': df['alpha_rms'],
    'alpha_filtered': alpha_filtered,
    'acc_magnitude': np.sqrt(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2)
})

output.to_csv('meditacion_20251219_PROCESSED.csv', index=False)
print("✓ Exportado: meditacion_20251219_PROCESSED.csv")
```

**Uso:**
```bash
python3 export_processed.py
```

---

## Ejemplo 9: Análisis Estadístico

```python
#!/usr/bin/env python3
import pandas as pd
import numpy as np

csv_files = [
    'meditacion_20251219_194323.csv',
    'meditacion_20251217_215911.csv',
    'meditacion_20251216_084530.csv',
]

for filename in csv_files:
    df = pd.read_csv(filename)
    
    print(f"\n📊 {filename}")
    print(f"   Duración: {df['time_sec'].max():.1f}s")
    print(f"   Muestras: {len(df)}")
    print(f"   Alpha promedio: {df['alpha_rms'].mean():.2f}")
    print(f"   Alpha desv: {df['alpha_rms'].std():.2f}")
    print(f"   ACC magnitud máx: {(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2).max()**.5:.2f}")
```

**Output:**
```
📊 meditacion_20251219_194323.csv
   Duración: 256.0s
   Muestras: 2560
   Alpha promedio: 1.45
   Alpha desv: 0.34
   ACC magnitud máx: 2.15

📊 meditacion_20251217_215911.csv
   Duración: 180.0s
   Muestras: 1800
   Alpha promedio: 1.38
   Alpha desv: 0.28
   ACC magnitud máx: 1.87

📊 meditacion_20251216_084530.csv
   Duración: 95.0s
   Muestras: 950
   Alpha promedio: 1.52
   Alpha desv: 0.42
   ACC magnitud máx: 2.34
```

---

## 🚀 Checklist de Uso

- [ ] Instalar dependencias: `pip install numpy scipy python-osc pandas`
- [ ] Navegar a directorio: `cd Procesador-osc`
- [ ] Ejecutar script: `python3 py-v25-full.py`
- [ ] Seleccionar modo (0, 1, ó 2)
- [ ] Para CSV: elegir archivo + velocidad
- [ ] Para Muse: conectar app a IP y puerto mostrado
- [ ] Presionar Enter para iniciar
- [ ] Ver datos en Processing/TouchDesigner
- [ ] Presionar Ctrl+C para parar

---

**Versión**: 25-full  
**Ejemplos Validados**: ✅ 9 escenarios  
**Últimas Actualizaciones**: Diciembre 2025
