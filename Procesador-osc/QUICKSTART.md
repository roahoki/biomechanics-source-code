# 🎯 py-v25-full: Guía de Uso Rápido

## ¿Qué es?

`py-v25-full.py` es el script definitivo para procesar datos biomecánicos. Combina:
- **CSV Replay**: Reproducir datos grabados anteriormente
- **Sensor en Vivo**: Conectar Muse directamente
- **Simulador**: Generar datos falsos para testing

## 🚀 Empezar en 30 segundos

```bash
cd /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc
python3 py-v25-full.py
```

Luego selecciona:
- **0** para simular
- **1** para conectar Muse
- **2** para reproducir un CSV grabado

## 📊 Reproducir un CSV (Lo más común)

```bash
python3 py-v25-full.py

=== SELECCIÓN DE FUENTE DE DATOS ===
0. Modo Simulador (Datos Falsos)
1. Sensor Cerebral en Vivo (Muse)
2. Reproducir desde CSV            ← Elige ESTO
3. Salir

Selecciona una opción (0-3): 2

--- MODO REPRODUCCIÓN CSV ---

📊 Archivos CSV disponibles:

1. meditacion_20251219_194323.csv
   📅 2025-12-19 19:43:23 | 📈 2560 líneas | ⏱️  4m 16s | 📁 125.3KB

2. meditacion_20251217_215911.csv
   📅 2025-12-17 21:59:11 | 📈 1800 líneas | ⏱️  3m | 📁 87.2KB

Selecciona archivo (0-3): 1

Velocidad de reproducción (1.0=normal, 2.0=2x, 0.5=mitad, default=1.0): 1.5

✓ Archivo seleccionado: meditacion_20251219_194323.csv
✓ Velocidad: 1.5x
✓ Duración: 2m 50s (ajustada desde 4m 16s)

▶️  Reproducción iniciada (Ctrl+C para detener)

Progreso: [████████████      ] 65%
```

**Eso es todo!** Los datos se envían a Processing/TouchDesigner automáticamente.

## 🎛️ Modos Disponibles

### Modo 0: Simulador 🎲
Perfecto para testing sin hardware
```bash
# Genera ondas senoidales sin Muse
python3 py-v25-full.py → Selecciona 0
```

### Modo 1: Sensor Vivo 🧠
Conecta Muse directamente
```bash
# Requiere Muse enviando OSC a puerto 5001
python3 py-v25-full.py → Selecciona 1

# Te pedirá configuración:
¿Ondas? s
¿Accel? s  
¿Heartbeat/PPG? n
¿Guardar datos? n
⏱️ Duración baseline (10-30s, default=10): 10
```

### Modo 2: CSV Replay ⭐ (Recomendado)
Reproduce datos grabados previamente
```bash
python3 py-v25-full.py → Selecciona 2
```

## 🔍 Archivos CSV Disponibles

Todos los archivos `meditacion_*.csv` en esta carpeta se detectan automáticamente:

```
Procesador-osc/
├── meditacion_20251219_194323.csv     (2560 lineas)
├── meditacion_20251217_215911.csv     (1800 líneas)
├── meditacion_20251216_084530.csv     (950 líneas)
├── meditacion_20251216_084319.csv     (1200 líneas)
└── ... 10 archivos más
```

### ¿Cómo verlos?

El script te muestra:
- 📅 **Fecha/Hora**: Cuándo se grabó
- 📈 **Líneas**: Número de muestras
- ⏱️ **Duración**: Tiempo total
- 📁 **Tamaño**: En KB/MB

## 🔌 Integración con Processing/TouchDesigner

El script envía datos automáticamente a:
- **IP**: 127.0.0.1 (localhost)
- **Puerto**: 5002
- **Protocolo**: OSC/UDP

### Mensajes OSC que envía:

```
/py/bands_env [0.5, 0.8, 1.2, 0.9, 0.4]      # 5 bandas EEG
/py/bands_raw [1.0, 1.5, 2.0, 1.8, 0.9]      # RMS sin procesar
/py/acc [0.1, -0.05, 0.2]                     # Acelerómetro X,Y,Z
/py/ppg/bpm 72.5                              # BPM (si disponible)
```

### Setup en Processing:

```processing
import oscP5.*;

OscP5 oscP5;

void setup() {
  size(800, 600);
  oscP5 = new OscP5(this, 5002);
}

void oscEvent(OscMessage msg) {
  if (msg.checkAddrPattern("/py/bands_env")) {
    float[] bands = new float[5];
    for (int i = 0; i < 5; i++) {
      bands[i] = msg.get(i).floatValue();
    }
    println("EEG Bands: " + java.util.Arrays.toString(bands));
  }
}
```

## ⌨️ Atajos durante ejecución

Presiona **Ctrl+C** para parar en cualquier momento.

En Windows (adicionales):
- **Ctrl+B** → Recalibrar baseline
- **Ctrl+D** → Debug mode
- **Ctrl+R** → Toggle display
- **Ctrl+Q** → Salir

## 🐛 Troubleshooting

### "No se encuentran archivos CSV"
- ✓ Asegúrate de ejecutar desde el directorio correcto:
  ```bash
  cd /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc
  ```
- ✓ Los archivos deben llamarse `meditacion_*.csv`

### "Error de importación de librerías"
```bash
pip install numpy scipy python-osc pandas
```

### "No llegan datos a Processing"
- ✓ Verifica puerto 5002 libre: `lsof -i :5002`
- ✓ Comprueba IP en Processing es 127.0.0.1
- ✓ Revisa firewall

### CSV no se abre
- ✓ Verifica que existe el archivo
- ✓ Comprueba que no está en uso por otro programa
- ✓ Formato debe ser CSV estándar (comas)

## 📊 Formato CSV Esperado

Los archivos CSV deben tener estas columnas (mínimo):

```csv
timestamp,time_sec,delta_rms,delta_env,theta_rms,theta_env,alpha_rms,alpha_env,beta_rms,beta_env,gamma_rms,gamma_env,acc_x,acc_y,acc_z
2025-12-19T19:43:23.000,0.0,1.234,0.5,0.987,0.4,1.456,0.6,1.234,0.5,0.789,0.3,0.1,-0.05,0.2
```

Columnas detectadas automáticamente:
- ✅ EEG (delta, theta, alpha, beta, gamma)
- ✅ ACC (acc_x, acc_y, acc_z)
- ✅ PPG (ppg_bpm)
- ✅ Otras columnas se ignoran

## 💡 Tips Avanzados

### Reproducir a doble velocidad
```
Velocidad de reproducción (1.0=normal, 2.0=2x, 0.5=mitad, default=1.0): 2.0
```
Útil para testing rápido.

### Reproducir a media velocidad
```
Velocidad de reproducción (...): 0.5
```
Útil para análisis detallado.

### Ver info técnica
```bash
# Ver estructura del CSV
head -5 meditacion_20251219_194323.csv

# Contar líneas
wc -l meditacion_20251219_194323.csv

# Ver tamaño
ls -lh meditacion_20251219_194323.csv
```

## 🔄 Diferencias v24 vs v25-full

| Feature | v24 | v25-full |
|---------|-----|----------|
| Sensor Muse en vivo | ✅ | ✅ |
| CSV Replay | ❌ | ✅ |
| Simulador | ✅ | ✅ |
| Baseline calibración | ✅ | ✅ |
| Menú unificado | ❌ | ✅ |
| Detección automática sensores CSV | ❌ | ✅ |
| Control de velocidad replay | ❌ | ✅ |

## 📞 Próximas características

- [ ] Web UI para selección de CSV
- [ ] Batch processing (varios archivos)
- [ ] Export a formato diferente
- [ ] Real-time visualization
- [ ] Almacenamiento en cloud

## 📝 Notas

- El script detecta automáticamente tu IP local
- Los datos se procesan en tiempo real
- Baseline es automático en modo Muse (10-30 segundos)
- CSV replay no requiere baseline

---

**Versión**: 25-full  
**Compatible con**: Python 3.7+  
**Estado**: Production Ready ✅
