# Cambios para Soporte Multicanal Muse 2

## Resumen
El archivo `py-v26-multichannel.py` ha sido creado como extensión de `py-v24.py` para soportar el procesamiento individual de los 4 canales EEG del dispositivo Muse 2.

## Canales EEG del Muse 2
El Muse 2 tiene 4 canales EEG ubicados en las siguientes posiciones:
- **TP9**: Temporal izquierdo posterior
- **AF7**: Frontal izquierdo anterior  
- **AF8**: Frontal derecho anterior
- **TP10**: Temporal derecho posterior

## Cambios Implementados

### 1. Constantes de Canales
```python
EEG_CHANNELS = ['TP9', 'AF7', 'AF8', 'TP10']
EEG_CHANNEL_INDICES = {ch: idx for idx, ch in enumerate(EEG_CHANNELS)}
```

### 2. Modo de Procesamiento
Nueva variable global `eeg_processing_mode` con dos opciones:
- `'average'`: Promedia los 4 canales (compatibilidad con v24)
- `'individual'`: Procesa cada canal por separado

### 3. Estructuras de Datos

#### Modo Promedio (v24 compatible):
```python
bands = {b: dict(...) for b in FILTS}
eeg_buf = deque(maxlen=WIN)
baseline_eeg_values = {}
```

#### Modo Multicanal (nuevo):
```python
bands_per_channel = {
    ch: {b: dict(...) for b in FILTS}
    for ch in EEG_CHANNELS
}
eeg_buf_per_channel = {ch: deque(maxlen=WIN) for ch in EEG_CHANNELS}
baseline_eeg_values_per_channel = {ch: {} for ch in EEG_CHANNELS}
```

### 4. Formato de Datos OSC del Muse 2

El Muse envía los datos en el siguiente formato:
- **1 canal**: 256 valores (SRATE)
- **4 canales**: 1024 valores (SRATE * 4)

Orden de los datos: `[TP9_samples..., AF7_samples..., AF8_samples..., TP10_samples...]`

### 5. Rutas OSC de Salida

#### Modo Promedio:
- `/py/bands_env` - Envolvente de las 5 bandas (promediado)
- `/py/bands_signed_env` - Envolvente con signo (promediado)
- `/py/bands_raw` - Valores RMS crudos (promediado)

#### Modo Multicanal:
Por cada canal (tp9, af7, af8, tp10):
- `/py/tp9/bands_env` - Envolvente de las 5 bandas del canal TP9
- `/py/tp9/bands_signed_env` - Envolvente con signo del canal TP9
- `/py/tp9/bands_raw` - Valores RMS crudos del canal TP9
- (Similar para af7, af8, tp10)

### 6. Funciones Principales

#### `muse_eeg(_, *vals)`
- Función principal que recibe datos OSC
- Detecta automáticamente el número de canales
- Redirige a modo promedio o individual según configuración

#### `process_eeg_average(vals)`
- Procesa en modo promedio (compatible v24)
- Promedia todos los valores recibidos
- Mantiene la lógica original de v24

#### `process_eeg_individual_channels(vals)`
- Nueva función para modo multicanal
- Divide los datos en 4 canales
- Procesa cada canal independientemente
- Calcula baseline por canal
- Envía datos separados por canal

#### `complete_baseline_eeg_phase()`
- Función común para ambos modos
- Maneja el progreso del baseline
- Calcula estadísticas según el modo activo

## Uso

### Configuración en el Menú
Al seleccionar "Solo Sensor Cerebral (Muse)" y activar "Ondas", el script preguntará:
```
¿Procesar canales individuales? (s/n):
```
- **s/sí**: Activa modo multicanal (procesa TP9, AF7, AF8, TP10 por separado)
- **n/no**: Usa modo promedio (compatibilidad v24)

### En TouchDesigner
Para recibir los datos multicanal, configura OSC In operators con las rutas:
```
/py/tp9/bands_env
/py/af7/bands_env
/py/af8/bands_env
/py/tp10/bands_env
```

Cada ruta envía un array de 5 valores: `[delta, theta, alpha, beta, gamma]`

## Ventajas del Modo Multicanal

1. **Resolución Espacial**: Permite ver diferencias entre regiones cerebrales
2. **Asimetría Hemisférica**: Comparar actividad entre hemisferios izquierdo/derecho
3. **Patrones Específicos**: Identificar patrones de activación específicos por región
4. **Mayor Granularidad**: 4x más datos para análisis y visualización

## Compatibilidad

- ✅ Totalmente compatible con v24 en modo promedio
- ✅ Mantiene todas las funciones de baseline, acelerómetro, PPG, etc.
- ✅ Soporta grabación CSV en ambos modos
- ✅ Compatible con simulación y otros sensores

## Próximos Pasos

Para implementar completamente el soporte multicanal, necesitarás:
1. ✅ Configurar la aplicación Muse para enviar datos de 4 canales
2. ✅ Actualizar TouchDesigner para recibir las nuevas rutas OSC
3. ✅ Adaptar visualizaciones para mostrar 4 canales
4. ⏳ Opcional: Agregar análisis de coherencia entre canales
