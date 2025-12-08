# Integración PPG (Heartbeat) - Documento Técnico

## 📊 Cambios Implementados

### 1. **Handler PPG Mejorado** (`muse_ppg()`)
- ✅ Extrae correctamente el segundo valor del mensaje OSC `/desdemuse/ppg: (nan, ppg_value, nan)`
- ✅ Convierte valor raw de Muse a BPM usando fórmula empírica
- ✅ Envía 2 OSC paths a TouchDesigner:
  - `/py/ppg` → Valor raw (125-126 millones)
  - `/py/ppg/bpm` → BPM calculado (40-180)
- ✅ Actualiza CC MIDI (0-127) para PPG

### 2. **Menú Principal**
- ✅ Agregado prompt: "¿Heartbeat/PPG?" al menú de configuración
- ✅ Variable global `use_ppg` controla activación

### 3. **Salida en Tiempo Real**
- ✅ Nuevo indicador en `line_post()`: `♥{bpm:6.1f}bpm→{cc:3d}`
- ✅ Muestra "♥calibrando" durante baseline
- ✅ Muestra BPM en vivo tras baseline completo

---

## 🔧 Fórmula de Conversión PPG → BPM

### Rango de Valores Observado
```
Muse PPG raw: 125,000,000 - 126,000,000
Variación típica: ±1,000,000 = ±40 BPM alrededor de 70 BPM
```

### Fórmula Empírica
```python
ppg_baseline = 125,500,000      # Punto medio observado
ppg_scale = 1,000,000           # Rango de variación
bpm_range = 40                  # ±20 BPM
bpm_center = 70                 # BPM central

normalized = (ppg_raw - ppg_baseline) / ppg_scale
bpm = bpm_center + (normalized * bpm_range)
bpm = clamp(bpm, 40, 180)       # Rango fisiológico
```

### Ejemplo
```
ppg_raw = 125,500,000
normalized = (125,500,000 - 125,500,000) / 1,000,000 = 0
bpm = 70 + (0 * 40) = 70 BPM ✓

ppg_raw = 125,900,000
normalized = (125,900,000 - 125,500,000) / 1,000,000 = 0.4
bpm = 70 + (0.4 * 40) = 86 BPM ✓

ppg_raw = 125,100,000
normalized = (125,100,000 - 125,500,000) / 1,000,000 = -0.4
bpm = 70 + (-0.4 * 40) = 54 BPM ✓
```

---

## 📤 Rutas OSC Enviadas a TouchDesigner

### Nuevo Path
```
/py/ppg/bpm → float (40-180)    # BPM calculado en tiempo real
/py/ppg     → float             # Valor raw de Muse
```

### Mapeo MIDI CC
```
ppg['cc'] = int(scale(bpm, 40, 180))  # Mapea 40-180 BPM → 0-127 CC
```

---

## 🔍 Validaciones Implementadas

1. **Formato del mensaje**: Verifica que llegan 3 valores
2. **Valores NaN**: Ignora índices 0 y 2, valida índice 1
3. **Rango fisiológico**: Clamp a 40-180 BPM
4. **Debug mode**: Imprime `[PPG] Raw: {raw} → BPM: {bpm}` cuando está activado

---

## 🧪 Cómo Probar

1. Ejecutar script: `python py-v24.py`
2. Seleccionar opción 1 (Sensor Muse)
3. Responder "Sí" a "¿Heartbeat/PPG?"
4. Observar línea de salida: `♥{bpm}bpm→{cc}`
5. En TouchDesigner, recibir en `/py/ppg/bpm` valores 40-180

---

## 📝 Variables de Estado

```python
ppg = {
    'raw': float,      # Valor raw de Muse (~125M)
    'bpm': float,      # BPM calculado (40-180)
    'cc': int          # MIDI CC 0-127
}
```

---

## ⚙️ Ajustes Futuros (si es necesario)

Si los valores BPM no coinciden con el ritmo cardíaco real, ajustar:
- `ppg_baseline`: Cambiar si el rango típico es diferente
- `ppg_scale`: Ajustar si las variaciones son mayores/menores
- `bpm_center`: Cambiar si el reposo no es ~70 BPM
- `bpm_range`: Ampliar rango si se necesita 30-200 BPM

---

**Estado**: ✅ Implementado y compilado sin errores
**Próximos pasos**: Probar con sensor Muse en vivo, ajustar fórmula si es necesario
