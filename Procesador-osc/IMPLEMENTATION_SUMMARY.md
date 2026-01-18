# Resumen de Implementación: Soporte Multicanal Muse 2

## ✅ Cambios Implementados

### 1. Estructuras de Datos
- ✅ Agregadas constantes `EEG_CHANNELS = ['TP9', 'AF7', 'AF8', 'TP10']`
- ✅ Variable global `eeg_processing_mode` ('average' o 'individual')
- ✅ Diccionario `bands_per_channel` para almacenar datos por canal
- ✅ Buffers individuales `eeg_buf_per_channel` para cada canal
- ✅ `baseline_eeg_values_per_channel` para estadísticas de baseline por canal

### 2. Funciones Nuevas/Modificadas

#### `muse_eeg(_, *vals)`
- Detecta automáticamente si hay datos de 4 canales (1024 valores)
- Redirige a `process_eeg_multichannel()` o `process_eeg_average()`

#### `process_eeg_multichannel(vals)` (NUEVA)
- Divide los 1024 valores en 4 canales de 256 muestras cada uno
- Procesa cada canal independientemente
- Aplica filtros de bandas de frecuencia por canal
- Calcula RMS, envelope y z-scores individuales
- Envía datos por rutas OSC separadas: `/py/tp9/*`, `/py/af7/*`, etc.

#### `process_eeg_average()` (NUEVA)
- Modo compatible con v24
- Promedia todos los valores recibidos
- Procesa como un único canal
- Mantiene rutas OSC originales: `/py/bands_env`, etc.

#### `complete_baseline_phase()` (NUEVA)
- Maneja baseline para ambos modos
- En modo individual: calcula μ, σ, min, max para cada canal
- En modo promedio: calcula estadísticas globales
- Muestra progreso con barra visual

#### `simulation_loop()` (MODIFICADA)
- Genera datos simulados para modo promedio
- Si modo individual: genera 4 canales con variaciones de fase
- Envía datos por todas las rutas OSC correspondientes

### 3. Menú de Configuración
- ✅ Nueva pregunta: "¿Procesar canales individuales? (s/n)"
- ✅ Mensaje de confirmación del modo seleccionado
- ✅ Actualizado en modo simulador y sensor en vivo

### 4. Rutas OSC

#### Modo Promedio (v24 compatible):
```
/py/bands_env
/py/bands_signed_env
/py/bands_raw
/py/baseline_mu
```

#### Modo Multicanal (NUEVO):
```
/py/tp9/bands_env
/py/tp9/bands_signed_env
/py/tp9/bands_raw
/py/af7/bands_env
/py/af7/bands_signed_env
/py/af7/bands_raw
/py/af8/bands_env
/py/af8/bands_signed_env
/py/af8/bands_raw
/py/tp10/bands_env
/py/tp10/bands_signed_env
/py/tp10/bands_raw
```

Cada mensaje contiene array de 5 valores: `[delta, theta, alpha, beta, gamma]`

### 5. Baseline por Canal

En modo multicanal, cada canal tiene sus propias estadísticas:
```python
baseline_eeg_values_per_channel = {
    'TP9': {
        'delta': {'mu': X, 'sigma': Y, 'min': Z, 'max': W},
        'theta': {'mu': X, 'sigma': Y, 'min': Z, 'max': W},
        ...
    },
    'AF7': {...},
    'AF8': {...},
    'TP10': {...}
}
```

## 🧪 Estado de Testing

- ✅ Sintaxis validada
- ✅ Imports correctos
- ✅ Modo simulador funcional (promedio + multicanal)
- ⏳ Pendiente: Prueba con sensor Muse real

## 📋 Para Probar con Sensor Real

1. **Inicia el script**:
```bash
/Users/tomas/Documents/GitHub/.venv/bin/python /Users/tomas/Documents/GitHub/biomechanics-source-code/Procesador-osc/py-v26-multichannel.py
```

2. **Selecciona**:
   - Opción `1` (Sensor Cerebral)
   - Ondas: `s`
   - **Procesar canales individuales: `s`** ⬅️ IMPORTANTE
   - Accel: según necesites
   - PPG: según necesites
   - Guardar: según necesites

3. **Verifica en la consola**:
   - Debe aparecer: "Modo EEG: INDIVIDUAL"
   - Durante baseline: "Calculando baseline (modo: INDIVIDUAL)..."
   - Verás estadísticas por cada canal: TP9, AF7, AF8, TP10

4. **En TouchDesigner**:
   - Configura OSC In para recibir `/py/tp9/*`, `/py/af7/*`, etc.
   - Deberías ver 4 streams de datos independientes

## ⚙️ Configuración del Muse

**Importante**: Asegúrate de que tu aplicación Muse esté configurada para enviar los 4 canales individuales:

- Algunas apps envían solo un canal combinado (256 valores)
- Para modo multicanal necesitas 4 canales × 256 = 1024 valores
- El script detecta automáticamente el formato y ajusta el procesamiento

## 🎯 Beneficios del Modo Multicanal

1. **Análisis Espacial**: Ver diferencias entre regiones cerebrales
2. **Asimetría Hemisférica**: Comparar izquierda vs derecha
3. **Detección de Patrones**: Identificar activación específica por zona
4. **Visualización Avanzada**: Mapas de calor, interpolación espacial
5. **Investigación**: Datos más ricos para análisis científico

## 📁 Archivos Creados/Modificados

1. **py-v26-multichannel.py** - Script principal con soporte multicanal
2. **MULTICHANNEL_CHANGES.md** - Documentación técnica de cambios
3. **README_MULTICANAL.md** - Guía de uso completa
4. **IMPLEMENTATION_SUMMARY.md** - Este archivo (resumen de implementación)

## 🔄 Compatibilidad

- ✅ 100% compatible con py-v24.py en modo promedio
- ✅ Mantiene todas las funciones: ACC, PPG, baseline, grabación CSV
- ✅ Modo simulador funcional en ambos modos
- ✅ Sin cambios en la lógica de baseline ACC o otros sensores

## 📞 Troubleshooting

**Si no ves datos multicanal:**
1. Verifica que el Muse envíe 1024 valores (no 256)
2. Confirma que seleccionaste "Procesar canales individuales: s"
3. Revisa que debug_mode esté activado para ver mensajes de depuración

**Si los canales se ven idénticos:**
1. Verifica el contacto de los sensores con la piel
2. Asegúrate de que el Muse esté correctamente posicionado
3. Revisa la configuración de la app Muse

---

**¡Listo para probar con el sensor real!** 🎉
