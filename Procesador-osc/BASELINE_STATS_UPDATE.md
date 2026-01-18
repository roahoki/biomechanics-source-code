# Baseline Statistics Update (v24)

## 📊 Cambios Implementados

Se han incorporado **desviación estándar (σ)**, **valores mínimos** y **máximos** a los datos de baseline en el script `py-v24.py`.

### 🧠 EEG Baseline

Ahora se capturan y envían para **cada onda cerebral** (delta, theta, alpha, beta, gamma):

- **μ (media)**: Promedio de la banda
- **σ (sigma/desviación estándar)**: Variabilidad en la banda
- **min**: Valor mínimo detectado durante el baseline
- **max**: Valor máximo detectado durante el baseline

#### OSC Paths EEG:
```
/py/baseline_mu      → [delta_μ, theta_μ, alpha_μ, beta_μ, gamma_μ]
/py/baseline_sigma   → [delta_σ, theta_σ, alpha_σ, beta_σ, gamma_σ]  ✨ NUEVO
/py/baseline_min     → [delta_min, theta_min, alpha_min, beta_min, gamma_min]  ✨ NUEVO
/py/baseline_max     → [delta_max, theta_max, alpha_max, beta_max, gamma_max]  ✨ NUEVO
```

#### CSV Metadata:
```
# DELTA: μ=0.123 σ=0.045 min=0.080 max=0.200
# THETA: μ=0.456 σ=0.078 min=0.300 max=0.650
# ... etc
```

---

### 📍 ACC (Acelerómetro) Baseline

Se mantienen todos los valores previos y se añade **desviación estándar** para cada eje:

- **neutral**: Posición de referencia (promedio de la fase neutra)
- **range**: Rango total de movimiento (max - min)
- **min**: Valor mínimo durante toda la medición
- **max**: Valor máximo durante toda la medición
- **sigma**: Desviación estándar de todos los valores capturados  ✨ NUEVO

#### OSC Paths ACC (Eje X como ejemplo):
```
/py/acc_x_neutral → posición neutra
/py/acc_x_range   → rango de movimiento
/py/acc_x_min     → valor mínimo
/py/acc_x_max     → valor máximo
/py/acc_x_sigma   → desviación estándar  ✨ NUEVO
```

Lo mismo para `acc_y_*` y `acc_z_*`

#### CSV Metadata:
```
# ACC_X: neutral=+0.0234 range=1.2345 [−0.5678, +0.7890] σ=0.3456
# ACC_Y: neutral=−0.0123 range=0.9876 [−0.4321, +0.5555] σ=0.2789
# ... etc
```

---

## 🔧 Cambios Técnicos

### Estructuras de Datos Modificadas

1. **`acc_rng`** - Ahora incluye campo `values[]` para capturar todos los datos durante baseline
   ```python
   acc_rng = {a: dict(min=None, max=None, values=[]) for a in acc}
   ```

2. **`baseline_eeg_values`** - Estructura mejorada
   ```python
   baseline_eeg_values = {}  # {band: {'mu': X, 'sigma': Y, 'min': Z, 'max': W}}
   ```

3. **`baseline_acc_*`** - Añadido campo sigma
   ```python
   baseline_acc_x = {'neutral': None, 'min': None, 'max': None, 'range': None, 'sigma': None}
   ```

### Funciones Actualizadas

- **`close_baseline_eeg()`**: Calcula min/max además de μ/σ
- **`close_baseline_acc()`**: Calcula σ de todos los valores capturados en cada eje
- **`DataRecorder.write_baseline_metadata()`**: Incluye σ en el CSV para ambos sensores

### Loops de Captura

Los loops de baseline ahora almacenan todos los valores en `acc_rng[a]['values']` para posterior cálculo de estadísticas:

```python
# En FASE A y FASE B
for a in acc:
    rng = acc_rng[a]
    rng['values'].append(acc[a])  # ✨ Captura de valores
    rng['min'] = acc[a] if rng['min'] is None else min(rng['min'], acc[a])
    rng['max'] = acc[a] if rng['max'] is None else max(rng['max'], acc[a])
```

---

## 📈 Ventajas

✅ **Mejor caracterización del baseline**: La desviación estándar permite entender la variabilidad natural en cada sensor

✅ **Detección de anomalías**: Con min/max se puede validar si el rango de valores es anómalo

✅ **Debugging mejorado**: Valores estadísticos completos facilitan diagnóstico de problemas en sensores

✅ **Compatibilidad con Touch Designer**: Los nuevos OSC paths (`/py/baseline_sigma`, `/py/baseline_min`, `/py/baseline_max`, `/py/acc_*_sigma`) están disponibles para visualización y análisis

✅ **CSV más informativo**: Los archivos de grabación contienen estadísticas completas del baseline

---

## 🚀 Próximas Mejoras (Sugerencias)

- [ ] Calcular z-scores durante operación normal usando σ del baseline
- [ ] Alertas si σ actual excede σ del baseline (indicador de anomalía)
- [ ] Exportar matrices de correlación entre bandas EEG
- [ ] Análisis de coherencia cross-frequency entre bandas cerebrales

