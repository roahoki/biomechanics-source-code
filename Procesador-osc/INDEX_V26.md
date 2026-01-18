# 📋 Índice de Documentación v26 - Acceso Rápido

## 🎯 START HERE - Comienza por aquí

### ⏱️ 5 Minutos: Setup Rápido
→ [USAGE_GUIDE_V26.md](#-rápido-start) **Sección "Inicio Rápido"**

### 📖 30 Minutos: Comprensión Completa
→ [USAGE_GUIDE_V26.md](USAGE_GUIDE_V26.md) **Leer completo**

### 🔧 Troubleshooting
→ [USAGE_GUIDE_V26.md](USAGE_GUIDE_V26.md) **Sección "Troubleshooting"**

---

## 📚 Documentación Disponible

### Archivos de Documentación
```
📄 COMMIT_SUMMARY_V26.md     ← Resumen ejecutivo (ESTE ARCHIVO)
📄 CHANGELOG_V26.md          ← Historia y cambios técnicos
📄 USAGE_GUIDE_V26.md        ← Guía completa (400+ líneas)
📄 README_MULTICANAL.md      ← Guía rápida multicanal
📄 OSC_VERIFICATION.md       ← Todas las rutas OSC
📄 IMPLEMENTATION_SUMMARY.md ← Detalles de implementación
📄 MULTICHANNEL_CHANGES.md   ← Cambios técnicos en detalle
```

### Scripts de Código
```
🐍 py-v26-multichannel.py    ← Versión multicanal PRINCIPAL
🐍 test_muse_format.py       ← Diagnóstico de formato Muse
🐍 test_osc_receiver.py      ← Monitor OSC en tiempo real
🐍 py-v24.py                 ← Versión anterior (referencia)
🐍 py-v25-full.py            ← Con debugging (referencia)
```

---

## 🚀 Guía de Selección Rápida

### "Quiero empezar ahora"
```
1. Ejecuta: python py-v26-multichannel.py
2. Lee: USAGE_GUIDE_V26.md "Inicio Rápido"
⏱️ Tiempo: 5 minutos
```

### "Quiero entender los datos"
```
1. Lee: CHANGELOG_V26.md "Cálculos de Signal Processing"
2. Lee: USAGE_GUIDE_V26.md "Análisis de Resultados"
⏱️ Tiempo: 15 minutos
```

### "Tengo un problema"
```
1. Ejecuta: python test_muse_format.py
2. Lee: USAGE_GUIDE_V26.md "Troubleshooting"
⏱️ Tiempo: 10 minutos
```

### "Quiero integrar con TouchDesigner"
```
1. Lee: USAGE_GUIDE_V26.md "Métodos de Uso - TouchDesigner OSC In"
2. Lee: OSC_VERIFICATION.md "Todas las rutas disponibles"
⏱️ Tiempo: 20 minutos
```

### "Quiero código de ejemplo"
```
1. Lee: USAGE_GUIDE_V26.md "Ejemplos Prácticos"
2. Lee: USAGE_GUIDE_V26.md "Métodos de Uso" (secciones Python/Max/Processing)
⏱️ Tiempo: 15 minutos
```

---

## 📡 Rutas OSC Principales

### Canales Individuales (Modo Individual)
```
/py/tp9/bands_raw           → [delta, theta, alpha, beta, gamma]
/py/tp9/bands_env           → Envolvente (0.0-1.0)
/py/tp9/bands_signed_env    → Z-score (-3.0 a +3.0)

/py/af7/bands_*             → Frontal izquierdo
/py/af8/bands_*             → Frontal derecho
/py/tp10/bands_*            → Temporal derecho
```

### Promedios (Siempre disponible)
```
/py/bands_raw               → Promedio RMS
/py/bands_env               → Promedio envolvente
/py/bands_signed_env        → Promedio z-score
```

### Acelerómetro y Pulso
```
/py/acc_x/y/z_neutral       → Posición neutra por eje
/py/acc_x/y/z_range         → Rango de movimiento
/py/acc_x/y/z_min/max       → Valores mínimos y máximos
/py/acc_x/y/z_sigma         → Desviación estándar
/py/ppg                     → Heartbeat/Pulso
```

---

## 🎯 Flujos Comunes

### Flujo 1: Visualizar 4 Canales en TouchDesigner
```
1. OSC In → Conectar a puerto 5002
2. En script CHOP: crear 4 canales (tp9, af7, af8, tp10)
3. Mapear rutas: /py/tp9/bands_env[0] → canal 0, etc.
4. Visualizar en gráfico
⏱️ Tiempo: 15 minutos
```

### Flujo 2: Detectar Cambios de Estado Mental
```
1. Capturar /py/bands_signed_env
2. Si z-score > 1.5 → Estado alterado
3. Si z-score < -1.5 → Supresión
4. Trigger eventos basados en umbrales
⏱️ Tiempo: 20 minutos
```

### Flujo 3: Comparar Asimetría Hemisférica
```
1. Capturar /py/af7/bands_env (frontal izq)
2. Capturar /py/af8/bands_env (frontal der)
3. Calcular diferencia: af7 - af8
4. Si diferencia > 0.3 → Asimetría detectada
⏱️ Tiempo: 25 minutos
```

### Flujo 4: Análisis Multicanal en Python
```python
import osc_handler

def process_eeg():
    tp9 = osc['/py/tp9/bands_raw']      # [167.06, 46.84, ...]
    af7 = osc['/py/af7/bands_raw']
    af8 = osc['/py/af8/bands_raw']
    tp10 = osc['/py/tp10/bands_raw']
    
    # Analizar por canal...
⏱️ Tiempo: 30 minutos
```

---

## 🔍 Búsqueda por Tema

### Signal Processing
- [Cálculos técnicos](CHANGELOG_V26.md#cálculos-de-signal-processing)
- [Filtrado Butterworth](CHANGELOG_V26.md#procesamiento-de-señal)
- [Z-score normalizado](USAGE_GUIDE_V26.md#interpretación-de-resultados)

### Bandas de Frecuencia
- [Banda Delta](USAGE_GUIDE_V26.md#tabla-de-bandas-por-estado-mental)
- [Banda Theta](USAGE_GUIDE_V26.md#tabla-de-bandas-por-estado-mental)
- [Banda Alpha](USAGE_GUIDE_V26.md#tabla-de-bandas-por-estado-mental)
- [Banda Beta](USAGE_GUIDE_V26.md#tabla-de-bandas-por-estado-mental)
- [Banda Gamma](USAGE_GUIDE_V26.md#tabla-de-bandas-por-estado-mental)

### Integración
- [TouchDesigner](USAGE_GUIDE_V26.md#método-1-touchdesigner-osc-in)
- [Python](USAGE_GUIDE_V26.md#método-2-python-script-receptor)
- [Max/MSP](USAGE_GUIDE_V26.md#método-3-maxmsp-o-pd)
- [Processing](USAGE_GUIDE_V26.md#método-4-processing-ide)

### Troubleshooting
- [Conexión Muse](USAGE_GUIDE_V26.md#problema-no-se-reciben-datos-en-touchdesigner)
- [Valores en 0](USAGE_GUIDE_V26.md#problema-valores-en-0-en-todos-los-canales)
- [Datos inconsistentes](USAGE_GUIDE_V26.md#problema-datos-inconsistentes-entre-canales)
- [Formato Muse](USAGE_GUIDE_V26.md#problema-qué-significan-esos-6-valores-que-envía-muse)

### Configuración
- [Setup inicial](USAGE_GUIDE_V26.md#inicio-rápido)
- [Modos de operación](USAGE_GUIDE_V26.md#modos-de-operación)
- [Configuración avanzada](USAGE_GUIDE_V26.md#configuración-avanzada)

---

## 📊 Datos de Referencia

### Valores Normales (Baseline)
```
Delta:   100-200 µV
Theta:   30-60 µV
Alpha:   20-50 µV
Beta:    10-40 µV
Gamma:   5-30 µV
```

### Tabla Z-score
```
-3.0: Completamente suprimido
-2.0: Muy suprimido
-1.0: Ligeramente bajo
 0.0: Baseline/Neutral
+1.0: Ligeramente elevado
+2.0: Elevado
+3.0: Muy elevado
```

### Performance
```
Latencia:       ~50ms
CPU:            5-8%
RAM:            ~50MB
Ancho banda:    4KB/s
Muestreo:       256 Hz
```

---

## 🛠️ Herramientas de Diagnóstico

### test_muse_format.py - Detectar formato
```bash
python test_muse_format.py
# Muestra: formato (1/4/6 valores), distribución, recomendaciones
```

### test_osc_receiver.py - Monitorear OSC
```bash
python test_osc_receiver.py
# Muestra: todos los mensajes en puerto 5002, resumen por categoría
```

---

## ✅ Checklist de Setup

### Instalación Inicial
- [ ] Clonar repositorio
- [ ] Crear venv Python
- [ ] Instalar dependencias (numpy, scipy, python-osc)
- [ ] Confirmar Muse 2 conectado

### Configuración Muse
- [ ] App Muse instalada en móvil
- [ ] Muse emparejado y encendido
- [ ] Ajustar OSC Stream Target IP:puerto
- [ ] Confirmar "Stream ON"

### Verificación Software
- [ ] Ejecutar `test_muse_format.py` → detecta formato
- [ ] Ejecutar `py-v26-multichannel.py` → recibe datos
- [ ] Ejecutar `test_osc_receiver.py` → ve mensajes OSC

### Integración TouchDesigner
- [ ] Crear OSC In operator
- [ ] Configurar puerto 5002
- [ ] Mapear rutas /py/bands_*
- [ ] Verificar recepción de datos

---

## 📚 Archivos por Experiencia

### Principiantes
```
1. USAGE_GUIDE_V26.md (sección "Inicio Rápido")
2. Ejecutar py-v26-multichannel.py
3. Ver datos en test_osc_receiver.py
```

### Intermedios
```
1. CHANGELOG_V26.md (entero)
2. USAGE_GUIDE_V26.md "Métodos de Uso"
3. Implementar en TouchDesigner
```

### Avanzados
```
1. IMPLEMENTATION_SUMMARY.md (detalles técnicos)
2. MULTICHANNEL_CHANGES.md (cambios en código)
3. OSC_VERIFICATION.md (todas las rutas)
4. Analizar py-v26-multichannel.py directamente
```

---

## 🎯 Commits Relacionados

```
a7dc9b4 docs: Agregar resumen completo del commit v26
019797d feat: Soporte completo multicanal EEG Muse 2 v26
189bd05 Create biomechanics-home-data-logging
```

Ver commits: `git log --oneline | head -5`

---

## 📞 Soporte Rápido

**Pregunta**: "¿Dónde empiezo?"
→ [USAGE_GUIDE_V26.md - Inicio Rápido](USAGE_GUIDE_V26.md#inicio-rápido)

**Pregunta**: "¿Cómo integro con TouchDesigner?"
→ [USAGE_GUIDE_V26.md - Método 1](USAGE_GUIDE_V26.md#método-1-touchdesigner-osc-in)

**Pregunta**: "¿Qué significan estos valores?"
→ [USAGE_GUIDE_V26.md - Análisis de Resultados](USAGE_GUIDE_V26.md#análisis-de-resultados)

**Pregunta**: "Tengo un error"
→ [USAGE_GUIDE_V26.md - Troubleshooting](USAGE_GUIDE_V26.md#-troubleshooting)

**Pregunta**: "¿Qué datos se envían?"
→ [OSC_VERIFICATION.md](OSC_VERIFICATION.md)

---

## 🎓 Orden de Lectura Recomendado

### Sesión 1 (30 min)
1. Este archivo (COMMIT_SUMMARY_V26.md)
2. USAGE_GUIDE_V26.md "Inicio Rápido"
3. Ejecutar y probar py-v26-multichannel.py

### Sesión 2 (1 hora)
1. CHANGELOG_V26.md "Nuevas Características"
2. USAGE_GUIDE_V26.md "Métodos de Uso"
3. Integrar con tu herramienta (TouchDesigner/Python/etc)

### Sesión 3 (30 min)
1. USAGE_GUIDE_V26.md "Ejemplos Prácticos"
2. Experimentar con datos reales
3. Customizar según tus necesidades

### Sesión 4 (opcional - avanzado)
1. IMPLEMENTATION_SUMMARY.md
2. MULTICHANNEL_CHANGES.md
3. Analizar código fuente py-v26-multichannel.py

---

## 🚀 Próximos Pasos

✅ **Completado**: Setup multicanal
✅ **Completado**: Documentación completa
✅ **Completado**: Herramientas de diagnóstico

🔄 **Siguiente**: Experimentar con los datos
🔄 **Siguiente**: Implementar visualizaciones
🔄 **Siguiente**: Entrenar modelos ML si es necesario

---

**Versión**: 26-multichannel
**Fecha**: 18 de enero, 2026
**Estado**: Production Ready ✅
**Documentación**: Completa ✅
