#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT PYTHON (v24)
- Mantiene Modo Simulador (Opción 0).
- CORRECCIÓN: Restaurada la función 'open_midi()' que
              fue eliminada por error en v23, causando
              el 'name 'open_midi' is not defined'.
- Mantiene estructura robusta try/except/finally y pausa final.
"""

import sys
import time # Para la pausa inicial

import math, re, threading, logging, socket
from collections import deque
from pythonosc.udp_client import SimpleUDPClient

# --- Dependencias ---
try:
    import numpy as np; import mido; import serial; import scipy.signal as sg
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
except ImportError as e: print(f"!!! ERROR: Falta librería: {e}\nInstala dependencias."); input("Enter..."); sys.exit(1)
# --------------------

# --- Pausa inicial ---
print("Iniciando script python v24...")
print("Esta ventana debería permanecer abierta.")
# --------------------

# --- Funciones (get_local_ip, preguntar_bool - sin cambios) ---
def get_local_ip():
    s=None; ip="127.0.0.1";
    try: s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]
    except Exception:
        try: ip=socket.gethostbyname(socket.gethostname())
        except Exception: print("⚠️ ADVERTENCIA: No IP. Usando 127.0.0.1")
    finally:
        if s: s.close()
    return ip
def preguntar_bool(texto): resp = input(texto + " (s/n): ").strip().lower(); return resp.startswith('s')
# -------------------------------------------------------------

# --- Config Inicial Red (Solo si no es simulación) ---
OSC_PORT = 5001; MY_LOCAL_IP = get_local_ip()
# ------------------------------------

# --- Menú de Selección con Opción 0 ---
print("=== SELECCIÓN DE FUENTE DE DATOS ===")
print("0. Modo Simulador (Datos Falsos)")
print("1. Solo Sensor Cerebral (Muse)")
print("2. Solo Arduino")
print("3. Ambos (Muse + Arduino)")
print("4. Salir")
choice = input("Selecciona una opción (0-4): ").strip()

is_simulation = (choice == '0')

use_eeg = use_acc = use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False; valid_choice = True

if is_simulation:
    print("\n--- MODO SIMULADOR ACTIVADO ---")
    use_eeg = True; use_acc = True
    use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False
elif choice == '1':
    print("\n" + "="*50 + "\n    CONFIG OSC\n"+f"    ► App Muse -> IP: {MY_LOCAL_IP} | Puerto: {OSC_PORT}\n"+"="*50 + "\n")
    print("--- Config Sensor Cerebral ---"); use_eeg=preguntar_bool("¿Ondas?"); use_acc=preguntar_bool("¿Accel?"); use_myo=use_temp_hum=use_plant1=use_plant2=use_dist=False
elif choice == '2':
    print("\n--- Config Arduino ---"); use_myo=preguntar_bool("¿Myo?");use_temp_hum=preguntar_bool("¿Temp/Hum?");use_plant1=preguntar_bool("¿Planta1?");use_plant2=preguntar_bool("¿Planta2?");use_dist=preguntar_bool("¿Dist?"); use_eeg=use_acc=False
elif choice == '3':
    print("\n" + "="*50 + "\n    CONFIG OSC\n"+f"    ► App Muse -> IP: {MY_LOCAL_IP} | Puerto: {OSC_PORT}\n"+"="*50 + "\n")
    print("--- Config Sensor Cerebral ---"); use_eeg=preguntar_bool("¿Ondas?"); use_acc=preguntar_bool("¿Accel?");
    print("\n--- Config Arduino ---"); use_myo=preguntar_bool("¿Myo?");use_temp_hum=preguntar_bool("¿Temp/Hum?");use_plant1=preguntar_bool("¿Planta1?");use_plant2=preguntar_bool("¿Planta2?");use_dist=preguntar_bool("¿Dist?")
elif choice == '4': print("Saliendo."); sys.exit()
else: print("Opción inválida."); valid_choice=False; sys.exit()

any_sensor_selected = any((use_eeg, use_acc, use_myo, use_temp_hum, use_plant1, use_plant2, use_dist))
if not any_sensor_selected and valid_choice and not is_simulation: print("\nAdvertencia: Ningún sensor específico fue seleccionado.")
if valid_choice: print("="*40+"\n")
# --- FIN MENÚ ---

# --- Config ---
SERIAL_PORT, BAUD="COM3", 115200; PROC_IP="127.0.0.1"; PROC_PORT=5002
proc_client = None
try:
    proc_client=SimpleUDPClient(PROC_IP, PROC_PORT)
    print("="*50+f"\n    ► Enviando a Processing -> IP: {PROC_IP} | Puerto: {PROC_PORT}\n"+"="*50+"\n")
except Exception as e: print(f"!!! ERROR FATAL creando cliente OSC: {e}"); input("Enter..."); sys.exit(1)

SRATE, WIN_S=256, 2; WIN, STEP=SRATE*WIN_S, (SRATE*WIN_S)//2; BASE_SEC=10
Z_MAX, ALPHA_ENV, DEAD_ZONE, ALPHA_DIST=3.0, 0.3, 0.2, 0.25
UPDATE_HZ=10.0; SLEW_PER_SEC=25; MIN_STEP_CC=1; CURVE_MODE="exp"; CURVE_K=0.65
PERIOD = 1.0 / UPDATE_HZ
# -------------

# --- Baseline Fijo Simulación ---
MU_DEFAULTS = {'delta': 1.2, 'theta': 1.0, 'alpha': 1.0, 'beta': 0.8, 'gamma': 0.5}
SD_DEFAULTS = {'delta': 0.4, 'theta': 0.3, 'alpha': 0.3, 'beta': 0.25, 'gamma': 0.2}
# --------------------------------

# --- MIDI Map ---
MIDI_PREFIX={'delta':'delta_midi','theta':'theta_midi','alpha':'alpha_midi','beta':'beta_midi','gamma':'gamma_midi','accx':'x_midi','accy':'y_midi','accz':'z_midi','plant1':'plant1_midi','plant2':'plant2_midi','myo':'myoware_midi','dist':'dist_midi','hum':'hum_midi','temp':'temp_midi'}
MIDI_CH={**{s:0 for s in ('delta','theta','alpha','beta','gamma')},**{s:0 for s in ('accx','accy','accz')},'plant1':0,'plant2':1,'myo':2,'dist':3,'hum':4,'temp':5}
CC_NUM={'delta':17,'theta':16,'alpha':14,'beta':15,'gamma':18,'accx':20,'accy':21,'accz':22,'plant1':40,'plant2':41,'myo':42,'dist':43,'hum':44,'temp':45}
# ---------------

# --- Utilidades Señal ---
def butter(lo, hi, fs=SRATE): nyq=fs*0.5; return sg.butter(4, [lo/nyq, hi/nyq], 'band')
FILTS={'delta':butter(0.5,4),'theta':butter(4,8),'alpha':butter(8,13),'beta':butter(13,30),'gamma':butter(30,45)}
def band_rms(seg, ba):
    b, a = ba
    try:
        f = sg.lfilter(b, a, seg)
        if f is None or f.size == 0 or np.all(np.isnan(f)): return np.nan
        rms_val = np.sqrt(np.nanmean(f**2))
        return rms_val if not np.isnan(rms_val) else np.nan
    except ValueError: return np.nan
    except Exception: return np.nan
def env_z(v, mu, sd, prev): # Magnitud
    if sd<=1e-9 or mu is None or math.isnan(v): return prev
    z = abs(v - mu) / sd; current_env = ALPHA_ENV*z+(1-ALPHA_ENV)*prev if z>=DEAD_ZONE else prev*(1-ALPHA_ENV); return max(0.0, current_env)
def scale(x, lo, hi): # MIDI 0-127
    if lo is None or hi is None or hi <= lo or math.isnan(x): return 0
    return max(0, min(127, round((x-lo)/(hi-lo)*127)))
# ----------------------

# --- CORRECCIÓN: Definición de open_midi() restaurada ---
def open_midi():
    avail = mido.get_output_names(); ports = {}; missing = []; active_signals = []
    if use_eeg: active_signals.extend(['delta','theta','alpha','beta','gamma'])
    if use_acc: active_signals.extend(['accx','accy','accz'])
    if use_plant1: active_signals.append('plant1')
    if use_plant2: active_signals.append('plant2')
    if use_myo: active_signals.append('myo')
    if use_dist: active_signals.append('dist')
    if use_temp_hum: active_signals.extend(['hum','temp'])
    for sig in active_signals:
        pre = MIDI_PREFIX.get(sig); name = next((n for n in avail if n.lower().startswith(pre.lower())), None) if pre else None
        if name:
            try: ports[sig] = mido.open_output(name)
            except Exception as e: print(f"Error MIDI {name}: {e}"); missing.append(pre)
        elif pre: missing.append(pre)
    if missing:
        print("--- ADVERTENCIA: Faltan puertos MIDI: "+", ".join(missing));
        for m in missing: sig_name = next((k for k,v in MIDI_PREFIX.items() if v == m), None);
        if sig_name and sig_name not in ports: ports[sig_name]=mido.ports.BaseOutput(name=f"fake_{m}"); print(f"  {sig_name:<7}→ (Falso)")
    print("Puertos MIDI detectados:");
    for s, p in ports.items():
        if not p.name.startswith("fake_"): print(f"  {s:<7}→ {p.name} (ch {MIDI_CH.get(s, 0)+1})")
    return ports
# --- FIN CORRECCIÓN ---

# --- Abrir Puertos MIDI ---
MIDI_OUT = None
try:
    MIDI_OUT = open_midi() # Ahora la función existe
except Exception as e:
    print(f"!!! ERROR abriendo puertos MIDI: {e}"); input("Enter..."); sys.exit(1)
# -----------------------

# --- Emisión CC ---
TARGET_CC={k: 0 for k in CC_NUM}; LAST_CC={k: 0 for k in CC_NUM}
threads_active = True
def cc_curve(cc, mode=CURVE_MODE,k=CURVE_K): x=max(0,min(127,cc))/127.0; y=x**(1-k) if mode=="exp" else (1.0-(1.0-x)**(1-k) if mode=="log" else x); return int(round(y*127))
def _send_cc(sig, val):
    if MIDI_OUT and sig in MIDI_OUT and MIDI_OUT[sig] is not None and not MIDI_OUT[sig].name.startswith("fake_"):
        try: MIDI_OUT[sig].send(mido.Message("control_change", channel=MIDI_CH.get(sig,0), control=CC_NUM.get(sig,0), value=int(val)))
        except Exception as e: print(f"Error MIDI {MIDI_OUT[sig].name}: {e}")
def set_cc(sig, val):
    if sig in CC_NUM: TARGET_CC[sig] = int(max(0, min(127, val)))
def midi_tick():
    period=PERIOD; max_step=int(round(SLEW_PER_SEC/UPDATE_HZ))
    print("... Hilo MIDI iniciado ...")
    while threads_active:
        try:
            t0=time.time(); active_cc_signals=[sig for sig in TARGET_CC if MIDI_OUT and sig in MIDI_OUT]
            for sig in active_cc_signals:
                prev=LAST_CC.get(sig, 0); target=TARGET_CC.get(sig, 0); step=max(-max_step, min(max_step, target-prev)); raw=prev+step; shaped=cc_curve(raw)
                if abs(shaped-prev)>=MIN_STEP_CC: LAST_CC[sig]=shaped; _send_cc(sig, shaped)
            dt=time.time()-t0; time.sleep(max(0.0, period-dt))
        except Exception as e: print(f"\n!!! Error en midi_tick: {e}"); time.sleep(1)
    print("... Hilo MIDI terminado.")
# ---------------

# --- Estados ---
bands = {b: dict(rms=np.nan, env=0, signed_env=0.0, mu=MU_DEFAULTS.get(b, 1.0) if is_simulation else None, sd=SD_DEFAULTS.get(b, 1.0) if is_simulation else None, cc=0, buf=[]) for b in FILTS}
acc = {'x':0.0, 'y':0.0, 'z':0.0}; acc_rng = {a: dict(min=-1.0 if is_simulation else None, max=1.0 if is_simulation else None) for a in acc}
bio = {k: dict(raw=None, env=0, mu=None, amp=None, min=None, max=None, sum=0, cnt=0, cc=0) for k in ('plant1', 'plant2', 'myo')}
dist = dict(raw=None, filt=None, min=None, max=None, cc=0); hum, temp = dict(raw=None, cc=0), dict(raw=None, cc=0)
eeg_buf = deque(maxlen=WIN)
needs_baseline_calibration = not is_simulation and any((use_eeg, use_acc, use_myo, use_plant1, use_plant2, use_dist))
frames_left = int(BASE_SEC / (STEP / SRATE)) if needs_baseline_calibration and (use_eeg or use_acc) else 0
baseline_done = not needs_baseline_calibration or not (use_eeg or use_acc)
bio_done = not needs_baseline_calibration or not (use_myo or use_plant1 or use_plant2)
dist_done = not needs_baseline_calibration or not use_dist
# ------------

# --- Impresión ---
PREV_LEN=0
def refresh(text): global PREV_LEN; pad=text.ljust(PREV_LEN); sys.stdout.write('\r'+pad); sys.stdout.flush(); PREV_LEN=len(text)
def line_pre():
    parts=[]; mode = "SIM" if is_simulation else "REAL"
    if use_eeg: parts+=[f"{b}:{'sim' if is_simulation else ('nan' if math.isnan(bands[b].get('rms', np.nan)) else f'{bands[b]['rms']:.2f}')}" for b in bands]
    if use_acc: parts+=[f"{a}:{acc.get(a, 0.0):+.2f}" for a in acc]
    if any((use_myo,use_plant1,use_plant2)): parts+=[f"{k}:{'sim' if is_simulation else (bio.get(k,{}).get('raw','-') if bio.get(k) else '-')}" for k in bio if globals().get(f'use_{k}',False)]
    if use_dist: parts.append(f"dist:{'sim' if is_simulation else (dist.get('raw', '-') if dist else '-')}")
    if use_temp_hum: parts.append(f"hum:{'sim' if is_simulation else (hum.get('raw', '-') if hum else '-')}"); parts.append(f"temp:{'sim' if is_simulation else (temp.get('raw', '-') if temp else '-')}")
    return f"[{mode}] " + " | ".join(parts)
def line_post():
    parts=[]; mode = "SIM" if is_simulation else "REAL"
    if use_eeg: parts+=[f"{b}:{bands[b].get('signed_env',0.0):+.2f}({bands[b].get('env',0.0):.2f})→{bands[b].get('cc',0):3d}" for b in bands]
    if use_acc and baseline_done: parts+=[f"{a}:{acc.get(a,0.0):+.2f}→{scale(acc.get(a,0.0),acc_rng.get(a,{}).get('min'),acc_rng.get(a,{}).get('max')):3d}" for a in acc]
    elif use_acc: parts+=[f"{a}:calibrando" for a in acc]
    if any((use_myo,use_plant1,use_plant2)):
        for k in bio:
            if globals().get(f'use_{k}',False): parts.append(f"{k}:{'sim' if is_simulation else (bio.get(k,{}).get('env',0.0) if bio_done else 'cal')}:.2f→{bio.get(k,{}).get('cc',0):3d}" if bio_done else f"{k}:calibrando")
    if use_dist: parts.append(f"dist:{'sim' if is_simulation else (dist.get('filt',0.0) if dist_done and dist.get('filt') is not None else 'cal')}:.1f→{dist.get('cc',0):3d}" if dist_done else "dist:calibrando")
    if use_temp_hum:
        parts.append(f"hum:{'sim' if is_simulation else (hum.get('raw','-'))}:.1f→{hum.get('cc',0):3d}")
        parts.append(f"temp:{'sim' if is_simulation else (temp.get('raw','-'))}:.1f→{temp.get('cc',0):3d}")
    return f"[{mode}] " + " | ".join(parts)
# ---------------

# --- Handlers y Parse (Solo modo real) ---
def muse_eeg(_, *vals):
    if not use_eeg or is_simulation: return
    global frames_left, baseline_done; valid_vals = [v for v in vals if not math.isnan(v)];
    if not valid_vals: return; eeg_buf.append(np.mean(valid_vals));
    if len(eeg_buf) < WIN: return; seg = np.array(eeg_buf); osc_band_values_env = []; osc_band_values_signed = []
    try:
        for n, f in FILTS.items():
            r = band_rms(seg, f); bands[n]['rms'] = r
            if not baseline_done:
                 if not math.isnan(r): bands[n]['buf'].append(r)
            else:
                if bands[n]['mu'] is None or bands[n]['sd'] is None: continue
                mu=bands[n]['mu']; sd=bands[n]['sd']; prev_env=bands[n]['env']; prev_signed_env=bands[n]['signed_env']
                current_env = env_z(r, mu, sd, prev_env); bands[n]['env']=current_env; bands[n]['cc']=c=scale(current_env,0,Z_MAX); set_cc(n,c); osc_band_values_env.append(current_env)
                if sd>1e-9 and not math.isnan(r): signed_z_raw=(r-mu)/sd; current_signed_env=ALPHA_ENV*signed_z_raw+(1-ALPHA_ENV)*prev_signed_env
                else: current_signed_env = prev_signed_env*(1-ALPHA_ENV)
                bands[n]['signed_env']=current_signed_env; osc_band_values_signed.append(current_signed_env)
    except Exception as e: print(f"\n!!! Error calculando bandas: {e}")
    if baseline_done:
        try:
            if len(osc_band_values_env)==5: proc_client.send_message("/py/bands_env", osc_band_values_env)
            if len(osc_band_values_signed)==5: proc_client.send_message("/py/bands_signed_env", osc_band_values_signed)
        except Exception as e: print(f"!!! Error enviando OSC continuo: {e}")
    if not baseline_done and use_eeg:
        frames_left -= 1
        if frames_left <= 0:
            baseline_mu_values = []; print("\nCalculando baseline MU/SD..."); all_bands_valid = True
            for n in bands:
                arr = np.array(bands[n]['buf']);
                if arr.size > 0: bands[n]['mu']=mu_val=arr.mean(); bands[n]['sd']=arr.std() if arr.size>1 else 1e-9; print(f"  {n}: mu={mu_val:.3f}, sd={bands[n]['sd']:.3f} ({arr.size}p)")
                else: print(f"  {n}: ADVERTENCIA - Sin datos."); bands[n]['mu']=mu_val=1.0; bands[n]['sd']=1e-9; all_bands_valid = False
                bands[n]['buf']=[]; baseline_mu_values.append(mu_val)

            if all_bands_valid: print("✅ Baseline EEG completado")
            else: print("⚠️ Baseline EEG con valores defecto.")

            if not use_acc: print("✅ Baseline ACC (no seleccionado)")
            try:
                if len(baseline_mu_values)==5: print(f"Enviando MU: {[f'{x:.2f}' for x in baseline_mu_values]} | Tipos: {[type(x) for x in baseline_mu_values]}"); proc_client.send_message("/py/baseline_mu", baseline_mu_values)
                else: print("!!! ERROR: baseline_mu_values incompleta.")
            except Exception as e: print(f"Error enviando MU: {e}")
            baseline_done = True
            
    if not (baseline_done and bio_done and dist_done): refresh(line_pre())
    else: refresh(line_post())
            
    if STEP > 0:
        for _ in range(STEP):
             if eeg_buf: eeg_buf.popleft()

def muse_acc(_, x, y, z):
    if not use_acc or is_simulation: return
    if math.isnan(x) or math.isnan(y) or math.isnan(z): return
    acc.update(x=x, y=y, z=z)
    try: proc_client.send_message("/py/acc", [x, y, z])
    except Exception: pass
    for a in acc:
        rng = acc_rng[a]
        if not baseline_done: rng['min'] = acc[a] if rng['min'] is None else min(rng['min'], acc[a]); rng['max'] = acc[a] if rng['max'] is None else max(rng['max'], acc[a])
        elif baseline_done and rng['min'] is not None and rng['max'] is not None: v = scale(acc[a], rng['min'], rng['max']); set_cc('acc'+a, v)
    if not use_eeg and not baseline_done: pass
    
    if not (baseline_done and bio_done and dist_done): refresh(line_pre())
    else: refresh(line_post())

CSV = re.compile(r"([0-9.]+)[ ,]+([0-9.]+)[ ,]+([0-9.]+)[ ,]+([0-9.]+)[ ,]+([0-9.]+)[ ,]+([0-9.]+)")
def parse_serial(line: bytes):
    if is_simulation: return
    if not any((use_plant1, use_plant2, use_myo, use_dist, use_temp_hum)): return
    try: decoded_line = line.decode(errors='ignore')
    except Exception: return
    m = CSV.search(decoded_line);
    if not m: return
    try: p1, p2, di, hu, te, my = map(float, m.groups())
    except ValueError: return
    if use_plant1: update_bio('plant1', p1)
    if use_plant2: update_bio('plant2', p2)
    if use_myo: update_bio('myo', my)
    if use_dist: update_dist(di)
    if use_temp_hum:
        hum['raw'], temp['raw'] = hu, te
        if bio_done: hum['cc']=c_hum=scale(hu,0,100); set_cc('hum',c_hum); temp['cc']=c_temp=scale(te,10,40); set_cc('temp',c_temp);
        try: proc_client.send_message("/py/hum",c_hum); proc_client.send_message("/py/temp",c_temp)
        except Exception: pass
        
    if not (baseline_done and bio_done and dist_done): refresh(line_pre())
    else: refresh(line_post())

def update_bio(k, x): # ... (igual que v19) ...
    if is_simulation: return
    if not globals().get(f'use_{k}', False): return
    if math.isnan(x): return
    b = bio[k]; b['raw'] = x
    if not bio_done: b['min']=x if b['min'] is None else min(b['min'],x); b['max']=x if b['max'] is None else max(b['max'],x); b['sum']+=x; b['cnt']+=1
    elif bio_done and b['mu'] is not None and b['amp'] is not None:
        rect = abs(x - b['mu']); b['env'] = ALPHA_ENV*rect+(1-ALPHA_ENV)*b['env']; b['cc'] = c = scale(b['env'], 0, b['amp']); set_cc(k, c)
        try: proc_client.send_message(f"/py/{k}", c)
        except Exception: pass

def update_dist(x): # ... (igual que v19) ...
    if is_simulation: return
    if not use_dist: return
    if math.isnan(x): return
    d = dist; d['raw'] = x; d['filt'] = x if d['filt'] is None else ALPHA_DIST*x+(1-ALPHA_DIST)*d['filt']
    if not dist_done:
        if d['filt'] is not None and not math.isnan(d['filt']): d['min']=d['filt'] if d['min'] is None else min(d['min'],d['filt']); d['max']=d['filt'] if d['max'] is None else max(d['max'],d['filt'])
    elif dist_done and d['min'] is not None and d['max'] is not None and d['filt'] is not None:
        d['cc'] = c = scale(d['filt'], d['min'], d['max']); set_cc('dist', c)
        try: proc_client.send_message("/py/dist", c)
        except Exception: pass

def serial_loop(): # ... (igual que v19) ...
    if is_simulation: return
    if not any((use_myo, use_plant1, use_plant2, use_temp_hum, use_dist)): print("Serial loop no iniciado."); return
    ser = None
    while threads_active:
        try:
             if ser is None or not ser.is_open: ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1); print(f"Puerto serial {SERIAL_PORT} abierto/reabierto.")
             if not threads_active: break
             ln = ser.readline()
             if ln: parse_serial(ln)
             else: time.sleep(0.01)
        except serial.SerialException as e: print(f"Error serial: {e}. Reconectando en 10s...");
        except Exception as e: print(f"Error inesperado serial: {e}");
        finally:
             if 'e' in locals() and isinstance(e, serial.SerialException):
                  if ser and ser.is_open: ser.close(); ser = None; time.sleep(10)
             elif 'e' in locals(): time.sleep(1)
    if ser and ser.is_open: ser.close(); print("Puerto serial cerrado.")
# ------------------------

# --- Cerrar Baseline (Solo modo real) ---
# ... (igual que v19) ...
def close_bio():
    if is_simulation: return
    global bio_done; print("Cerrando baseline Bio...")
    for k, b in bio.items():
        if globals().get(f'use_{k}',False):
            if b['cnt']==0: print(f"Advertencia: No datos {k}"); b['mu'],b['amp']=0,1
            else: b['mu']=b['sum']/b['cnt']; b_min=b['min'] if b['min'] is not None else b['mu']; b_max=b['max'] if b['max'] is not None else b['mu']; b['amp']=max(b['mu']-b_min, b_max-b['mu']); b['amp']=max(b['amp'], 1e-9)
            b['env']=0; print(f"Baseline {k}: mu={b['mu']:.2f}, amp={b['amp']:.2f} (min={b['min']}, max={b['max']})")
    bio_done=True; print("✅ Baseline Myo/Plantas completado")
def close_dist():
    if is_simulation: return
    global dist_done; print("Cerrando baseline Dist...")
    if dist['min'] is None or dist['max'] is None or dist['min']>=dist['max']: print("Advertencia: No datos Dist"); dist['min'],dist['max']=0,100
    else: print(f"Baseline Dist: min={dist['min']:.1f}, max={dist['max']:.1f}")
    dist_done=True; print("✅ Baseline Distancia completado")
def close_eeg_acc():
    if is_simulation: return
    global baseline_done, frames_left
    if use_acc and not use_eeg and not baseline_done:
        print("Cerrando baseline ACC (solo)..."); baseline_done=True; frames_left=0; valid=True
        for a in acc:
            if acc_rng[a]['min'] is None or acc_rng[a]['max'] is None or acc_rng[a]['min']>=acc_rng[a]['max']: print(f"Advertencia: Rango ACC {a} inválido"); acc_rng[a]['min'],acc_rng[a]['max']=-1.0,1.0; valid=False
            else: print(f"Baseline Acc {a}: min={acc_rng[a]['min']:.2f}, max={acc_rng[a]['max']:.2f}")
        if valid: print("\n✅ Baseline ACC (solo) completado")
        else: print("\n⚠️ Baseline ACC (solo) con rangos defecto.")
# ---------------------

# --- Bucle de Simulación ---
# ... (igual que v19) ...
def simulation_loop():
    global baseline_done, bio_done, dist_done
    print("\n--- Iniciando Modo Simulación ---"); baseline_done = True; bio_done = True; dist_done = True
    baseline_mu_values = [MU_DEFAULTS.get(b, 1.0) for b in FILTS]
    try: print(f"Enviando Baseline MU (fijo): {[f'{x:.2f}' for x in baseline_mu_values]}"); proc_client.send_message("/py/baseline_mu", baseline_mu_values)
    except Exception as e: print(f"Error enviando baseline MU simulado: {e}")
    t_sim = 0.0; print(">>> ENTRANDO A BUCLE DE SIMULACIÓN <<<"); print("Simulación iniciada. Presiona Ctrl+C para detener.")
    while threads_active:
        try:
            row_start_time = time.time()
            # 1. Generar signed_env
            s_env_delta_sim=1.5*math.sin(0.2*t_sim+0.0); s_env_theta_sim=1.8*math.sin(0.4*t_sim+1.5); s_env_alpha_sim=2.0*math.sin(0.6*t_sim+3.0); s_env_beta_sim=1.5*math.sin(1.0*t_sim+4.5); s_env_gamma_sim=1.0*math.sin(1.5*t_sim+6.0)
            osc_band_values_signed = [s_env_delta_sim, s_env_theta_sim, s_env_alpha_sim, s_env_beta_sim, s_env_gamma_sim]
            # 2. Generar env
            env_delta_sim=0.1+((math.sin(0.22*t_sim+0.2)+1.0)/2.0)*(Z_MAX-0.2); env_theta_sim=0.1+((math.sin(0.42*t_sim+1.7)+1.0)/2.0)*(Z_MAX-0.4); env_alpha_sim=0.1+((math.sin(0.62*t_sim+3.2)+1.0)/2.0)*(Z_MAX-0.5); env_beta_sim=0.1+((math.sin(1.02*t_sim+4.7)+1.0)/2.0)*(Z_MAX-1.0); env_gamma_sim=0.1+((math.sin(1.52*t_sim+6.2)+1.0)/2.0)*(Z_MAX-1.5)
            osc_band_values_env = [env_delta_sim, env_theta_sim, env_alpha_sim, env_beta_sim, env_gamma_sim]
            # 3. Generar ACC
            accX_sim=0.8*math.sin(0.15*t_sim); accY_sim=0.6*math.cos(0.12*t_sim+1.0); accZ_sim=0.1*math.sin(0.08*t_sim+2.0); osc_acc_values = [accX_sim, accY_sim, accZ_sim]
            # 4. Actualizar estado interno y MIDI
            for i, n in enumerate(FILTS.keys()): bands[n]['signed_env'] = osc_band_values_signed[i]; bands[n]['env'] = osc_band_values_env[i]; bands[n]['cc'] = scale(bands[n]['env'], 0, Z_MAX); set_cc(n, bands[n]['cc'])
            for i, a in enumerate(['x', 'y', 'z']): acc[a] = osc_acc_values[i]; set_cc('acc'+a, scale(acc[a], -1.0, 1.0))
            # 5. Enviar OSC
            proc_client.send_message("/py/bands_signed_env", osc_band_values_signed); proc_client.send_message("/py/bands_env", osc_band_values_env); proc_client.send_message("/py/acc", osc_acc_values)
            # 6. Imprimir estado
            refresh(line_post())
            # 7. Incrementar tiempo y esperar
            t_sim += PERIOD; time_spent = time.time() - row_start_time; time.sleep(max(0, PERIOD - time_spent))
        except Exception as e: print(f"\n!!! Error en simulation_loop: {e}"); time.sleep(1)
# ---------------------------

# --- Logs, Servidor OSC, Timers ---
logging.getLogger('pythonosc').setLevel(logging.ERROR); disp = Dispatcher()
if not is_simulation:
    if use_eeg: disp.map("/desdemuse/eeg", muse_eeg)
    if use_acc: disp.map("/desdemuse/acc", muse_acc)
needs_baseline_calibration = not is_simulation and any((use_eeg, use_acc, use_myo, use_plant1, use_plant2, use_dist))
if needs_baseline_calibration: print(f"► Iniciando baseline ({BASE_SEC}s).");
elif not is_simulation: print("► No se requiere baseline.")
if not is_simulation:
    if use_myo or use_plant1 or use_plant2: threading.Timer(BASE_SEC, close_bio).start()
    if use_dist: threading.Timer(BASE_SEC, close_dist).start()
    if use_acc and not use_eeg: threading.Timer(BASE_SEC, close_eeg_acc).start()
# --------------------------------

# --- Lanzar Loops ---
threads_active = True
midi_thread = None; serial_thread = None
if any(sig in MIDI_OUT and not MIDI_OUT[sig].name.startswith("fake_") for sig in TARGET_CC): midi_thread = threading.Thread(target=midi_tick, daemon=True); midi_thread.start()
else: print("⚠️ No MIDI activo.")
if not is_simulation and any((use_myo, use_plant1, use_plant2, use_temp_hum, use_dist)): serial_thread = threading.Thread(target=serial_loop, daemon=True); serial_thread.start()
elif not is_simulation: print("⚠️ No Arduino activo.")

muse_selected = not is_simulation and (use_eeg or use_acc)
arduino_selected = not is_simulation and any((use_myo, use_plant1, use_plant2, use_temp_hum, use_dist))

print("\n--- Estado de Ejecución ---")
if is_simulation: print("Modo: SIMULACIÓN")
else: print(f"Modo: REAL (Muse: {muse_selected}, Arduino: {arduino_selected})")

server = None; main_loop_running = True
try:
    input("Presiona Enter para iniciar bucle principal...")

    if is_simulation:
        print("Entrando a simulation_loop...")
        simulation_loop() # Bucle simulador
    elif muse_selected: # Modo Real con Muse
        print("Iniciando servidor OSC...")
        try: server = BlockingOSCUDPServer(("0.0.0.0", OSC_PORT), disp); print(f"OSC escuchando en puerto {OSC_PORT}...")
        except OSError as e: print(f"[OSC] Error {OSC_PORT}: {e}"); main_loop_running = False; raise
        except Exception as e: print(f"[OSC] Error inesperado inicio: {e}"); main_loop_running = False; raise
        print("Entrando a bucle OSC...")
        while main_loop_running: server.handle_request(); time.sleep(0.001) # Bucle OSC
    elif arduino_selected: # Modo Real solo Arduino
        print("Solo Arduino. Ctrl+C para salir.")
        while main_loop_running: time.sleep(1) # Bucle Arduino
    else: # Modo Real sin sensores
        if valid_choice: print("No se seleccionaron sensores activos.")
        main_loop_running = False

except KeyboardInterrupt: print("\nCtrl+C detectado. Saliendo..."); main_loop_running = False
except Exception as e:
    print(f"\n!!! ERROR INESPERADO EN BUCLE PRINCIPAL: {e}")
    import traceback; traceback.print_exc()
    main_loop_running = False
finally:
    threads_active = False
    print("Iniciando cierre...")
    time.sleep(0.5)
    if server: print("Cerrando servidor OSC...");
    try:
        if server: server.shutdown(); server.server_close()
    except Exception as e: print(f"  Error al cerrar OSC: {e}")
    print("Programa finalizado.")
    input("Presiona Enter para cerrar la consola...") # Pausa final
    sys.exit(0)
# --- FIN Lanzar Loops ---