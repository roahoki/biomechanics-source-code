#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT PYTHON (v25-full)
- Extiende v24 con capacidad de reproducir datos desde CSV
- Integra todas las funciones de v24 (handlers OSC, baseline, etc.)
- Mantiene compatibilidad con modo simulación y sensor en vivo
"""

import sys
import time
import os
import math, re, threading, logging, socket
from collections import deque
from pythonosc.udp_client import SimpleUDPClient
from datetime import datetime
import csv

# --- Dependencias ---
try:
    import numpy as np
    import scipy.signal as sg
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
    import pandas as pd
except ImportError as e:
    print(f"!!! ERROR: Falta librería: {e}\nInstala: pip install numpy scipy python-osc pandas")
    input("Enter...")
    sys.exit(1)

# --- Pausa inicial ---
print("="*60)
print("  BIOMECHANICS OSC PROCESSOR v25-full")
print("="*60)
print("Esta ventana debe permanecer abierta.\n")

# --- Modo de ejecución ---
EXECUTION_MODE = 'live'
CSV_REPLAY_FILE = None
CSV_REPLAY_SPEED = 1.0

# --- Funciones básicas ---
def get_local_ip():
    s=None; ip="127.0.0.1";
    try: s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]
    except Exception:
        try: ip=socket.gethostbyname(socket.gethostname())
        except Exception: print("⚠️ ADVERTENCIA: No IP. Usando 127.0.0.1")
    finally:
        if s: s.close()
    return ip

def preguntar_bool(texto):
    """Pregunta al usuario sí/no con validación y reintentos"""
    while True:
        resp = input(texto + " (s/n): ").strip().lower()
        if resp in ('s', 'si', 'sí', 'yes'):
            return True
        elif resp in ('n', 'no'):
            return False
        else:
            print("❌ Valor no permitido. Ingresa 's' (sí) o 'n' (no).")

# Variables globales
is_simulation = False
use_eeg = use_acc = use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False
use_ppg = use_gyro = use_jaw = False
baseline_duration_seconds = 10

def list_available_csv_files():
    """Lista archivos CSV disponibles en el directorio del script"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_files = [f for f in os.listdir(script_dir) if f.endswith('.csv') and f.startswith('meditacion_')]
    csv_files.sort(reverse=True)
    return csv_files, script_dir

def get_csv_info(csv_path):
    """Obtiene número de líneas y duración del CSV"""
    try:
        df = pd.read_csv(csv_path)
        if 'timestamp' in df.columns:
            df = df[~df['timestamp'].astype(str).str.startswith('#')]
        num_lines = len(df)
        duration_sec = 0
        if 'time_sec' in df.columns:
            max_time = df['time_sec'].max()
            if pd.notna(max_time):
                duration_sec = int(max_time)
            else:
                duration_sec = int(num_lines / 10)
        else:
            duration_sec = int(num_lines / 10)
        return num_lines, duration_sec
    except Exception:
        return 0, 0

def show_main_menu():
    """Muestra el menú principal con opción de replay CSV."""
    global is_simulation, use_eeg, use_acc, use_ppg, use_myo, use_temp_hum
    global use_plant1, use_plant2, use_dist, baseline_duration_seconds
    global in_menu, pause_outputs, save_data
    global EXECUTION_MODE, CSV_REPLAY_FILE, CSV_REPLAY_SPEED
    
    in_menu = False
    pause_outputs = False
    
    print("\n=== SELECCIÓN DE FUENTE DE DATOS ===")
    print("0. Modo Simulador (Datos Falsos)")
    print("1. Sensor Cerebral en Vivo (Muse)")
    print("2. Reproducir desde CSV")
    print("3. Salir")
    choice = input("Selecciona una opción (0-3): ").strip()

    is_simulation = (choice == '0')
    use_eeg = use_acc = use_ppg = use_myo = use_temp_hum = False
    use_plant1 = use_plant2 = use_dist = use_gyro = use_jaw = False
    save_data = False
    baseline_duration_seconds = 10

    if is_simulation:
        print("\n--- MODO SIMULADOR ACTIVADO ---")
        EXECUTION_MODE = 'simulation'
        use_eeg = True
        use_acc = True
        use_ppg = False
        
    elif choice == '1':
        print("\n" + "="*50)
        print(f"    ► App Muse -> IP: {MY_LOCAL_IP} | Puerto: {OSC_PORT}")
        print("="*50 + "\n")
        EXECUTION_MODE = 'live'
        print("--- Config Sensor Cerebral ---")
        use_eeg = preguntar_bool("¿Ondas?")
        use_acc = preguntar_bool("¿Accel?")
        use_ppg = preguntar_bool("¿Heartbeat/PPG?")
        save_data = preguntar_bool("¿Guardar datos?")
        
        if use_eeg:
            while True:
                try:
                    baseline_str = input("⏱️  Duración baseline (10-30s, default=10): ").strip()
                    baseline_duration_seconds = int(baseline_str) if baseline_str else 10
                    if baseline_duration_seconds <= 0:
                        print("⚠️ Debe ser > 0")
                        continue
                    if baseline_duration_seconds > 120:
                        print("⚠️ Máximo 120s")
                        continue
                    print(f"✓ Baseline: {baseline_duration_seconds}s")
                    break
                except ValueError:
                    print("⚠️ Número válido")
                    
    elif choice == '2':
        print("\n--- MODO REPRODUCCIÓN CSV ---")
        EXECUTION_MODE = 'csv_replay'
        
        csv_files, script_dir = list_available_csv_files()
        
        if not csv_files:
            print(f"❌ No se encontraron archivos CSV (meditacion_*.csv) en: {script_dir}")
            show_main_menu()
            return
        
        print("\n📊 Archivos CSV disponibles:\n")
        for idx, filename in enumerate(csv_files, 1):
            csv_path = os.path.join(script_dir, filename)
            num_lines, duration_sec = get_csv_info(csv_path)
            file_size = os.path.getsize(csv_path) / 1024
            try:
                timestamp_part = filename.replace('meditacion_', '').replace('.csv', '')
                date_str = f"{timestamp_part[:4]}-{timestamp_part[4:6]}-{timestamp_part[6:8]}"
                time_str = f"{timestamp_part[9:11]}:{timestamp_part[11:13]}:{timestamp_part[13:15]}"
                duration_str = f"{duration_sec // 60}m {duration_sec % 60}s" if duration_sec >= 60 else f"{duration_sec}s"
                print(f"{idx}. {filename}")
                print(f"   📅 {date_str} {time_str} | 📈 {num_lines} líneas | ⏱️  {duration_str} | 📁 {file_size:.1f}KB\n")
            except Exception as e:
                print(f"{idx}. {filename} (Error: {e})\n")
        
        print(f"{len(csv_files) + 1}. Escribir ruta manualmente")
        print("0. Volver al menú")
        
        csv_choice = input(f"\nSelecciona archivo (0-{len(csv_files) + 1}): ").strip()
        
        try:
            csv_idx = int(csv_choice)
            
            if csv_idx == 0:
                show_main_menu()
                return
            elif csv_idx == len(csv_files) + 1:
                csv_path = input("Ruta del archivo CSV: ").strip()
            elif 1 <= csv_idx <= len(csv_files):
                csv_path = os.path.join(script_dir, csv_files[csv_idx - 1])
            else:
                print("❌ Opción inválida")
                show_main_menu()
                return
                
        except ValueError:
            print("❌ Opción inválida")
            show_main_menu()
            return
        
        if not os.path.exists(csv_path):
            print(f"❌ Archivo no encontrado: {csv_path}")
            show_main_menu()
            return
            
        CSV_REPLAY_FILE = csv_path
        
        num_lines, duration_sec = get_csv_info(csv_path)
        duration_str = f"{duration_sec // 60}m {duration_sec % 60}s" if duration_sec >= 60 else f"{duration_sec}s"
        
        speed_str = input(f"\nVelocidad de reproducción (1.0=normal, 2.0=2x, 0.5=mitad, default=1.0): ").strip()
        try:
            CSV_REPLAY_SPEED = float(speed_str) if speed_str else 1.0
            if CSV_REPLAY_SPEED <= 0:
                CSV_REPLAY_SPEED = 1.0
        except ValueError:
            CSV_REPLAY_SPEED = 1.0
        
        adjusted_duration = int(duration_sec / CSV_REPLAY_SPEED)
        adjusted_duration_str = f"{adjusted_duration // 60}m {adjusted_duration % 60}s" if adjusted_duration >= 60 else f"{adjusted_duration}s"
            
        print(f"\n✓ Archivo seleccionado: {os.path.basename(CSV_REPLAY_FILE)}")
        print(f"✓ Velocidad: {CSV_REPLAY_SPEED}x")
        print(f"✓ Duración original: {duration_str}")
        print(f"✓ Duración ajustada: {adjusted_duration_str}")
        print(f"✓ Total de líneas: {num_lines}")
        
        try:
            df = pd.read_csv(CSV_REPLAY_FILE, nrows=5)
            use_eeg = 'delta_rms' in df.columns
            use_acc = 'acc_x' in df.columns
            use_ppg = 'ppg_bpm' in df.columns
            
            print(f"\n📊 Sensores detectados en CSV:")
            print(f"   EEG: {'✓' if use_eeg else '✗'}")
            print(f"   ACC: {'✓' if use_acc else '✗'}")
            print(f"   PPG: {'✓' if use_ppg else '✗'}")
        except Exception as e:
            print(f"⚠️ Error leyendo CSV: {e}")
            show_main_menu()
            return
        
    elif choice == '3':
        print("Saliendo...")
        return_to_menu(exit_app=True)
    else:
        print("Opción inválida.")
        show_main_menu()

def detect_serial_port():
    """Detecta automáticamente el puerto serial según el SO"""
    import platform
    import glob

    sistema = platform.system()

    if sistema == "Windows":
        return None

    candidates = glob.glob("/dev/tty.usbserial*") + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*") + glob.glob('/dev/cu.*')
    return candidates[0] if candidates else None

# --- Motor de reproducción CSV ---
class CSVReplayEngine:
    """Motor de reproducción de datos desde CSV"""
    
    def __init__(self, csv_file, speed_factor=1.0):
        self.csv_file = csv_file
        self.speed_factor = speed_factor
        self.df = None
        self.current_index = 0
        self.start_time = None
        self.paused = False
        self.last_time = 0
        
    def load(self):
        """Carga el archivo CSV"""
        try:
            self.df = pd.read_csv(self.csv_file)
            
            if 'timestamp' in self.df.columns:
                self.df = self.df[~self.df['timestamp'].astype(str).str.startswith('#')]
                self.df = self.df.reset_index(drop=True)
            
            print(f"✓ CSV cargado: {len(self.df)} registros")
            print(f"Columnas: {list(self.df.columns)[:10]}...")
            
            if 'time_sec' not in self.df.columns:
                print("⚠️ No se encontró columna 'time_sec', usando índice como tiempo")
                self.df['time_sec'] = self.df.index * 0.1
                
            return True
        except Exception as e:
            print(f"✗ Error cargando CSV: {e}")
            return False
    
    def get_next_sample(self):
        """Obtiene la siguiente muestra con timing real"""
        if self.current_index >= len(self.df):
            return None
        
        if self.paused:
            return None
            
        row = self.df.iloc[self.current_index]
        
        current_time = row.get('time_sec', self.current_index * 0.1)
        
        if self.current_index > 0:
            time_diff = current_time - self.last_time
            if time_diff > 0:
                time.sleep(time_diff / self.speed_factor)
        
        self.last_time = current_time
        self.current_index += 1
        return row
    
    def reset(self):
        """Reinicia la reproducción"""
        self.current_index = 0
        self.start_time = time.time()
        self.last_time = 0
    
    def get_progress(self):
        """Retorna progreso 0-100"""
        if self.df is None or len(self.df) == 0:
            return 0
        return int((self.current_index / len(self.df)) * 100)

# --- Config Inicial ---
OSC_PORT = 5001
MY_LOCAL_IP = get_local_ip()

# Mostrar menú
show_main_menu()

any_sensor_selected = any((use_eeg, use_acc, use_ppg, use_gyro, use_jaw, use_myo, use_temp_hum, use_plant1, use_plant2, use_dist))
if not any_sensor_selected and not is_simulation and EXECUTION_MODE != 'csv_replay':
    print("\nAdvertencia: Ningún sensor específico fue seleccionado.")
if True:
    print("="*40+"\n")

# --- Config OSC ---
SERIAL_PORT = detect_serial_port()
if SERIAL_PORT is None:
    SERIAL_PORT = "COM3"

BAUD = 115200
PROC_IP = "127.0.0.1"
PROC_PORT = 5002
proc_client = None
try:
    proc_client=SimpleUDPClient(PROC_IP, PROC_PORT)
    print("="*50+f"\n    ► Enviando a Processing -> IP: {PROC_IP} | Puerto: {PROC_PORT}\n"+"="*50+"\n")
except Exception as e:
    print(f"!!! ERROR FATAL creando cliente OSC: {e}")
    input("Enter...")
    sys.exit(1)

# --- Globales para control ---
in_recalibration = False
pause_outputs = False
debug_mode = False
show_realtime_data = True
in_menu = False
exit_requested = False

def send_proc(path, data, force=False):
    """Enviar OSC a Processing"""
    global pause_outputs, proc_client
    try:
        if pause_outputs and not force:
            return
        if proc_client is not None:
            proc_client.send_message(path, data)
    except BlockingIOError:
        pass
    except Exception:
        pass

def send_baseline_event(phase, event_type, duration=0):
    """Enviar eventos de baseline a TouchDesigner."""
    try:
        if event_type == "start":
            send_proc("/py/baseline/start", [phase, duration], force=True)
        elif event_type == "progress":
            send_proc(f"/py/baseline/{phase}/progress", float(duration), force=True)
        elif event_type == "end":
            send_proc("/py/baseline/end", [phase], force=True)
    except Exception as e:
        if debug_mode:
            print(f"Error enviando evento baseline: {e}")

# --- Grabador de datos ---
class DataRecorder:
    """Registra datos de sensores a CSV cada 1 segundo post-baseline"""
    def __init__(self, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meditacion_{timestamp}.csv"
        self.filename = filename
        self.file = None
        self.writer = None
        self.last_write_time = None
        self.baseline_data_written = False
        
    def start(self):
        """Abre archivo e inicia grabación"""
        try:
            self.file = open(self.filename, 'w', newline='')
            self.writer = csv.DictWriter(self.file, fieldnames=self._get_fieldnames())
            self.writer.writeheader()
            self.file.flush()
            safe_print(f"📁 Grabando datos en: {self.filename}")
        except Exception as e:
            safe_print(f"Error iniciando DataRecorder: {e}")
            
    def _get_fieldnames(self):
        """Retorna lista de campos para el CSV"""
        fields = ['timestamp', 'time_sec']
        if use_eeg:
            for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                fields.extend([f'{band}_rms', f'{band}_env', f'{band}_cc'])
        if use_acc:
            fields.extend(['acc_x', 'acc_y', 'acc_z', 'acc_x_dev', 'acc_y_dev', 'acc_z_dev'])
        if use_ppg:
            fields.extend(['ppg_bpm', 'ppg_cc'])
        return fields
    
    def write_baseline_metadata(self):
        """Escribe información del baseline como comentarios"""
        if self.baseline_data_written or self.file is None:
            return
        try:
            self.file.write("\n# === BASELINE DATA ===\n")
            if use_eeg and baseline_eeg_values:
                for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                    if band in baseline_eeg_values:
                        mu = baseline_eeg_values[band].get('mu', 0.0)
                        sigma = baseline_eeg_values[band].get('sigma', 0.0)
                        self.file.write(f"# {band.upper()}: μ={float(mu):.2f} σ={float(sigma):.2f}\n")
            self.file.write("# === DATA START ===\n")
            self.file.flush()
            self.baseline_data_written = True
        except Exception as e:
            safe_print(f"Error escribiendo baseline metadata: {e}")
    
    def write_data(self, elapsed_seconds):
        """Escribe una fila de datos si pasó 1 segundo desde la última"""
        if self.file is None or self.writer is None:
            return
        
        now = time.time()
        if self.last_write_time is None:
            self.last_write_time = now
        
        if now - self.last_write_time < 1.0:
            return
        
        try:
            row = {
                'timestamp': datetime.now().isoformat(),
                'time_sec': f"{elapsed_seconds:.1f}"
            }
            if use_eeg:
                for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                    row[f'{band}_rms'] = bands[band].get('rms', '')
                    row[f'{band}_env'] = bands[band].get('env', '')
                    row[f'{band}_cc'] = bands[band].get('cc', '')
            if use_acc:
                for axis in ['x', 'y', 'z']:
                    row[f'acc_{axis}'] = acc.get(axis, '')
                    baseline_val = acc_baseline.get(axis, 0)
                    current_val = acc.get(axis, 0)
                    row[f'acc_{axis}_dev'] = f"{current_val - baseline_val:.4f}"
            if use_ppg:
                row['ppg_bpm'] = ppg.get('bpm', '')
                row['ppg_cc'] = ppg.get('cc', '')
            self.writer.writerow(row)
            self.file.flush()
            self.last_write_time = now
        except Exception as e:
            safe_print(f"Error escribiendo datos: {e}")
    
    def close(self):
        """Cierra el archivo"""
        if self.file:
            try:
                self.file.close()
                safe_print(f"✅ Datos guardados: {self.filename}")
            except Exception as e:
                safe_print(f"Error cerrando archivo: {e}")

# --- CONSTANTES ---
SRATE, WIN_S=256, 2
WIN, STEP=SRATE*WIN_S, (SRATE*WIN_S)//2
BASE_SEC = baseline_duration_seconds if use_eeg and not is_simulation else 10
Z_MAX, ALPHA_ENV, DEAD_ZONE, ALPHA_DIST=3.0, 0.3, 0.2, 0.25
UPDATE_HZ=10.0; SLEW_PER_SEC=25; MIN_STEP_CC=1; CURVE_MODE="exp"; CURVE_K=0.65
PERIOD = 1.0 / UPDATE_HZ

MU_DEFAULTS = {'delta': 1.2, 'theta': 1.0, 'alpha': 1.0, 'beta': 0.8, 'gamma': 0.5}
SD_DEFAULTS = {'delta': 0.4, 'theta': 0.3, 'alpha': 0.3, 'beta': 0.25, 'gamma': 0.2}

MIDI_PREFIX={'delta':'delta_midi','theta':'theta_midi','alpha':'alpha_midi','beta':'beta_midi','gamma':'gamma_midi','accx':'x_midi','accy':'y_midi','accz':'z_midi','plant1':'plant1_midi','plant2':'plant2_midi','myo':'myoware_midi','dist':'dist_midi','hum':'hum_midi','temp':'temp_midi'}
MIDI_CH={**{s:0 for s in ('delta','theta','alpha','beta','gamma')},**{s:0 for s in ('accx','accy','accz')},'plant1':0,'plant2':1,'myo':2,'dist':3,'hum':4,'temp':5}
CC_NUM={'delta':17,'theta':16,'alpha':14,'beta':15,'gamma':18,'accx':20,'accy':21,'accz':22,'plant1':40,'plant2':41,'myo':42,'dist':43,'hum':44,'temp':45}

# --- Utilidades Señal ---
def butter(lo, hi, fs=SRATE):
    nyq=fs*0.5
    return sg.butter(4, [lo/nyq, hi/nyq], 'band')

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

def env_z(v, mu, sd, prev):
    if sd<=1e-9 or mu is None or math.isnan(v): return prev
    z = abs(v - mu) / sd
    current_env = ALPHA_ENV*z+(1-ALPHA_ENV)*prev if z>=DEAD_ZONE else prev*(1-ALPHA_ENV)
    return max(0.0, current_env)

def scale(x, lo, hi):
    if lo is None or hi is None or hi <= lo or math.isnan(x): return 0
    return max(0, min(127, round((x-lo)/(hi-lo)*127)))

# --- MIDI ---
def open_midi():
    print("MIDI support disabled in this build — no MIDI ports will be opened.")
    return {}

MIDI_OUT = {}
print("MIDI disabled — routing MIDI handled externally (TouchDesigner/Ableton)")

TARGET_CC={k: 0 for k in CC_NUM}; LAST_CC={k: 0 for k in CC_NUM}
threads_active = True

def cc_curve(cc, mode=CURVE_MODE,k=CURVE_K):
    x=max(0,min(127,cc))/127.0
    y=x**(1-k) if mode=="exp" else (1.0-(1.0-x)**(1-k) if mode=="log" else x)
    return int(round(y*127))

def _send_cc(sig, val):
    return

def set_cc(sig, val):
    if sig in CC_NUM:
        TARGET_CC[sig] = int(max(0, min(127, val)))

def midi_tick():
    period=PERIOD; max_step=int(round(SLEW_PER_SEC/UPDATE_HZ))
    print("... Hilo MIDI iniciado ...")
    while threads_active:
        try:
            t0=time.time()
            for sig in TARGET_CC:
                prev=LAST_CC.get(sig, 0)
                target=TARGET_CC.get(sig, 0)
                step=max(-max_step, min(max_step, target-prev))
                raw=prev+step
                shaped=cc_curve(raw)
                if abs(shaped-prev)>=MIN_STEP_CC:
                    LAST_CC[sig]=shaped
                    _send_cc(sig, shaped)
            dt=time.time()-t0
            time.sleep(max(0.0, period-dt))
        except Exception as e:
            print(f"\n!!! Error en midi_tick: {e}")
            time.sleep(1)
    print("... Hilo MIDI terminado.")

# --- Estados ---
bands = {b: dict(rms=np.nan, env=0, signed_env=0.0, mu=MU_DEFAULTS.get(b, 1.0) if is_simulation else None, sd=SD_DEFAULTS.get(b, 1.0) if is_simulation else None, cc=0, buf=[]) for b in FILTS}
acc = {'x':0.0, 'y':0.0, 'z':0.0}
acc_baseline = {'x': 0.0, 'y': 0.0, 'z': 0.0}
acc_rng = {a: dict(min=None, max=None) for a in acc}

baseline_acc_x = {'neutral': None, 'min': None, 'max': None, 'range': None}
baseline_acc_y = {'neutral': None, 'min': None, 'max': None, 'range': None}
baseline_acc_z = {'neutral': None, 'min': None, 'max': None, 'range': None}

baseline_eeg_values = {}

bio = {k: dict(raw=None, env=0, mu=None, amp=None, min=None, max=None, sum=0, cnt=0, cc=0) for k in ('plant1', 'plant2', 'myo')}
dist = dict(raw=None, filt=None, min=None, max=None, cc=0)
hum, temp = dict(raw=None, cc=0), dict(raw=None, cc=0)

ppg = dict(raw=None, cc=0, bpm=0.0, buffer=deque(maxlen=10))
gyro = dict(x=0.0, y=0.0, z=0.0, cc=0)
jaw = dict(clenched=0, cc=0)

eeg_buf = deque(maxlen=WIN)

baseline_eeg_start_sent = False
baseline_acc_neutral_start_sent = False
baseline_acc_movement_start_sent = False

needs_baseline_calibration = not is_simulation and any((use_eeg, use_acc, use_myo, use_plant1, use_plant2, use_dist))

frames_left_eeg = int(BASE_SEC / (STEP / SRATE)) if needs_baseline_calibration and use_eeg else 0
baseline_eeg_done = not needs_baseline_calibration or not use_eeg

baseline_acc_neutral_duration = 5
baseline_acc_movement_duration = 10
frames_left_acc_neutral = int(baseline_acc_neutral_duration / (STEP / SRATE)) if needs_baseline_calibration and use_acc else 0
frames_left_acc_movement = 0
baseline_acc_neutral_done = not needs_baseline_calibration or not use_acc
baseline_acc_movement_done = not needs_baseline_calibration or not use_acc
baseline_acc_done = baseline_acc_neutral_done and baseline_acc_movement_done
acc_neutral_start_time = None
acc_movement_start_time = None

frames_left_bio = int(BASE_SEC / (STEP / SRATE)) if needs_baseline_calibration and any((use_plant1, use_plant2, use_myo)) else 0
bio_done = not needs_baseline_calibration or not any((use_plant1, use_plant2, use_myo))

frames_left_dist = int(BASE_SEC / (STEP / SRATE)) if needs_baseline_calibration and use_dist else 0
dist_done = not needs_baseline_calibration or not use_dist

baseline_done = baseline_eeg_done and baseline_acc_done and bio_done and dist_done
frames_left = frames_left_eeg if use_eeg else frames_left_acc_neutral

if not baseline_eeg_done:
    baseline_phase = "eeg"
elif not baseline_acc_neutral_done:
    baseline_phase = "acc_neutral"
elif not baseline_acc_movement_done:
    baseline_phase = "acc_movement"
else:
    baseline_phase = "complete"

# --- Impresión ---
PREV_LEN=0

def safe_print(*args, **kwargs):
    """Imprime de forma robusta"""
    try:
        print(*args, **kwargs)
    except:
        pass

def refresh(text):
    global PREV_LEN, show_realtime_data
    if not show_realtime_data:
        return
    pad=text.ljust(PREV_LEN)
    try:
        sys.stdout.write('\r'+pad)
        sys.stdout.flush()
    except:
        pass
    PREV_LEN=len(text)

# --- Recalibración y Shortcuts ---
def recalibration_routine():
    """Inicia rutina de recalibración manual"""
    global in_recalibration, baseline_eeg_done, baseline_acc_neutral_done, baseline_acc_movement_done
    global baseline_eeg_start_sent, baseline_acc_neutral_start_sent, baseline_acc_movement_start_sent
    global frames_left_eeg, frames_left_acc_neutral, frames_left_acc_movement, baseline_done, baseline_phase
    global acc_neutral_start_time, acc_movement_start_time, baseline_eeg_values
    
    if in_recalibration:
        return
    
    in_recalibration = True
    
    try:
        safe_print("\n" + "="*50)
        safe_print("    🔄 RECALIBRACIÓN INICIADA")
        safe_print("="*50)
        
        baseline_eeg_done = not use_eeg
        baseline_acc_neutral_done = not use_acc
        baseline_acc_movement_done = not use_acc
        baseline_eeg_start_sent = False
        baseline_acc_neutral_start_sent = False
        baseline_acc_movement_start_sent = False
        
        frames_left_eeg = int(BASE_SEC / (STEP / SRATE)) if use_eeg else 0
        frames_left_acc_neutral = int(baseline_acc_neutral_duration / (STEP / SRATE)) if use_acc else 0
        frames_left_acc_movement = 0
        
        baseline_eeg_values = {}
        for band in FILTS:
            bands[band]['buf'] = []
            bands[band]['mu'] = None
            bands[band]['sd'] = None
        
        acc_neutral_start_time = None
        acc_movement_start_time = None
        
        while not baseline_done and threads_active:
            time.sleep(0.1)
        
        safe_print("\n✅ Recalibración completada")
        safe_print("="*50 + "\n")
        
    except Exception as e:
        safe_print(f"Error en recalibración: {e}")
    
    finally:
        in_recalibration = False

def trigger_recalibration():
    """Dispara recalibración en un thread separado"""
    if not baseline_eeg_done or not baseline_acc_done:
        return
    
    thread = threading.Thread(target=recalibration_routine, daemon=True)
    thread.start()

def listen_shortcuts():
    """Escucha comandos de teclado (Ctrl+B, Ctrl+D, etc.)"""
    global debug_mode, show_realtime_data, pause_outputs, in_menu, threads_active
    global baseline_done, EXECUTION_MODE
    
    try:
        import platform
        if platform.system() == "Windows":
            import msvcrt
            safe_print("\n[Shortcuts] Ctrl+B=Recalibrate | Ctrl+D=Debug | Ctrl+R=Display | Ctrl+Q=Quit | Ctrl+M=Menu\n")
            while threads_active:
                try:
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        
                        if key == b'\x02':
                            trigger_recalibration()
                        elif key == b'\x04':
                            debug_mode = not debug_mode
                            safe_print(f"Debug: {debug_mode}")
                        elif key == b'\x12':
                            show_realtime_data = not show_realtime_data
                            safe_print(f"Display: {show_realtime_data}")
                        elif key == b'\x17':
                            return_to_menu(exit_app=True)
                        elif key == b'\x0d':
                            in_menu = True
                    
                    time.sleep(0.05)
                except Exception:
                    time.sleep(0.1)
        else:
            safe_print("\n[Shortcuts] Disponibles en Windows\n")
            while threads_active:
                time.sleep(0.1)
    
    except Exception as e:
        safe_print(f"Shortcut listener error: {e}")

def return_to_menu(exit_app=False):
    global exit_requested, threads_active
    if exit_app:
        print("\n⏹️  Preparando salida...")
        exit_requested = True
        threads_active = False
        time.sleep(0.5)
        sys.exit(0)

# --- CSV Replay Loop ---
def csv_replay_loop():
    """Bucle de reproducción desde CSV"""
    global baseline_done
    
    print(f"\n🎬 Iniciando reproducción de {CSV_REPLAY_FILE}")
    print(f"Velocidad: {CSV_REPLAY_SPEED}x")
    
    replay_engine = CSVReplayEngine(CSV_REPLAY_FILE, CSV_REPLAY_SPEED)
    
    if not replay_engine.load():
        print("❌ Error cargando CSV")
        return
    
    baseline_done = True
    print("\n▶️  Reproducción iniciada (Ctrl+C para detener)\n")
    print("Progreso: [                    ] 0%")
    
    last_progress_print = 0
    
    try:
        while threads_active:
            sample = replay_engine.get_next_sample()
            
            if sample is None:
                print("\n✓ Reproducción completada")
                break
            
            if use_eeg:
                try:
                    bands_env = [
                        float(sample.get('delta_env', 0)),
                        float(sample.get('theta_env', 0)),
                        float(sample.get('alpha_env', 0)),
                        float(sample.get('beta_env', 0)),
                        float(sample.get('gamma_env', 0))
                    ]
                    bands_signed = bands_env
                    send_proc("/py/bands_env", bands_env)
                    send_proc("/py/bands_signed_env", bands_signed)
                    bands_raw = [
                        float(sample.get('delta_rms', 0)),
                        float(sample.get('theta_rms', 0)),
                        float(sample.get('alpha_rms', 0)),
                        float(sample.get('beta_rms', 0)),
                        float(sample.get('gamma_rms', 0))
                    ]
                    send_proc("/py/bands_raw", bands_raw)
                except Exception as e:
                    if debug_mode:
                        print(f"Error enviando EEG: {e}")
            
            if use_acc:
                try:
                    acc_data = [
                        float(sample.get('acc_x', 0)),
                        float(sample.get('acc_y', 0)),
                        float(sample.get('acc_z', 0))
                    ]
                    send_proc("/py/acc", acc_data)
                except Exception as e:
                    if debug_mode:
                        print(f"Error enviando ACC: {e}")
            
            if use_ppg:
                try:
                    ppg_bpm = float(sample.get('ppg_bpm', 0))
                    send_proc("/py/ppg/bpm", ppg_bpm)
                except Exception as e:
                    if debug_mode:
                        print(f"Error enviando PPG: {e}")
            
            progress = replay_engine.get_progress()
            time_sec = float(sample.get('time_sec', 0))
            
            if progress >= last_progress_print + 5:
                progress_bar = "█" * (progress // 5) + " " * (20 - progress // 5)
                sys.stdout.write(f"\rProgreso: [{progress_bar}] {progress}% | ⏱️  {time_sec:.1f}s")
                sys.stdout.flush()
                last_progress_print = progress
    
    except KeyboardInterrupt:
        print("\n\n⏸️  Reproducción detenida por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante reproducción: {e}")

def simulation_loop():
    """Bucle de simulación"""
    global baseline_done
    baseline_done = True
    print("\n--- Iniciando Modo Simulación ---")
    
    baseline_mu_values = [MU_DEFAULTS.get(b, 1.0) for b in FILTS]
    send_proc("/py/baseline_mu", baseline_mu_values, force=True)
    
    t_sim = 0.0
    print("Simulación iniciada. Presiona Ctrl+C para detener.")
    
    while threads_active:
        try:
            s0 = 1.5*math.sin(0.2*t_sim+0.0)
            s1 = 1.8*math.sin(0.4*t_sim+1.5)
            s2 = 2.0*math.sin(0.6*t_sim+3.0)
            s3 = 1.5*math.sin(1.0*t_sim+4.5)
            s4 = 1.0*math.sin(1.5*t_sim+6.0)
            
            osc_signed = [s0, s1, s2, s3, s4]
            osc_env = [abs(v) for v in osc_signed]
            
            accX = 0.8*math.sin(0.15*t_sim)
            accY = 0.6*math.cos(0.12*t_sim+1.0)
            accZ = 0.1*math.sin(0.08*t_sim+2.0)
            
            send_proc("/py/bands_signed_env", osc_signed)
            send_proc("/py/bands_env", osc_env)
            send_proc("/py/acc", [accX, accY, accZ])
            
            t_sim += PERIOD
            time.sleep(PERIOD)
            
        except Exception as e:
            print(f"Error en simulación: {e}")
            time.sleep(1)

# --- MAIN LOOP ---
logging.getLogger('pythonosc').setLevel(logging.ERROR)

# --- HANDLERS OSC ---
def close_baseline_eeg():
    """Finaliza baseline EEG calculando μ y σ para cada banda"""
    global baseline_eeg_done, baseline_eeg_values
    if baseline_eeg_done:
        return
    
    safe_print("\n✅ EEG baseline completado")
    
    baseline_eeg_values = {}
    for band in FILTS:
        buf = bands[band]['buf']
        if len(buf) > 0:
            buf_arr = np.array(buf)
            mu = float(np.nanmean(buf_arr))
            sd = float(np.nanstd(buf_arr))
            baseline_eeg_values[band] = {'mu': mu, 'sigma': sd}
            bands[band]['mu'] = mu
            bands[band]['sd'] = sd
            safe_print(f"  {band:6s}: μ={mu:.3f}  σ={sd:.3f}")
        bands[band]['buf'] = []
    
    send_baseline_event("eeg", "end")
    baseline_eeg_done = True

def close_baseline_acc():
    """Finaliza baseline ACC con rango neutral + movement"""
    global baseline_acc_done, baseline_acc_neutral_done, baseline_acc_movement_done
    
    if baseline_acc_done:
        return
    
    safe_print("\n✅ ACC baseline completado")
    safe_print(f"  x: neutral={baseline_acc_x['neutral']:.3f}  range={baseline_acc_x['range']:.3f}")
    safe_print(f"  y: neutral={baseline_acc_y['neutral']:.3f}  range={baseline_acc_y['range']:.3f}")
    safe_print(f"  z: neutral={baseline_acc_z['neutral']:.3f}  range={baseline_acc_z['range']:.3f}")
    
    send_baseline_event("acc", "end")
    baseline_acc_neutral_done = True
    baseline_acc_movement_done = True
    baseline_acc_done = True

def close_bio():
    """Finaliza baseline BIO (plant1, plant2, myo)"""
    global bio_done
    if bio_done or not any((use_plant1, use_plant2, use_myo)):
        return
    safe_print("✅ BIO baseline completado")
    for k in ('plant1', 'plant2', 'myo'):
        if k in bio:
            bio[k]['mu'] = float(bio[k]['sum'] / max(1, bio[k]['cnt']))
            safe_print(f"  {k}: μ={bio[k]['mu']:.1f}")
    send_baseline_event("bio", "end")
    bio_done = True

def close_dist():
    """Finaliza baseline DIST"""
    global dist_done
    if dist_done or not use_dist:
        return
    safe_print("✅ DIST baseline completado")
    if dist['min'] is not None and dist['max'] is not None:
        dist['range'] = dist['max'] - dist['min']
        safe_print(f"  range: {dist['range']:.1f}")
    send_baseline_event("dist", "end")
    dist_done = True

def muse_eeg(unused_addr, *args):
    """Handler para EEG del Muse"""
    global baseline_eeg_done, frames_left_eeg, baseline_done, baseline_phase
    global baseline_eeg_start_sent
    
    if len(args) < SRATE:
        return
    
    seg = np.array(args[:SRATE], dtype=float)
    eeg_buf.extend(seg)
    
    if not baseline_eeg_done:
        if not baseline_eeg_start_sent:
            send_baseline_event("eeg", "start", BASE_SEC)
            baseline_eeg_start_sent = True
        
        for band in FILTS:
            rms = band_rms(seg, FILTS[band])
            if not np.isnan(rms):
                bands[band]['buf'].append(rms)
        
        frames_left_eeg -= 1
        progress = max(0, BASE_SEC - (frames_left_eeg * (STEP / SRATE)))
        send_baseline_event("eeg", "progress", progress)
        
        if frames_left_eeg <= 0:
            close_baseline_eeg()
            if not baseline_acc_done and use_acc:
                baseline_phase = "acc_neutral"
            baseline_done = baseline_eeg_done and baseline_acc_done
    else:
        eeg_vals = []
        for band in FILTS:
            rms = band_rms(seg, FILTS[band])
            if np.isnan(rms):
                rms = 0.0
            
            env_val = env_z(rms, bands[band]['mu'], bands[band]['sd'], bands[band]['env'])
            bands[band]['rms'] = rms
            bands[band]['env'] = env_val
            bands[band]['signed_env'] = env_val
            
            cc_val = scale(env_val, 0, 3.0)
            bands[band]['cc'] = cc_val
            eeg_vals.append(env_val)
            set_cc(band, cc_val)
        
        if not pause_outputs:
            send_proc("/py/bands_env", eeg_vals)
            send_proc("/py/bands_signed_env", eeg_vals)

def muse_acc(unused_addr, *args):
    """Handler para acelerómetro del Muse"""
    global baseline_acc_neutral_done, baseline_acc_movement_done, baseline_acc_done
    global frames_left_acc_neutral, frames_left_acc_movement, baseline_done
    global acc_neutral_start_time, acc_movement_start_time, baseline_acc_neutral_start_sent
    global baseline_acc_movement_start_sent, baseline_phase
    
    if len(args) < 3:
        return
    
    ax, ay, az = float(args[0]), float(args[1]), float(args[2])
    acc['x'], acc['y'], acc['z'] = ax, ay, az
    
    if not baseline_acc_neutral_done:
        if not baseline_acc_neutral_start_sent:
            send_baseline_event("acc_neutral", "start", baseline_acc_neutral_duration)
            baseline_acc_neutral_start_sent = True
            acc_neutral_start_time = time.time()
        
        baseline_acc_x['neutral'] = ax if baseline_acc_x['neutral'] is None else baseline_acc_x['neutral']
        baseline_acc_y['neutral'] = ay if baseline_acc_y['neutral'] is None else baseline_acc_y['neutral']
        baseline_acc_z['neutral'] = az if baseline_acc_z['neutral'] is None else baseline_acc_z['neutral']
        
        elapsed = time.time() - acc_neutral_start_time
        send_baseline_event("acc_neutral", "progress", elapsed)
        
        if elapsed >= baseline_acc_neutral_duration:
            baseline_acc_neutral_done = True
            acc_baseline['x'] = baseline_acc_x['neutral']
            acc_baseline['y'] = baseline_acc_y['neutral']
            acc_baseline['z'] = baseline_acc_z['neutral']
            safe_print("\n✅ ACC neutral completado")
            baseline_phase = "acc_movement"
    
    elif not baseline_acc_movement_done:
        if not baseline_acc_movement_start_sent:
            send_baseline_event("acc_movement", "start", baseline_acc_movement_duration)
            baseline_acc_movement_start_sent = True
            acc_movement_start_time = time.time()
        
        for axis, val in [('x', ax), ('y', ay), ('z', az)]:
            if baseline_acc_x[axis if axis == 'x' else ('y' if axis == 'y' else 'z')]['min'] is None:
                baseline_acc_x[axis if axis == 'x' else ('y' if axis == 'y' else 'z')]['min'] = val
                baseline_acc_x[axis if axis == 'x' else ('y' if axis == 'y' else 'z')]['max'] = val
            else:
                baseline_acc_x[axis if axis == 'x' else ('y' if axis == 'y' else 'z')]['min'] = min(baseline_acc_x[axis if axis == 'x' else ('y' if axis == 'y' else 'z')]['min'], val)
                baseline_acc_x[axis if axis == 'x' else ('y' if axis == 'y' else 'z')]['max'] = max(baseline_acc_x[axis if axis == 'x' else ('y' if axis == 'y' else 'z')]['max'], val)
        
        elapsed = time.time() - acc_movement_start_time
        send_baseline_event("acc_movement", "progress", elapsed)
        
        if elapsed >= baseline_acc_movement_duration:
            for axis_data in [baseline_acc_x, baseline_acc_y, baseline_acc_z]:
                if axis_data['min'] is not None and axis_data['max'] is not None:
                    axis_data['range'] = axis_data['max'] - axis_data['min']
            
            close_baseline_acc()
            baseline_phase = "complete"
    
    else:
        for axis in ['x', 'y', 'z']:
            val = ax if axis == 'x' else (ay if axis == 'y' else az)
            baseline = acc_baseline[axis]
            rng = baseline_acc_x[axis if axis == 'x' else (baseline_acc_y if axis == 'y' else baseline_acc_z)]['range']
            if rng and rng > 0:
                cc_val = scale(abs(val - baseline), 0, rng)
            else:
                cc_val = 0
            set_cc(f'acc{axis}', cc_val)
    
    if baseline_acc_done and not pause_outputs:
        send_proc("/py/acc", [ax, ay, az])
    
    baseline_done = baseline_eeg_done and baseline_acc_done and bio_done and dist_done

def muse_ppg(unused_addr, *args):
    """Handler para PPG del Muse"""
    if len(args) < 1:
        return
    
    ppg_val = float(args[0])
    ppg['raw'] = ppg_val
    
    if not pause_outputs:
        send_proc("/py/ppg/bpm", ppg_val)
        set_cc('ppg_bpm', scale(ppg_val, 60, 120))

def muse_gyro(unused_addr, *args):
    """Handler para giroscopio del Muse"""
    if len(args) < 3:
        return
    
    gyro['x'], gyro['y'], gyro['z'] = float(args[0]), float(args[1]), float(args[2])
    
    if not pause_outputs:
        send_proc("/py/gyro", [gyro['x'], gyro['y'], gyro['z']])

def muse_jaw(unused_addr, *args):
    """Handler para detección de mordida del Muse"""
    if len(args) < 1:
        return
    
    jaw['clenched'] = int(args[0])
    set_cc('jaw', 127 if jaw['clenched'] else 0)
    
    if not pause_outputs:
        send_proc("/py/jaw", [jaw['clenched']])

def catch_all_osc(unused_addr, *args):
    """Captura todos los mensajes OSC para debugging"""
    if debug_mode:
        print(f"[OSC RECEIVED] {unused_addr}: {args}")

# Registrar handlers
disp = Dispatcher()
disp.map("/muse/eeg", muse_eeg)
disp.map("/muse/acc", muse_acc)
disp.map("/muse/ppg", muse_ppg)
disp.map("/muse/gyro", muse_gyro)
disp.map("/muse/jaw", muse_jaw)
disp.set_default_handler(catch_all_osc)

if not is_simulation:
    print("[OSC] Mapeos configurados:")

# --- Loops de datos ---
def live_loop():
    """Loop para modo en vivo con servidor OSC"""
    global baseline_done, save_data
    
    print("\n--- Iniciando servidor OSC ---")
    print(f"Esperando datos Muse en {MY_LOCAL_IP}:{OSC_PORT}\n")
    
    server = BlockingOSCUDPServer((MY_LOCAL_IP, OSC_PORT), disp)
    
    try:
        while threads_active:
            server.handle_request()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        safe_print(f"Error en servidor OSC: {e}")

def serial_loop():
    """Loop para leer datos del puerto serial (Arduino)"""
    global threads_active
    try:
        import serial
        if not SERIAL_PORT or not os.path.exists(SERIAL_PORT):
            return
        
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
        safe_print(f"Serial conectado: {SERIAL_PORT} @ {BAUD} baud")
        
        while threads_active:
            try:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line and not line.startswith('#'):
                        parts = line.split(',')
                        if len(parts) >= 3:
                            try:
                                temp_val = float(parts[0])
                                hum_val = float(parts[1])
                                hum['raw'] = hum_val
                                temp['raw'] = temp_val
                                send_proc("/py/temp_hum", [temp_val, hum_val])
                            except ValueError:
                                pass
                time.sleep(0.01)
            except Exception as e:
                if debug_mode:
                    safe_print(f"Serial read error: {e}")
                time.sleep(1)
    except ImportError:
        safe_print("Serial not available (pyserial not installed)")
    except Exception as e:
        safe_print(f"Serial loop error: {e}")

try:
    print("\n--- Estado de Ejecución ---")
    print(f"Modo: {EXECUTION_MODE.upper()}")
    
    if EXECUTION_MODE == 'csv_replay':
        print(f"Archivo: {CSV_REPLAY_FILE}")
        print(f"Velocidad: {CSV_REPLAY_SPEED}x")
    
    input("\nPresiona Enter para iniciar...")
    
    if EXECUTION_MODE == 'simulation':
        midi_thread = threading.Thread(target=midi_tick, daemon=True)
        midi_thread.start()
        simulation_loop()
    
    elif EXECUTION_MODE == 'csv_replay':
        csv_replay_loop()
    
    elif EXECUTION_MODE == 'live':
        safe_print("\n--- Configuración LIVE ---")
        safe_print(f"IP: {MY_LOCAL_IP} | Puerto: {OSC_PORT}")
        safe_print("Conecta Muse a esta dirección IP\n")
        
        shortcuts_thread = threading.Thread(target=listen_shortcuts, daemon=True)
        shortcuts_thread.start()
        
        midi_thread = threading.Thread(target=midi_tick, daemon=True)
        midi_thread.start()
        
        serial_thread = threading.Thread(target=serial_loop, daemon=True)
        serial_thread.start()
        
        live_loop()

except KeyboardInterrupt:
    safe_print("\n✋ Ctrl+C detectado. Saliendo...")
except Exception as e:
    safe_print(f"\n!!! ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    threads_active = False
    time.sleep(0.5)
    print("\n✅ Programa finalizado.")
    sys.exit(0)
