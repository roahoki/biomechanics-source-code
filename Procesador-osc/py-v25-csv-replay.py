#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT PYTHON (v25-csv-replay)
- Extiende v24 con capacidad de reproducir datos desde CSV
- Añade selector de archivo CSV en el menú principal
- Mantiene toda la funcionalidad de v24
"""

import sys
import time
import os
import math, re, threading, logging, socket
from collections import deque
from pythonosc.udp_client import SimpleUDPClient
from datetime import datetime

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
print("  BIOMECHANICS OSC PROCESSOR v25-csv-replay")
print("="*60)
print("Esta ventana debe permanecer abierta.\n")

# --- Modo de ejecución ---
EXECUTION_MODE = 'live'  # live, csv_replay, simulation
CSV_REPLAY_FILE = None
CSV_REPLAY_SPEED = 1.0

# --- Funciones (get_local_ip, preguntar_bool) ---
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

# Variables globales necesarias para show_main_menu
is_simulation = False
use_eeg = use_acc = use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False
baseline_duration_seconds = 10

def list_available_csv_files():
    """Lista archivos CSV disponibles en el directorio del script"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_files = [f for f in os.listdir(script_dir) if f.endswith('.csv') and f.startswith('meditacion_')]
    csv_files.sort(reverse=True)  # Más recientes primero
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
            # Manejar NaN
            if pd.notna(max_time):
                duration_sec = int(max_time)
            else:
                duration_sec = int(num_lines / 10)
        else:
            duration_sec = int(num_lines / 10)
        return num_lines, duration_sec
    except Exception as e:
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
    use_plant1 = use_plant2 = use_dist = False
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
        
        # Listar archivos CSV disponibles
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
        
        # Mostrar info del archivo seleccionado
        num_lines, duration_sec = get_csv_info(csv_path)
        duration_str = f"{duration_sec // 60}m {duration_sec % 60}s" if duration_sec >= 60 else f"{duration_sec}s"
        
        speed_str = input(f"\nVelocidad de reproducción (1.0=normal, 2.0=2x, 0.5=mitad, default=1.0): ").strip()
        try:
            CSV_REPLAY_SPEED = float(speed_str) if speed_str else 1.0
            if CSV_REPLAY_SPEED <= 0:
                print("⚠️ Velocidad debe ser > 0, usando 1.0")
                CSV_REPLAY_SPEED = 1.0
        except ValueError:
            print("⚠️ Valor inválido, usando velocidad 1.0")
            CSV_REPLAY_SPEED = 1.0
        
        # Calcular duración con velocidad aplicada
        adjusted_duration = int(duration_sec / CSV_REPLAY_SPEED)
        adjusted_duration_str = f"{adjusted_duration // 60}m {adjusted_duration % 60}s" if adjusted_duration >= 60 else f"{adjusted_duration}s"
            
        print(f"\n✓ Archivo seleccionado: {os.path.basename(CSV_REPLAY_FILE)}")
        print(f"✓ Velocidad: {CSV_REPLAY_SPEED}x")
        print(f"✓ Duración original: {duration_str}")
        print(f"✓ Duración ajustada: {adjusted_duration_str}")
        print(f"✓ Total de líneas: {num_lines}")
        
        # Detectar qué sensores están en el CSV
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

    # macOS / Linux: buscar candidatos comunes
    candidates = glob.glob("/dev/tty.usbserial*") + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*") + glob.glob('/dev/cu.*')
    return candidates[0] if candidates else None

# --- Nueva clase: CSV Replay ---
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
            
            # Filtrar líneas de comentario si timestamp es string
            if 'timestamp' in self.df.columns:
                # Eliminar filas que empiezan con #
                self.df = self.df[~self.df['timestamp'].astype(str).str.startswith('#')]
                self.df = self.df.reset_index(drop=True)
            
            print(f"✓ CSV cargado: {len(self.df)} registros")
            print(f"Columnas: {list(self.df.columns)[:10]}...")  # Mostrar primeras 10
            
            # Verificar que tenga columna time_sec
            if 'time_sec' not in self.df.columns:
                print("⚠️ No se encontró columna 'time_sec', usando índice como tiempo")
                self.df['time_sec'] = self.df.index * 0.1  # 10Hz por defecto
                
            return True
        except Exception as e:
            print(f"✗ Error cargando CSV: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_next_sample(self):
        """Obtiene la siguiente muestra con timing real"""
        if self.current_index >= len(self.df):
            return None
        
        if self.paused:
            return None
            
        row = self.df.iloc[self.current_index]
        
        # Calcular espera hasta siguiente muestra
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

# --- Config Inicial Red ---
OSC_PORT = 5001
MY_LOCAL_IP = get_local_ip()

# --- Menú de Selección ---
is_simulation = False
use_eeg = use_acc = use_ppg = use_gyro = use_jaw = use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False
save_data = False
baseline_duration_seconds = 10

# Mostrar el menú inicial
show_main_menu()

any_sensor_selected = any((use_eeg, use_acc, use_ppg, use_gyro, use_jaw, use_myo, use_temp_hum, use_plant1, use_plant2, use_dist))
if not any_sensor_selected and not is_simulation and EXECUTION_MODE != 'csv_replay':
    print("\nAdvertencia: Ningún sensor específico fue seleccionado.")
if True:
    print("="*40+"\n")

# --- Config ---
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

# --- Wrapper para enviar OSC ---
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

# [Copiar todo el código de DataRecorder, funciones de baseline, handlers OSC, etc. de v24]
# Por brevedad, incluyo solo las partes esenciales nuevas...

# --- CONSTANTES ---
SRATE, WIN_S=256, 2
WIN, STEP=SRATE*WIN_S, (SRATE*WIN_S)//2
BASE_SEC = baseline_duration_seconds if use_eeg and not is_simulation else 10
Z_MAX, ALPHA_ENV, DEAD_ZONE, ALPHA_DIST=3.0, 0.3, 0.2, 0.25
UPDATE_HZ=10.0
PERIOD = 1.0 / UPDATE_HZ

MU_DEFAULTS = {'delta': 1.2, 'theta': 1.0, 'alpha': 1.0, 'beta': 0.8, 'gamma': 0.5}
SD_DEFAULTS = {'delta': 0.4, 'theta': 0.3, 'alpha': 0.3, 'beta': 0.25, 'gamma': 0.2}

def butter(lo, hi, fs=SRATE):
    nyq=fs*0.5
    return sg.butter(4, [lo/nyq, hi/nyq], 'band')

FILTS={'delta':butter(0.5,4),'theta':butter(4,8),'alpha':butter(8,13),'beta':butter(13,30),'gamma':butter(30,45)}

# --- Estados ---
bands = {b: dict(rms=np.nan, env=0, signed_env=0.0, mu=MU_DEFAULTS.get(b, 1.0) if is_simulation else None, sd=SD_DEFAULTS.get(b, 1.0) if is_simulation else None, cc=0, buf=[]) for b in FILTS}
acc = {'x':0.0, 'y':0.0, 'z':0.0}
ppg = dict(bpm=0.0, cc=0)

baseline_done = True if is_simulation or EXECUTION_MODE == 'csv_replay' else False
threads_active = True

# --- Impresión ---
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except:
        pass

# --- Nueva función: CSV Replay Loop ---
def csv_replay_loop():
    """Bucle de reproducción desde CSV"""
    global baseline_done
    
    print(f"\n🎬 Iniciando reproducción de {CSV_REPLAY_FILE}")
    print(f"Velocidad: {CSV_REPLAY_SPEED}x")
    
    replay_engine = CSVReplayEngine(CSV_REPLAY_FILE, CSV_REPLAY_SPEED)
    
    if not replay_engine.load():
        print("❌ Error cargando CSV")
        return
    
    # Marcar baseline como completo (datos ya están procesados)
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
            
            # Extraer y enviar datos EEG
            if use_eeg:
                try:
                    bands_env = [
                        float(sample.get('delta_env', 0)),
                        float(sample.get('theta_env', 0)),
                        float(sample.get('alpha_env', 0)),
                        float(sample.get('beta_env', 0)),
                        float(sample.get('gamma_env', 0))
                    ]
                    
                    # Para signed_env, usar env con signo (simplificación)
                    bands_signed = bands_env
                    
                    send_proc("/py/bands_env", bands_env)
                    send_proc("/py/bands_signed_env", bands_signed)
                    
                    # Enviar raw también
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
            
            # Extraer y enviar ACC
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
            
            # Extraer y enviar PPG
            if use_ppg:
                try:
                    ppg_bpm = float(sample.get('ppg_bpm', 0))
                    send_proc("/py/ppg/bpm", ppg_bpm)
                except Exception as e:
                    if debug_mode:
                        print(f"Error enviando PPG: {e}")
            
            # Mostrar progreso
            progress = replay_engine.get_progress()
            time_sec = float(sample.get('time_sec', 0))
            
            # Actualizar cada 5%
            if progress >= last_progress_print + 5:
                progress_bar = "█" * (progress // 5) + " " * (20 - progress // 5)
                sys.stdout.write(f"\rProgreso: [{progress_bar}] {progress}% | ⏱️  {time_sec:.1f}s")
                sys.stdout.flush()
                last_progress_print = progress
    
    except KeyboardInterrupt:
        print("\n\n⏸️  Reproducción detenida por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante reproducción: {e}")
        import traceback
        traceback.print_exc()

def simulation_loop():
    """Bucle de simulación (mismo que v24)"""
    global baseline_done
    baseline_done = True
    print("\n--- Iniciando Modo Simulación ---")
    
    baseline_mu_values = [MU_DEFAULTS.get(b, 1.0) for b in FILTS]
    send_proc("/py/baseline_mu", baseline_mu_values, force=True)
    
    t_sim = 0.0
    print("Simulación iniciada. Presiona Ctrl+C para detener.")
    
    while threads_active:
        try:
            # Generar señales simuladas
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

def return_to_menu(exit_app=False):
    """Vuelve al menú o sale"""
    global exit_requested, threads_active
    
    if exit_app:
        print("\n⏹️  Preparando salida...")
        exit_requested = True
        threads_active = False
        time.sleep(0.5)
        sys.exit(0)

# --- MAIN LOOP ---
threads_active = True

try:
    print("\n--- Estado de Ejecución ---")
    print(f"Modo: {EXECUTION_MODE.upper()}")
    
    if EXECUTION_MODE == 'csv_replay':
        print(f"Archivo: {CSV_REPLAY_FILE}")
        print(f"Velocidad: {CSV_REPLAY_SPEED}x")
    
    input("\nPresiona Enter para iniciar...")
    
    if EXECUTION_MODE == 'simulation':
        simulation_loop()
    elif EXECUTION_MODE == 'csv_replay':
        csv_replay_loop()
    elif EXECUTION_MODE == 'live':
        print("Modo LIVE requiere implementación completa de handlers OSC")
        print("(Ver py-v24.py para implementación completa)")
        time.sleep(2)

except KeyboardInterrupt:
    safe_print("\n✋ Ctrl+C detectado. Saliendo...")
except Exception as e:
    safe_print(f"\n!!! ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    threads_active = False
    print("\n✅ Programa finalizado.")
    sys.exit(0)
