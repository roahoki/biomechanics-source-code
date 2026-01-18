# Guía de Uso: py-v26-multichannel.py

## 🎯 ¿Qué es nuevo?

El script **py-v26-multichannel.py** extiende py-v24.py con la capacidad de procesar **individualmente los 4 canales EEG** del dispositivo Muse 2:

- **TP9**: Temporal izquierdo posterior
- **AF7**: Frontal izquierdo anterior
- **AF8**: Frontal derecho anterior
- **TP10**: Temporal derecho posterior

## 🚀 Cómo usar

### 1. Iniciar el script

```bash
/Users/tomas/Documents/GitHub/.venv/bin/python /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc/py-v26-multichannel.py
```

### 2. Menú de selección

```
=== SELECCIÓN DE FUENTE DE DATOS ===
0. Modo Simulador (Datos Falsos)
1. Solo Sensor Cerebral (Muse)
2. Salir
Selecciona una opción (0-2): 1
```

### 3. Configurar el sensor

Cuando selecciones opción `1`, verás:

```
--- Config Sensor Cerebral ---
¿Ondas? (s/n): s
¿Procesar canales individuales? (s/n): s  ⬅️ NUEVA PREGUNTA
¿Accel? (s/n): s
¿Heartbeat/PPG? (s/n): n
¿Guardar datos? (s/n): n
```

#### Opciones de procesamiento:

- **s** (Sí): Modo **MULTICANAL** - Procesa TP9, AF7, AF8, TP10 por separado
- **n** (No): Modo **PROMEDIO** - Promedia los 4 canales (como en v24)

## 📡 Rutas OSC generadas

### Modo Promedio (compatible v24)

```
/py/bands_env          → [delta, theta, alpha, beta, gamma] (promedio de 4 canales)
/py/bands_signed_env   → [delta, theta, alpha, beta, gamma] con signo
/py/bands_raw          → [delta, theta, alpha, beta, gamma] valores RMS crudos
```

### Modo Multicanal (NUEVO)

**Canal TP9:**
```
/py/tp9/bands_env          → [delta, theta, alpha, beta, gamma] del canal TP9
/py/tp9/bands_signed_env   → [delta, theta, alpha, beta, gamma] con signo
/py/tp9/bands_raw          → [delta, theta, alpha, beta, gamma] RMS crudo
```

**Canal AF7:**
```
/py/af7/bands_env          → [delta, theta, alpha, beta, gamma] del canal AF7
/py/af7/bands_signed_env   → [delta, theta, alpha, beta, gamma] con signo
/py/af7/bands_raw          → [delta, theta, alpha, beta, gamma] RMS crudo
```

**Canal AF8:**
```
/py/af8/bands_env          → [delta, theta, alpha, beta, gamma] del canal AF8
/py/af8/bands_signed_env   → [delta, theta, alpha, beta, gamma] con signo
/py/af8/bands_raw          → [delta, theta, alpha, beta, gamma] RMS crudo
```

**Canal TP10:**
```
/py/tp10/bands_env         → [delta, theta, alpha, beta, gamma] del canal TP10
/py/tp10/bands_signed_env  → [delta, theta, alpha, beta, gamma] con signo
/py/tp10/bands_raw         → [delta, theta, alpha, beta, gamma] RMS crudo
```

## 🎭 Modo Simulador

El modo simulador **también soporta multicanal**. Si seleccionas procesamiento individual, generará datos simulados para los 4 canales con pequeñas variaciones de fase entre ellos.

## 🔍 Baseline en Modo Multicanal

Cuando activas el modo multicanal, el baseline se calcula **individualmente para cada canal**:

```
✨ Calculando baseline (modo: INDIVIDUAL)...

📡 Canal TP9:
  ✓ delta : μ=1.234 σ=0.456 [0.789, 1.987]
  ✓ theta : μ=0.987 σ=0.234 [0.567, 1.543]
  ✓ alpha : μ=1.123 σ=0.345 [0.678, 1.789]
  ✓ beta  : μ=0.876 σ=0.198 [0.456, 1.234]
  ✓ gamma : μ=0.654 σ=0.123 [0.345, 0.987]

📡 Canal AF7:
  ...
```

Cada canal tiene sus propias estadísticas de baseline (μ, σ, min, max).

## 📊 Configuración en TouchDesigner

### Para recibir datos multicanal:

1. Crea **4 OSC In operators** (uno por canal)
2. Configura cada uno con las rutas correspondientes:
   - OSC In 1: `/py/tp9/*`
   - OSC In 2: `/py/af7/*`
   - OSC In 3: `/py/af8/*`
   - OSC In 4: `/py/tp10/*`

3. Cada mensaje contendrá un array de 5 valores: `[delta, theta, alpha, beta, gamma]`

### Ejemplo de uso en TD:

```python
# Comparar actividad entre hemisferios
left_hemisphere = (tp9_alpha + af7_alpha) / 2
right_hemisphere = (af8_alpha + tp10_alpha) / 2
asymmetry = left_hemisphere - right_hemisphere
```

## 🎨 Casos de Uso

### 1. Visualización de Asimetría Hemisférica
- Compara AF7 (izquierda) vs AF8 (derecha)
- Detecta dominancia hemisférica en tiempo real

### 2. Análisis Espacial
- Frontal (AF7, AF8) vs Temporal (TP9, TP10)
- Detecta patrones de activación específicos

### 3. Coherencia entre Canales
- Calcula correlación entre canales
- Detecta sincronización neural

### 4. Mapeo Topográfico
- Crea mapas de calor con los 4 puntos
- Interpola valores entre canales

## ⚠️ Notas Importantes

1. **Formato de Datos del Muse**: El Muse 2 envía 1024 valores cuando transmite 4 canales (256 muestras × 4 canales)

2. **Modo Automático**: El script detecta automáticamente si los datos incluyen 4 canales

3. **Compatibilidad**: El modo promedio funciona exactamente igual que py-v24.py

4. **Rendimiento**: El modo multicanal requiere ~4x más procesamiento, pero sigue siendo en tiempo real

## 🐛 Troubleshooting

### "Solo recibo datos en modo promedio"
- Verifica que la aplicación Muse esté configurada para enviar los 4 canales
- Algunos dispositivos solo envían un canal compuesto por defecto

### "Los datos de canales se ven idénticos"
- Verifica la configuración del dispositivo Muse
- Asegúrate de que el contacto con la piel sea bueno en los 4 sensores

### "Error durante baseline multicanal"
- Asegúrate de mantener el dispositivo estable durante todo el baseline
- Verifica que todos los sensores tengan buen contacto

## 📝 Registro de Cambios desde v24

- ✅ Agregadas constantes `EEG_CHANNELS` y `EEG_CHANNEL_INDICES`
- ✅ Nueva variable `eeg_processing_mode` ('average' | 'individual')
- ✅ Estructuras de datos separadas: `bands_per_channel`, `eeg_buf_per_channel`
- ✅ Función `process_eeg_multichannel()` para procesamiento por canal
- ✅ Función `complete_baseline_phase()` con soporte multicanal
- ✅ Baseline individual por cada canal con estadísticas separadas
- ✅ Modo simulador actualizado para generar datos multicanal
- ✅ Rutas OSC individuales por canal

## 🎯 Próximos Pasos

1. Prueba con sensor real y verifica que recibes datos de los 4 canales
2. Configura TouchDesigner para recibir las nuevas rutas OSC
3. Experimenta con visualizaciones que aprovechen los datos espaciales
4. Considera agregar análisis de coherencia entre canales (futura implementación)

---

**Versión**: 26-multichannel  
**Basado en**: py-v24.py  
**Fecha**: Enero 2026
