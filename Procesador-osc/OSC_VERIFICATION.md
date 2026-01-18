# Verificación y Corrección de Envío OSC

## 🔧 Problema Identificado y Corregido

### Error en simulation_loop (CORREGIDO)

**Problema**: En la línea 1641, las variables estaban mal nombradas:
- Se usaba `osc_band_values_signed` pero se definía `osc_signed`
- Se usaba `osc_band_values_env` pero se definía `osc_env`
- Se usaba `osc_acc_values` pero se definía `osc_acc`
- Faltaba el envío de `bands_raw`

**Solución aplicada**:
```python
# Antes (INCORRECTO):
send_proc("/py/bands_signed_env", osc_band_values_signed, force=True)
send_proc("/py/bands_env", osc_band_values_env, force=True)
send_proc("/py/acc", osc_acc_values, force=True)

# Después (CORREGIDO):
send_proc("/py/bands_signed_env", osc_signed, force=True)
send_proc("/py/bands_env", osc_env, force=True)
send_proc("/py/bands_raw", osc_raw, force=True)  # ← AGREGADO
send_proc("/py/acc", osc_acc, force=True)
```

## ✅ Mensajes OSC que SE ESTÁN ENVIANDO

### Puerto: 5002 (127.0.0.1)
### IP Destino: TouchDesigner localhost

### 1. Datos EEG (Modo Promedio)
```
/py/bands_env           → [delta, theta, alpha, beta, gamma] (envelope)
/py/bands_signed_env    → [delta, theta, alpha, beta, gamma] (con signo)
/py/bands_raw           → [delta, theta, alpha, beta, gamma] (RMS crudo)
```

### 2. Datos EEG (Modo Multicanal) - NUEVO
```
/py/tp9/bands_env           → [delta, theta, alpha, beta, gamma]
/py/tp9/bands_signed_env    → [delta, theta, alpha, beta, gamma]
/py/tp9/bands_raw           → [delta, theta, alpha, beta, gamma]

/py/af7/bands_env           → [delta, theta, alpha, beta, gamma]
/py/af7/bands_signed_env    → [delta, theta, alpha, beta, gamma]
/py/af7/bands_raw           → [delta, theta, alpha, beta, gamma]

/py/af8/bands_env           → [delta, theta, alpha, beta, gamma]
/py/af8/bands_signed_env    → [delta, theta, alpha, beta, gamma]
/py/af8/bands_raw           → [delta, theta, alpha, beta, gamma]

/py/tp10/bands_env          → [delta, theta, alpha, beta, gamma]
/py/tp10/bands_signed_env   → [delta, theta, alpha, beta, gamma]
/py/tp10/bands_raw          → [delta, theta, alpha, beta, gamma]
```

### 3. Baseline EEG
```
/py/baseline/start          → [fase, duración]
/py/baseline/eeg/progress   → progreso (0-100)
/py/baseline/eeg/end        → [fase]
/py/baseline_mu             → [delta_μ, theta_μ, alpha_μ, beta_μ, gamma_μ]
/py/baseline_sigma          → [delta_σ, theta_σ, alpha_σ, beta_σ, gamma_σ]
/py/baseline_min            → [delta_min, theta_min, alpha_min, beta_min, gamma_min]
/py/baseline_max            → [delta_max, theta_max, alpha_max, beta_max, gamma_max]
```

### 4. Acelerómetro
```
/py/acc                     → [x, y, z] (valores actuales)
```

### 5. Baseline ACC
```
/py/baseline/acc_neutral/start      → [duración]
/py/baseline/acc_neutral/progress   → progreso (0-100)
/py/baseline/acc_movement/start     → [duración]
/py/baseline/acc_movement/progress  → progreso (0-100)
/py/baseline/acc/end                → [fase]

/py/acc_x_neutral          → valor neutral eje X
/py/acc_x_range            → rango de movimiento X
/py/acc_x_min              → valor mínimo X
/py/acc_x_max              → valor máximo X
/py/acc_x_sigma            → desviación estándar X

/py/acc_y_neutral          → valor neutral eje Y
/py/acc_y_range            → rango de movimiento Y
/py/acc_y_min              → valor mínimo Y
/py/acc_y_max              → valor máximo Y
/py/acc_y_sigma            → desviación estándar Y

/py/acc_z_neutral          → valor neutral eje Z
/py/acc_z_range            → rango de movimiento Z
/py/acc_z_min              → valor mínimo Z
/py/acc_z_max              → valor máximo Z
/py/acc_z_sigma            → desviación estándar Z
```

### 6. PPG (Heartbeat)
```
/py/ppg/bpm                → BPM estimado (60-140)
/py/ppg                    → valor raw del sensor
```

### 7. Giroscopio (si está habilitado)
```
/py/gyro                   → [x, y, z]
```

### 8. Jaw Clench (si está habilitado)
```
/py/jaw                    → 0 o 1 (clenched)
```

## 🔍 Cómo Verificar que Todo Funciona

### Paso 1: Ejecutar el Script de Diagnóstico

En una terminal, ejecuta:
```bash
cd /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc
/Users/tomas/Documents/GitHub/.venv/bin/python test_osc_receiver.py
```

### Paso 2: Ejecutar py-v26-multichannel

En otra terminal:
```bash
/Users/tomas/Documents/GitHub/.venv/bin/python /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc/py-v26-multichannel.py
```

Selecciona:
- Opción 0 (Simulador) o 1 (Sensor Real)
- Configuración según necesites

### Paso 3: Ver Diagnóstico

Después de ~10 segundos, presiona Ctrl+C en el script de diagnóstico.
Verás un resumen completo de todos los mensajes recibidos.

## 🎯 Configuración en TouchDesigner

### OSC In Operator (Principal)
```
Protocol: UDP
Network Address: 127.0.0.1
Port: 5002
```

### Para Modo Promedio (v24 compatible):
Crea un OSC In con:
- Active: ON
- Port: 5002
- Address Filter: `/py/*` o específicos como `/py/bands_*`, `/py/acc`

### Para Modo Multicanal:
Crea 4 OSC In adicionales (uno por canal):
1. **TP9**: Address Filter = `/py/tp9/*`
2. **AF7**: Address Filter = `/py/af7/*`
3. **AF8**: Address Filter = `/py/af8/*`
4. **TP10**: Address Filter = `/py/tp10/*`

## 📋 Checklist de Verificación

- [ ] Puerto 5002 está abierto (verificar con script de diagnóstico)
- [ ] py-v26-multichannel.py está ejecutándose sin errores
- [ ] En TD, OSC In muestra mensajes en el info CHOP (botón i)
- [ ] Los valores cambian en tiempo real
- [ ] Durante baseline, se reciben mensajes de progreso
- [ ] Después de baseline, se reciben datos continuos

## ⚠️ Troubleshooting

### Si no recibes NINGÚN mensaje:
1. Verifica que el puerto 5002 no esté en uso:
   ```bash
   lsof -i :5002
   ```
2. Verifica que no haya firewall bloqueando localhost
3. Reinicia TouchDesigner

### Si recibes algunos mensajes pero no todos:
1. Ejecuta el script de diagnóstico para ver exactamente qué llega
2. Verifica que el modo (promedio/individual) esté correctamente configurado
3. Revisa la consola de Python por errores

### Si los valores no cambian:
1. Verifica que el baseline haya completado
2. Verifica que `pause_outputs` no esté activado
3. Revisa que el sensor Muse esté transmitiendo (en modo live)

## 📊 Tasa de Actualización

- **EEG**: ~10 Hz (cada 100ms)
- **ACC**: ~10 Hz (cada 100ms)  
- **PPG**: Variable según detección de pulso
- **Baseline**: Eventos puntuales durante calibración

---

**Estado**: Código corregido ✅  
**Puerto confirmado**: 5002 ✅  
**Listo para probar**: ✅
