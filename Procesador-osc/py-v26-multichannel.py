1#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT PYTHON (v26-multichannel)
- Extensión de v24 con soporte para procesar cada canal EEG del Muse 2 individualmente
- Soporta 4 canales EEG: TP9, AF7, AF8, TP10
- Procesa y envía datos de cada canal por separado
- Mantiene compatibilidad con modo simulador y todas las funciones de v24
"""

import sys
import time # Para la pausa inicial

import math, re, threading, logging, socket
from collections import deque
from pythonosc.udp_client import SimpleUDPClient

# --- Dependencias ---
try:
    import numpy as np; import scipy.signal as sg
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
except ImportError as e: print(f"!!! ERROR: Falta librería: {e}\nInstala dependencias"); input("Enter..."); sys.exit(1)
# --------------------

# --- Pausa inicial ---
print("="*60)
print("  BIOMECHANICS OSC PROCESSOR v26-multichannel")
print("  Soporte para 4 canales EEG individuales")
print("="*60)
print("Esta ventana debe permanecer abierta.\n")
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

# --- Canales EEG del Muse 2 ---
EEG_CHANNELS = ['TP9', 'AF7', 'AF8', 'TP10']
EEG_CHANNEL_INDICES = {ch: idx for idx, ch in enumerate(EEG_CHANNELS)}

# Variables globales necesarias para show_main_menu
is_simulation = False
use_eeg = use_acc = use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False
baseline_duration_seconds = 10

def show_main_menu():
    """Muestra el menú principal y procesa la selección del usuario."""
    global is_simulation, use_eeg, use_acc, use_ppg, use_myo, use_temp_hum, use_plant1, use_plant2, use_dist, baseline_duration_seconds, in_menu, pause_outputs, save_data
    
    in_menu = False  # Salir del menú cuando se selecciona una opción
    pause_outputs = False  # Reanudar outputs
    
    print("\n=== SELECCIÓN DE FUENTE DE DATOS ===")
    print("0. Modo Simulador (Datos Falsos)")
    print("1. Solo Sensor Cerebral (Muse)")
    print("2. Salir")
    choice = input("Selecciona una opción (0-2): ").strip()

    is_simulation = (choice == '0')
    use_eeg = use_acc = use_ppg = use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False
    save_data = False
    baseline_duration_seconds = 10  # Default

    if is_simulation:
        print("\n--- MODO SIMULADOR ACTIVADO ---")
        use_eeg = True; use_acc = True; use_ppg = False
        use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False
        save_data = False
    elif choice == '1':
        print("\n" + "="*50 + "\n    CONFIG OSC\n"+f"    ► App Muse -> IP: {MY_LOCAL_IP} | Puerto: {OSC_PORT}\n"+"="*50 + "\n")
        print("--- Config Sensor Cerebral ---")
        use_eeg = preguntar_bool("¿Ondas?")
        if use_eeg:
            global eeg_processing_mode
            eeg_processing_mode = 'individual' if preguntar_bool("¿Procesar canales individuales?") else 'average'
            print(f"✓ Modo EEG: {eeg_processing_mode.upper()}")
        use_acc = preguntar_bool("¿Accel?")
        use_ppg = preguntar_bool("¿Heartbeat/PPG?")
        save_data = preguntar_bool("¿Guardar datos?")
        use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False
        if use_eeg:
            while True:
                try:
                    baseline_str = input("⏱️  ¿Duración del baseline en segundos? (recomendado 10-30s, default=10): ").strip()
                    baseline_duration_seconds = int(baseline_str) if baseline_str else 10
                    if baseline_duration_seconds <= 0: print("⚠️ Debe ser > 0"); return
                    if baseline_duration_seconds > 120: print("⚠️ Máximo recomendado 120s"); continue
                    print(f"✓ Baseline: {baseline_duration_seconds}s")
                    break
                except ValueError: print("⚠️ Ingresa un número válido")
    elif choice == '2':
        print("Saliendo."); return_to_menu(exit_app=True)
    else:
        print("Opción inválida."); show_main_menu()

def detect_serial_port():
    """Detecta automáticamente el puerto serial según el SO"""
    import platform
    import glob

    sistema = platform.system()

    if sistema == "Windows":
        # No intentar abrir puertos serial aquí; devolver None (user may not use Arduino)
        return None

    # macOS / Linux: buscar candidatos comunes
    candidates = glob.glob("/dev/tty.usbserial*") + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*") + glob.glob('/dev/cu.*')
    return candidates[0] if candidates else None
# ---------------------------------------------------------

# --- Config Inicial Red (Solo si no es simulación) ---
OSC_PORT = 5001; MY_LOCAL_IP = get_local_ip()
# ------------------------------------

# --- Menú de Selección con Opción 0 ---
# Inicializar variables (se completarán en show_main_menu)
is_simulation = False
use_eeg = use_acc = use_ppg = use_gyro = use_jaw = use_myo = use_temp_hum = use_plant1 = use_plant2 = use_dist = False
save_data = False
baseline_duration_seconds = 10
eeg_processing_mode = 'average'  # 'average' o 'individual'

# Mostrar el menú inicial
show_main_menu()

any_sensor_selected = any((use_eeg, use_acc, use_ppg, use_gyro, use_jaw, use_myo, use_temp_hum, use_plant1, use_plant2, use_dist))
if not any_sensor_selected and not is_simulation:
    print("\nAdvertencia: Ningún sensor específico fue seleccionado.")
if True:
    print("="*40+"\n")
# --- FIN MENÚ ---

# --- Config ---
SERIAL_PORT = detect_serial_port()
if SERIAL_PORT is None:
    print("⚠️ ADVERTENCIA: No se detectó puerto serial. Usando COM3 como fallback.")
    SERIAL_PORT = "COM3"
else:
    print(f"✓ Puerto serial detectado: {SERIAL_PORT}")

BAUD = 115200
PROC_IP = "127.0.0.1"
PROC_PORT = 5002
proc_client = None
try:
    proc_client=SimpleUDPClient(PROC_IP, PROC_PORT)
    print("="*50+f"\n    ► Enviando a Processing -> IP: {PROC_IP} | Puerto: {PROC_PORT}\n"+"="*50+"\n")
except Exception as e: print(f"!!! ERROR FATAL creando cliente OSC: {e}"); input("Enter..."); sys.exit(1)

# --- Wrapper para enviar OSC que respeta el modo recalibración/pause ---
in_recalibration = False
pause_outputs = False
debug_mode = False  # Se activa con Ctrl+D
show_realtime_data = True  # Se alterna con Ctrl+R para mostrar/ocultar datos en tiempo real
in_menu = False  # Flag para indicar que estamos en el menú principal
exit_requested = False  # Flag para solicitar salida de la aplicación

def send_proc(path, data, force=False):
    """Enviar OSC a Processing salvo si estamos en recalibración/pause.
    force=True envía aunque pause esté activo (usar sólo desde el thread de recalibración)."""
    global pause_outputs, proc_client
    try:
        if pause_outputs and not force:
            return
        if proc_client is not None:
            proc_client.send_message(path, data)
    except BlockingIOError:
        # Socket no-bloqueante saturado, ignorar silenciosamente
        pass
    except Exception:
        pass

def send_baseline_event(phase, event_type, duration=0):
    """Enviar eventos de baseline a TouchDesigner.
    phase: "eeg", "acc_neutral", "acc_movement"
    event_type: "start", "progress", "end"
    duration: duración esperada en segundos (para start), o progreso 0-100 (para progress)
    """
    try:
        if event_type == "start":
            # Enviar inicio de baseline
            send_proc("/py/baseline/start", [phase, duration], force=True)
        elif event_type == "progress":
            # Enviar progreso (0-100)
            send_proc(f"/py/baseline/{phase}/progress", float(duration), force=True)
        elif event_type == "end":
            # Enviar término de baseline
            send_proc("/py/baseline/end", [phase], force=True)
    except Exception as e:
        if debug_mode:
            print(f"Error enviando evento baseline: {e}")


class DataRecorder:
    """Registra datos de sensores a CSV cada 1 segundo post-baseline"""
    def __init__(self, filename=None):
        import csv
        from datetime import datetime
        self.csv = csv
        self.datetime = datetime
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
            self.writer = self.csv.DictWriter(self.file, fieldnames=self._get_fieldnames())
            self.writer.writeheader()
            self.file.flush()
            safe_print(f"📁 Grabando datos en: {self.filename}")
        except Exception as e:
            safe_print(f"Error iniciando DataRecorder: {e}")
            
    def _get_fieldnames(self):
        """Retorna lista de campos para el CSV"""
        fields = ['timestamp', 'time_sec']
        
        # EEG bands
        if use_eeg:
            for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                fields.extend([f'{band}_rms', f'{band}_env', f'{band}_cc'])
        
        # Acelerómetro
        if use_acc:
            fields.extend(['acc_x', 'acc_y', 'acc_z', 'acc_x_dev', 'acc_y_dev', 'acc_z_dev'])
        
        # PPG
        if use_ppg:
            fields.extend(['ppg_bpm', 'ppg_cc'])
        
        return fields
    
    def write_baseline_metadata(self):
        """Escribe información del baseline como comentarios (se llama post-baseline)"""
        if self.baseline_data_written or self.file is None:
            return
            
        try:
            self.file.write("\n# === BASELINE DATA ===\n")
            
            # EEG Baseline
            if use_eeg and baseline_eeg_values:
                for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                    if band in baseline_eeg_values:
                        mu = baseline_eeg_values[band].get('mu', 0.0)
                        sigma = baseline_eeg_values[band].get('sigma', 0.0)
                        min_val = baseline_eeg_values[band].get('min', 0.0)
                        max_val = baseline_eeg_values[band].get('max', 0.0)
                        self.file.write(f"# {band.upper()}: μ={float(mu):.3f} σ={float(sigma):.3f} min={float(min_val):.3f} max={float(max_val):.3f}\n")
            
            # ACC Baseline
            if use_acc:
                for axis, var_name in [('x', baseline_acc_x), ('y', baseline_acc_y), ('z', baseline_acc_z)]:
                    if var_name and var_name.get('neutral') is not None:
                        neutral = float(var_name.get('neutral', 0.0))
                        min_val = float(var_name.get('min', 0.0))
                        max_val = float(var_name.get('max', 0.0))
                        range_val = float(var_name.get('range', 0.0))
                        sigma = float(var_name.get('sigma', 0.0))
                        self.file.write(f"# ACC_{axis.upper()}: neutral={neutral:+.4f} range={range_val:.4f} [{min_val:+.4f}, {max_val:+.4f}] σ={sigma:.4f}\n")
            
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
        
        # Solo escribir cada 1 segundo
        if now - self.last_write_time < 1.0:
            return
        
        try:
            row = {
                'timestamp': self.datetime.now().isoformat(),
                'time_sec': f"{elapsed_seconds:.1f}"
            }
            
            # EEG
            if use_eeg:
                for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                    row[f'{band}_rms'] = bands[band].get('rms', '')
                    row[f'{band}_env'] = bands[band].get('env', '')
                    row[f'{band}_cc'] = bands[band].get('cc', '')
            
            # ACC
            if use_acc:
                for axis in ['x', 'y', 'z']:
                    row[f'acc_{axis}'] = acc.get(axis, '')
                    # Calcular desviación actual
                    baseline_val = acc_baseline.get(axis, 0)
                    current_val = acc.get(axis, 0)
                    row[f'acc_{axis}_dev'] = f"{current_val - baseline_val:.4f}"
            
            # PPG
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


def trigger_recalibration():
    """Inicia la rutina de recalibración en un hilo separado."""
    if in_recalibration:
        print("Ya está en recalibración.")
        return
    t = threading.Thread(target=recalibration_routine, daemon=True)
    t.start()


def return_to_menu(exit_app=False):
    """Vuelve al menú principal o sale de la aplicación.
    Si exit_app=True, se sale. Si exit_app=False, vuelve al menú principal."""
    global in_menu, exit_requested, threads_active, pause_outputs
    
    if exit_app:
        print("\n⏹️  Preparando salida de la aplicación...")
        exit_requested = True
        threads_active = False
        time.sleep(0.5)
        sys.exit(0)
    else:
        # Volver al menú principal
        in_menu = True
        pause_outputs = True
        print("\n📋 En menú principal - datos pausados")
        print("Presiona Ctrl+B para recalibrar, Ctrl+Q para salir")
        
        # Lanzar hilo para mantener visual mientras está en menú
        t = threading.Thread(target=menu_idle_loop, daemon=True)
        t.start()




def recalibration_routine():
    """Rutina que pausa salidas, recolecta baseline y mantiene envíos simulados a TD."""
    global in_recalibration, pause_outputs, baseline_done, baseline_eeg_done, baseline_acc_neutral_done, baseline_acc_movement_done, baseline_acc_done, frames_left, frames_left_acc_neutral, frames_left_acc_movement
    global acc_neutral_start_time, acc_movement_start_time
    global baseline_eeg_start_sent, baseline_acc_neutral_start_sent, baseline_acc_movement_start_sent
    in_recalibration = True
    pause_outputs = True
    print("\n🔔 Recalibración iniciada: recolectando baseline...\n")

    # Reset buffers/counters
    if use_eeg:
        for n in bands: bands[n]['buf'] = []
        baseline_done = False
        baseline_eeg_done = False
        frames_left = int(BASE_SEC / (STEP / SRATE))
        baseline_eeg_start_sent = False
    if use_acc:
        for a in acc:
            acc_rng[a]['min'] = None; acc_rng[a]['max'] = None
            acc_rng[a]['values'] = []
            acc_rng[a]['neutral_min'] = None; acc_rng[a]['neutral_max'] = None
        baseline_acc_neutral_done = False
        baseline_acc_movement_done = False
        baseline_acc_done = False
        frames_left_acc_neutral = int(baseline_acc_neutral_duration / (STEP / SRATE))
        frames_left_acc_movement = 0
        acc_neutral_start_time = None
        acc_movement_start_time = None
        baseline_acc_neutral_start_sent = False
        baseline_acc_movement_start_sent = False

    t_sim = 0.0
    try:
        while True:
            # generar simulación visual corta para TD (mantener actividad)
            s0 = 0.9 * math.sin(0.2 * t_sim + 0.0)
            s1 = 1.1 * math.sin(0.4 * t_sim + 1.5)
            s2 = 1.0 * math.sin(0.6 * t_sim + 3.0)
            s3 = 0.8 * math.sin(1.0 * t_sim + 4.5)
            s4 = 0.6 * math.sin(1.5 * t_sim + 6.0)
            osc_signed = [s0, s1, s2, s3, s4]
            osc_env = [abs(v) for v in osc_signed]

            # raw: usar mu actuales si existen, sino defaults
            raw_vals = []
            for n in list(FILTS.keys()):
                mu = bands[n].get('mu')
                if mu is None: mu = MU_DEFAULTS.get(n, 1.0)
                raw_vals.append(round(float(mu), 3))

            # enviar a TD FORZANDO (para que la visual no se congele)
            send_proc("/py/bands_signed_env", osc_signed, force=True)
            send_proc("/py/bands_env", osc_env, force=True)
            send_proc("/py/bands_raw", raw_vals, force=True)
            send_proc("/py/acc", [acc['x'], acc['y'], acc['z']], force=True)

            time.sleep(PERIOD)
            t_sim += PERIOD

            # condición de salida: cuando todos los baselines completaron
            eeg_ok = (not use_eeg) or baseline_eeg_done
            acc_ok = (not use_acc) or (baseline_acc_neutral_done and baseline_acc_movement_done)
            if eeg_ok and acc_ok:
                break

    finally:
        # Asegurarse que los cierres de baseline se ejecuten
        if use_eeg and not baseline_eeg_done:
            try: close_baseline_eeg()
            except Exception: pass
        if use_acc and not (baseline_acc_neutral_done and baseline_acc_movement_done):
            try: close_baseline_acc()
            except Exception: pass

        pause_outputs = False
        in_recalibration = False
        print("\n✅ Recalibración finalizada.\n")


def menu_idle_loop():
    """Mantiene simulación visual mientras se está en el menú principal."""
    global in_menu, pause_outputs
    t_menu = 0.0
    print("🎬 Enviando simulación visual a TouchDesigner mientras espera selección...")
    
    while in_menu and threads_active:
        try:
            row_start_time = time.time()
            
            # Generar simulación visual (misma que recalibration_routine)
            s0 = 0.9 * math.sin(0.2 * t_menu + 0.0)
            s1 = 1.1 * math.sin(0.4 * t_menu + 1.5)
            s2 = 1.0 * math.sin(0.6 * t_menu + 3.0)
            s3 = 0.8 * math.sin(1.0 * t_menu + 4.5)
            s4 = 0.6 * math.sin(1.5 * t_menu + 6.0)
            osc_signed = [s0, s1, s2, s3, s4]
            osc_env = [abs(v) for v in osc_signed]
            
            # Enviar a TD FORZANDO (para que la visual no se congele)
            send_proc("/py/bands_signed_env", osc_signed, force=True)
            send_proc("/py/bands_env", osc_env, force=True)
            send_proc("/py/acc", [0.0, 0.0, 0.0], force=True)
            
            time.sleep(PERIOD)
            t_menu += PERIOD
            
            dt = time.time() - row_start_time
            if dt < PERIOD:
                time.sleep(PERIOD - dt)
        except Exception as e:
            if debug_mode:
                print(f"Error en menu_idle_loop: {e}")
            time.sleep(PERIOD)


def listen_shortcuts():
    """Escucha Ctrl+B (recalibración), Ctrl+D (debug), Ctrl+R (mostrar/ocultar datos), Ctrl+Q (salir), Ctrl+M (menú). Thread daemon no-blocking."""
    try:
        import sys, termios, tty, select, fcntl, os
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        
        # Poner stdin en non-blocking
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        while threads_active:
            try:
                ch = sys.stdin.read(1)
                if ch == '\x02':  # Ctrl+B
                    print("\n✋ Ctrl+B detectado: iniciando recalibración...")
                    trigger_recalibration()
                elif ch == '\x04':  # Ctrl+D
                    global debug_mode
                    debug_mode = not debug_mode
                    state = "ACTIVADO" if debug_mode else "DESACTIVADO"
                    print(f"\n🔍 Debug mode {state}")
                elif ch == '\x12':  # Ctrl+R
                    global show_realtime_data
                    show_realtime_data = not show_realtime_data
                    state = "VISIBLE" if show_realtime_data else "OCULTO"
                    print(f"\n📊 Datos en tiempo real {state}")
                elif ch == '\x11':  # Ctrl+Q
                    print("\n👋 Ctrl+Q detectado: saliendo...")
                    return_to_menu(exit_app=True)
                elif ch == '\x0d':  # Ctrl+M
                    print("\n📋 Ctrl+M detectado: volviendo al menú principal...")
                    return_to_menu(exit_app=False)
            except (IOError, OSError):
                # No data available, expected in non-blocking mode
                pass
            time.sleep(0.05)
    except Exception:
        return
    finally:
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        except Exception:
            pass

SRATE, WIN_S=256, 2; WIN, STEP=SRATE*WIN_S, (SRATE*WIN_S)//2
# Usar la duración configurada por el usuario
BASE_SEC = baseline_duration_seconds if use_eeg and not is_simulation else 10
Z_MAX, ALPHA_ENV, DEAD_ZONE, ALPHA_DIST=3.0, 0.3, 0.2, 0.25
UPDATE_HZ=10.0; SLEW_PER_SEC=25; MIN_STEP_CC=1; CURVE_MODE="exp"; CURVE_K=0.65
PERIOD = 1.0 / UPDATE_HZ
# ----------

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
    # MIDI support disabled: return empty mapping
    print("MIDI support disabled in this build — no MIDI ports will be opened.")
    return {}
# --- FIN CORRECCIÓN ---

# --- Abrir Puertos MIDI (desactivado) ---
MIDI_OUT = {}
print("MIDI disabled — routing MIDI handled externally (TouchDesigner/Ableton)")
# -----------------------

# --- Emisión CC ---
TARGET_CC={k: 0 for k in CC_NUM}; LAST_CC={k: 0 for k in CC_NUM}
threads_active = True
def cc_curve(cc, mode=CURVE_MODE,k=CURVE_K): x=max(0,min(127,cc))/127.0; y=x**(1-k) if mode=="exp" else (1.0-(1.0-x)**(1-k) if mode=="log" else x); return int(round(y*127))
def _send_cc(sig, val):
    # MIDI sending disabled in this version (handled externally)
    return
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
# Estructura para modo promedio (compatibilidad con v24)
bands = {b: dict(rms=np.nan, env=0, signed_env=0.0, mu=MU_DEFAULTS.get(b, 1.0) if is_simulation else None, sd=SD_DEFAULTS.get(b, 1.0) if is_simulation else None, cc=0, buf=[]) for b in FILTS}

# Estructura para modo multicanal (4 canales individuales del Muse 2)
# Cada canal tiene sus propias bandas de frecuencia procesadas independientemente
bands_per_channel = {
    ch: {b: dict(rms=np.nan, env=0, signed_env=0.0, mu=None, sd=None, cc=0, buf=[]) for b in FILTS}
    for ch in EEG_CHANNELS
}

acc = {'x':0.0, 'y':0.0, 'z':0.0}
acc_baseline = {'x': 0.0, 'y': 0.0, 'z': 0.0}  # ← Posición neutral
acc_rng = {a: dict(min=None, max=None, values=[]) for a in acc}  # ← values[] para capturar datos del baseline

# Rangos de baseline ACC para exportar a TouchDesigner (incluyendo desviación estándar)
baseline_acc_x = {'neutral': None, 'min': None, 'max': None, 'range': None, 'sigma': None}
baseline_acc_y = {'neutral': None, 'min': None, 'max': None, 'range': None, 'sigma': None}
baseline_acc_z = {'neutral': None, 'min': None, 'max': None, 'range': None, 'sigma': None}

# Baseline EEG para exportar a CSV y TouchDesigner
baseline_eeg_values = {}  # {band: {'mu': X, 'sigma': Y, 'min': Z, 'max': W}}
baseline_eeg_values_per_channel = {ch: {} for ch in EEG_CHANNELS}  # Baseline por canal

bio = {k: dict(raw=None, env=0, mu=None, amp=None, min=None, max=None, sum=0, cnt=0, cc=0) for k in ('plant1', 'plant2', 'myo')}

dist = dict(raw=None, filt=None, min=None, max=None, cc=0)
hum, temp = dict(raw=None, cc=0), dict(raw=None, cc=0)

# --- Nuevos sensores Muse (PPG, Gyro, Jaw) ---
ppg = dict(raw=None, cc=0)  # Photoplethysmography - Heartbeat
gyro = dict(x=0.0, y=0.0, z=0.0, cc=0)  # Giróscopo
jaw = dict(clenched=0, cc=0)  # Jaw clench detection
# use_ppg, use_gyro, use_jaw se inicializan en línea 116 (antes del menú)

# Buffer de EEG - un buffer por canal para modo multicanal
eeg_buf = deque(maxlen=WIN)  # Modo promedio (compatibilidad)
eeg_buf_per_channel = {ch: deque(maxlen=WIN) for ch in EEG_CHANNELS}  # Modo multicanal

# --- Tracking de eventos de baseline para evitar envíos duplicados ---
baseline_eeg_start_sent = False
baseline_acc_neutral_start_sent = False
baseline_acc_movement_start_sent = False

# --- BASELINE SECUENCIAL (NUEVO) ---
needs_baseline_calibration = not is_simulation and any((use_eeg, use_acc, use_myo, use_plant1, use_plant2, use_dist))

# Fase 1: Baseline EEG
frames_left_eeg = int(BASE_SEC / (STEP / SRATE)) if needs_baseline_calibration and use_eeg else 0
baseline_eeg_done = not needs_baseline_calibration or not use_eeg

# Fase 2: Baseline ACC (después de EEG) - DOS sub-fases
baseline_acc_neutral_duration = 5   # segundos para capturar posición neutra
baseline_acc_movement_duration = 10 # segundos para medir rango de movimiento
# ACC baseline puede ejecutarse incluso sin EEG
frames_left_acc_neutral = int(baseline_acc_neutral_duration / (STEP / SRATE)) if needs_baseline_calibration and use_acc else 0
frames_left_acc_movement = 0  # se inicializa después de neutral
# ACC baseline solo se salta si: (a) no hay calibración, o (b) no hay ACC
baseline_acc_neutral_done = not needs_baseline_calibration or not use_acc
baseline_acc_movement_done = not needs_baseline_calibration or not use_acc
baseline_acc_done = baseline_acc_neutral_done and baseline_acc_movement_done
# Timestamps para control de baseline ACC (en lugar de solo contar frames)
acc_neutral_start_time = None
acc_movement_start_time = None

# Fase 3: Baselines de sensores de Arduino
frames_left_bio = int(BASE_SEC / (STEP / SRATE)) if needs_baseline_calibration and any((use_plant1, use_plant2, use_myo)) else 0
bio_done = not needs_baseline_calibration or not any((use_plant1, use_plant2, use_myo))

frames_left_dist = int(BASE_SEC / (STEP / SRATE)) if needs_baseline_calibration and use_dist else 0
dist_done = not needs_baseline_calibration or not use_dist

# Compatibilidad hacia atrás: many parts del código usan `baseline_done` y `frames_left`
# baseline_done debe ser True cuando TODOS los baselines requeridos están hechos
baseline_done = baseline_eeg_done and baseline_acc_done and bio_done and dist_done
frames_left = frames_left_eeg if use_eeg else frames_left_acc_neutral

# Indicador global de estado
if not baseline_eeg_done:
    baseline_phase = "eeg"
elif not baseline_acc_neutral_done:
    baseline_phase = "acc_neutral"
elif not baseline_acc_movement_done:
    baseline_phase = "acc_movement"
else:
    baseline_phase = "complete"
# --------------------

# --- Impresión ---
PREV_LEN=0

def safe_print(*args, **kwargs):
    """Imprime de forma robusta ignorando BlockingIOError del socket no-bloqueante"""
    try:
        print(*args, **kwargs)
    except BlockingIOError:
        # Socket no-bloqueante saturado, ignorar
        pass
    except Exception:
        pass

def refresh(text): 
    global PREV_LEN, show_realtime_data
    if not show_realtime_data:
        return
    pad=text.ljust(PREV_LEN)
    try:
        sys.stdout.write('\r'+pad)
        sys.stdout.flush()
    except BlockingIOError:
        # Socket no-bloqueante saturado, ignorar
        pass
    PREV_LEN=len(text)

def line_pre():
    parts=[]; mode = "SIM" if is_simulation else "REAL"
    if use_eeg:
        for b in bands:
            if is_simulation:
                parts.append(f"{b}:sim")
            else:
                r = bands[b].get('rms', np.nan)
                parts.append(f"{b}:{'nan' if (r is None or math.isnan(r)) else f'{r:.2f}'}")
    if use_acc:
        for a in acc:
            parts.append(f"{a}:{acc.get(a, 0.0):+.2f}")
    if any((use_myo,use_plant1,use_plant2)):
        for k in bio:
            if globals().get(f'use_{k}',False):
                raw = bio.get(k,{}).get('raw','-')
                parts.append(f"{k}:{'sim' if is_simulation else raw}")
    if use_dist:
        parts.append(f"dist:{'sim' if is_simulation else (dist.get('raw','-'))}")
    if use_temp_hum:
        parts.append(f"hum:{'sim' if is_simulation else (hum.get('raw','-'))}")
        parts.append(f"temp:{'sim' if is_simulation else (temp.get('raw','-'))}")
    return f"[{mode}] " + " | ".join(parts)

def line_post():
    parts=[]; mode = "SIM" if is_simulation else "REAL"
    if use_eeg:
        if eeg_processing_mode == 'individual':
            # Mostrar promedio de los 4 canales para compactar display
            for band_name in FILTS:
                avg_signed = sum(bands_per_channel[ch][band_name].get('signed_env', 0) for ch in EEG_CHANNELS) / 4
                avg_env = sum(bands_per_channel[ch][band_name].get('env', 0) for ch in EEG_CHANNELS) / 4
                avg_rms = sum(bands_per_channel[ch][band_name].get('rms', 0) for ch in EEG_CHANNELS) / 4
                avg_cc = sum(bands_per_channel[ch][band_name].get('cc', 0) for ch in EEG_CHANNELS) / 4
                parts.append(f"{band_name}:{avg_signed:+.2f}({avg_env:.2f}) r={avg_rms:.3f}→{int(avg_cc):3d}")
        else:
            for b in bands:
                signed = bands[b].get('signed_env',0.0)
                env = bands[b].get('env',0.0)
                cc = bands[b].get('cc',0)
                r = bands[b].get('rms', None)
                if isinstance(r, (int,float)) and not math.isnan(r):
                    r_str = f"{r:.3f}"
                else:
                    r_str = "nan"
                parts.append(f"{b}:{signed:+.2f}({env:.2f}) r={r_str}→{cc:3d}")
    if use_acc:
        if baseline_done:
            for a in acc:
                lo = acc_rng.get(a,{}).get('min')
                hi = acc_rng.get(a,{}).get('max')
                scaled = scale(acc.get(a,0.0), lo, hi)
                parts.append(f"{a}:{acc.get(a,0.0):+.2f}→{scaled:3d}")
        else:
            for a in acc:
                parts.append(f"{a}:calibrando")
    if use_ppg:
        if baseline_done:
            bpm = ppg.get('bpm', 0)
            cc = ppg.get('cc', 0)
            parts.append(f"♥{bpm:6.1f}bpm→{cc:3d}")
        else:
            parts.append("♥calibrando")
    if any((use_myo,use_plant1,use_plant2)):
        for k in bio:
            if globals().get(f'use_{k}',False):
                if bio_done:
                    parts.append(f"{k}:{bio.get(k,{}).get('env',0.0):.2f}→{bio.get(k,{}).get('cc',0):3d}")
                else:
                    parts.append(f"{k}:calibrando")
    if use_dist:
        if dist_done and dist.get('filt') is not None:
            parts.append(f"dist:{dist.get('filt'):.1f}→{dist.get('cc',0):3d}")
        else:
            parts.append("dist:calibrando")
    if use_temp_hum:
        parts.append(f"hum:{hum.get('raw','-')}→{hum.get('cc',0):3d}")
        parts.append(f"temp:{temp.get('raw','-')}→{temp.get('cc',0):3d}")
    return f"[{mode}] " + " | ".join(parts)
# ---------------

# --- Handlers y Parse (Solo modo real) ---
def muse_eeg(_, *vals):
    """Handler EEG - Soporta modo promedio y multicanal (4 canales)
    Muse envía mensajes con:
    - 1 valor: modo promedio
    - 4 valores: [TP9, AF7, AF8, TP10]
    - 6 valores: [TP9, AF7, AF8, TP10, AUX_LEFT, AUX_RIGHT] - formato Muse 2
    """
    if not use_eeg or is_simulation: return
    global frames_left, baseline_done, baseline_eeg_done
    
    if debug_mode and baseline_done and len(vals) > 0:
        print(f"[EEG DEBUG] Recibido {len(vals)} valores, modo: {eeg_processing_mode}")
    
    if len(vals) == 0:
        if baseline_done:
            print(f"[EEG] ⚠️ Sin datos recibidos")
        return
    
    # Detectar si tenemos datos multicanal: 4 o 6 valores
    if (len(vals) == 4 or len(vals) == 6) and eeg_processing_mode == 'individual':
        # Procesar multicanal: usar los primeros 4 valores (canales principales)
        process_eeg_multichannel(vals[:4])  # TP9, AF7, AF8, TP10
    
    # Siempre procesar también el promedio (compatible con v24)
    # para evitar duplicar lógica y permitir envío de datos en todos los modos
    valid_vals = [v for v in vals if not (v is None or (isinstance(v, float) and math.isnan(v)))]
    if not valid_vals:
        if baseline_done:
            print(f"[EEG] ⚠️ Todos los valores son NaN")
        return
    mean_val = float(np.mean(valid_vals))
    eeg_buf.append(mean_val)
    process_eeg_average()

def process_eeg_multichannel(vals):
    """Procesa 4 canales EEG individuales del Muse 2
    vals = [tp9_sample, af7_sample, af8_sample, tp10_sample]
    Cada llamada agrega UNA muestra por canal
    """
    global frames_left, baseline_done, baseline_eeg_done, baseline_eeg_start_sent
    
    if len(vals) != 4:
        print(f"⚠️ Esperaba 4 valores, recibí {len(vals)}")
        return
    
    # Agregar un sample por canal
    for idx, ch_name in enumerate(EEG_CHANNELS):
        sample_val = vals[idx]
        if sample_val is not None and not (isinstance(sample_val, float) and math.isnan(sample_val)):
            eeg_buf_per_channel[ch_name].append(float(sample_val))
    
    # Verificar si tenemos suficientes muestras (WIN samples)
    all_ready = all(len(eeg_buf_per_channel[ch]) >= WIN for ch in EEG_CHANNELS)
    if not all_ready:
        return  # Seguir acumulando samples
    
    # Procesar cada canal con ventana completa
    channel_results = {}
    for ch_name in EEG_CHANNELS:
        seg = np.array(eeg_buf_per_channel[ch_name])
        ch_env = []
        ch_signed = []
        ch_raw = []
        
        try:
            for band_name, filt in FILTS.items():
                r = band_rms(seg, filt)
                bands_per_channel[ch_name][band_name]['rms'] = r
                ch_raw.append(float(r) if (r is not None and not math.isnan(r)) else float('nan'))
                
                if not baseline_done:
                    if r is not None and not math.isnan(r):
                        bands_per_channel[ch_name][band_name]['buf'].append(r)
                else:
                    mu = bands_per_channel[ch_name][band_name]['mu']
                    sd = bands_per_channel[ch_name][band_name]['sd']
                    if mu is None or sd is None: continue
                    
                    prev_signed = bands_per_channel[ch_name][band_name]['signed_env']
                    if sd <= 1e-9 or r is None or math.isnan(r):
                        signed_z = 0.0
                    else:
                        signed_z = (r - mu) / sd
                    
                    current_signed = ALPHA_ENV * signed_z + (1 - ALPHA_ENV) * prev_signed
                    bands_per_channel[ch_name][band_name]['signed_env'] = current_signed
                    current_env = abs(current_signed)
                    bands_per_channel[ch_name][band_name]['env'] = current_env
                    bands_per_channel[ch_name][band_name]['cc'] = scale(current_env, 0, Z_MAX)
                    
                    ch_env.append(current_env)
                    ch_signed.append(current_signed)
            
            channel_results[ch_name] = {'env': ch_env, 'signed': ch_signed, 'raw': ch_raw}
        except Exception as e:
            print(f"Error procesando canal {ch_name}: {e}")
    
    # Enviar datos multicanal
    if baseline_done:
        try:
            for ch_name in EEG_CHANNELS:
                if ch_name in channel_results:
                    ch_lower = ch_name.lower()
                    if len(channel_results[ch_name]['env']) == 5:
                        send_proc(f"/py/{ch_lower}/bands_env", channel_results[ch_name]['env'])
                        send_proc(f"/py/{ch_lower}/bands_signed_env", channel_results[ch_name]['signed'])
                        raw_fmt = [round(x,3) if not math.isnan(x) else 0.0 for x in channel_results[ch_name]['raw']]
                        send_proc(f"/py/{ch_lower}/bands_raw", raw_fmt)
        except Exception as e:
            print(f"Error enviando OSC multicanal: {e}")
    
    # Baseline
    if not baseline_done:
        complete_baseline_phase()
    
    # Limpiar buffers
    if STEP > 0:
        for ch_name in EEG_CHANNELS:
            for _ in range(min(STEP, len(eeg_buf_per_channel[ch_name]))):
                if eeg_buf_per_channel[ch_name]:
                    eeg_buf_per_channel[ch_name].popleft()

def process_eeg_average():
    """Procesa EEG en modo promedio (v24 compatible)"""
    global frames_left, baseline_done, baseline_eeg_done, baseline_eeg_start_sent
    
    if len(eeg_buf) < WIN:
        return
    
    seg = np.array(eeg_buf)
    osc_band_values_env = []
    osc_band_values_signed = []
    osc_band_values_raw = []
    
    try:
        for n, f in FILTS.items():
            r = band_rms(seg, f)
            bands[n]['rms'] = r
            # guardar raw (si es numérico) para salida
            osc_band_values_raw.append(float(r) if (r is not None and not math.isnan(r)) else float('nan'))
            if not baseline_done:
                 if r is not None and not math.isnan(r): bands[n]['buf'].append(r)
            else:
                if bands[n]['mu'] is None or bands[n]['sd'] is None: continue
                # Calcular z-score (signed) y usar el mismo valor suavizado para signed y env
                mu = bands[n]['mu']; sd = bands[n]['sd']; prev_signed_env = bands[n]['signed_env']
                eps = 1e-9
                if sd is None or sd <= eps or r is None or (isinstance(r, float) and math.isnan(r)):
                    signed_z_raw = 0.0
                else:
                    signed_z_raw = (r - mu) / sd

                # Suavizar el z-score (misma alpha para signed y luego env = abs(signed))
                current_signed = ALPHA_ENV * signed_z_raw + (1 - ALPHA_ENV) * prev_signed_env
                bands[n]['signed_env'] = current_signed

                # Env debe ser la magnitud absoluta del signed suavizado (misma magnitud)
                current_env = abs(current_signed)
                bands[n]['env'] = current_env

                # Actualizar CC usando la misma escala (0..Z_MAX)
                bands[n]['cc'] = c = scale(current_env, 0, Z_MAX)
                set_cc(n, c)

                osc_band_values_env.append(current_env)
                osc_band_values_signed.append(current_signed)
    except Exception as e:
        print(f"\n!!! Error calculando bandas: {e}")
        osc_band_values_env = []
        osc_band_values_signed = []
        osc_band_values_raw = []
    
    if baseline_done:
        try:
            if len(osc_band_values_env)==5:
                send_proc("/py/bands_env", osc_band_values_env)
            if len(osc_band_values_signed)==5:
                send_proc("/py/bands_signed_env", osc_band_values_signed)
            # Enviar raw RMS con 3 decimales
            if len(osc_band_values_raw)==5:
                raw_3 = [round(x,3) if (isinstance(x,(int,float)) and not math.isnan(x)) else float('nan') for x in osc_band_values_raw]
                send_proc("/py/bands_raw", raw_3)
        except Exception as e:
            print(f"!!! Error enviando OSC continuo: {e}")
    if not baseline_done and use_eeg:
        complete_baseline_phase()

            
    # No mostrar line_pre durante baseline con EEG
    if use_eeg and not baseline_done: pass
    elif not (baseline_done and bio_done and dist_done):
        refresh(line_pre())
    else:
        refresh(line_post())
    if STEP > 0:
        for _ in range(STEP):
            if eeg_buf:
                eeg_buf.popleft()

def complete_baseline_phase():
    """Completa la fase de baseline EEG (común para ambos modos)"""
    global frames_left, baseline_done, baseline_eeg_done, baseline_eeg_start_sent
    
    if not baseline_eeg_start_sent:
        send_baseline_event("eeg", "start", BASE_SEC)
        baseline_eeg_start_sent = True
    
    frames_left -= 1
    total_frames = int(BASE_SEC / (STEP / SRATE))
    frames_done = total_frames - frames_left
    progress_pct = max(0, int((frames_done / max(1, total_frames)) * 100))
    progress_bar = "█" * (progress_pct // 5) + "░" * (20 - progress_pct // 5)
    tiempo_restante = max(0, BASE_SEC - (frames_done * STEP / SRATE))
    
    send_baseline_event("eeg", "progress", progress_pct)
    sys.stdout.write(f"\r[BASELINE] {progress_bar} {progress_pct:3d}% | ⏱️  {tiempo_restante:5.1f}s restantes")
    sys.stdout.flush()
    
    if frames_left <= 0:
        sys.stdout.write("\n")
        print(f"\n✨ Calculando baseline (modo: {eeg_processing_mode.upper()})...\n")
        
        if eeg_processing_mode == 'individual':
            # Baseline multicanal
            for ch_name in EEG_CHANNELS:
                print(f"📡 Canal {ch_name}:")
                for band_name in FILTS:
                    arr = np.array(bands_per_channel[ch_name][band_name]['buf'])
                    if arr.size > 0:
                        mu_val = arr.mean()
                        sd_val = arr.std() if arr.size > 1 else 1e-9
                        min_val = float(np.min(arr))
                        max_val = float(np.max(arr))
                        bands_per_channel[ch_name][band_name]['mu'] = mu_val
                        bands_per_channel[ch_name][band_name]['sd'] = sd_val
                        baseline_eeg_values_per_channel[ch_name][band_name] = {
                            'mu': mu_val, 'sigma': sd_val, 'min': min_val, 'max': max_val
                        }
                        print(f"  ✓ {band_name:6s}: μ={mu_val:6.3f} σ={sd_val:6.3f} [{min_val:6.3f}, {max_val:6.3f}]")
                        bands_per_channel[ch_name][band_name]['buf'] = []
                    else:
                        bands_per_channel[ch_name][band_name]['mu'] = 1.0
                        bands_per_channel[ch_name][band_name]['sd'] = 1e-9
                print()
            print("✅ ¡Baseline MULTICANAL completado!")
        else:
            # Baseline promedio
            baseline_mu_values = []
            all_bands_valid = True
            for n in bands:
                arr = np.array(bands[n]['buf'])
                if arr.size > 0:
                    bands[n]['mu'] = mu_val = arr.mean()
                    bands[n]['sd'] = sd_val = arr.std() if arr.size > 1 else 1e-9
                    min_val = float(np.min(arr))
                    max_val = float(np.max(arr))
                    baseline_eeg_values[n] = {'mu': mu_val, 'sigma': sd_val, 'min': min_val, 'max': max_val}
                    print(f"  ✓ {n:8s}: μ={mu_val:7.3f} σ={sd_val:7.3f} [{min_val:7.3f}, {max_val:7.3f}]")
                else:
                    bands[n]['mu'] = mu_val = 1.0
                    bands[n]['sd'] = 1e-9
                    baseline_eeg_values[n] = {'mu': 1.0, 'sigma': 1e-9, 'min': 1.0, 'max': 1.0}
                    all_bands_valid = False
                bands[n]['buf'] = []
                baseline_mu_values.append(mu_val)
            
            if all_bands_valid:
                print("\n✅ ¡Baseline EEG completado!")
            if len(baseline_mu_values) == 5:
                send_proc("/py/baseline_mu", baseline_mu_values, force=True)
        
        send_baseline_event("eeg", "end")
        baseline_eeg_start_sent = False
        baseline_eeg_done = True
        baseline_done = True
        
        if use_acc:
            print(f"\n🔄 Iniciando FASE ACC: Posición Neutra ({baseline_acc_neutral_duration}s)...")
            print("   ⚠️ MANTÉN CABEZA EN POSICIÓN NEUTRAL\n")

def muse_acc(_, x, y, z):
    if not use_acc or is_simulation: return
    global frames_left_acc_neutral, frames_left_acc_movement, baseline_acc_neutral_done, baseline_acc_movement_done, baseline_acc_done, baseline_eeg_done, baseline_done
    global acc_neutral_start_time, acc_movement_start_time
    
    # Si hay EEG, ignorar ACC durante baseline EEG
    if use_eeg and not baseline_eeg_done:
        return
    
    # Si no hay EEG pero ACC baseline aún no está hecho, procesar ACC
    if use_acc and baseline_acc_done:
        # Ya está hecho el baseline, procesar normalmente
        pass
    
    if x is None or y is None or z is None or any(math.isnan(v) for v in (x,y,z)):
        if baseline_acc_done:
            print(f"[ACC] ⚠️ Valores NaN recibidos - revisar conexión Muse")
        return
    
    acc.update(x=x, y=y, z=z)
    try:
        send_proc("/py/acc", [x, y, z])
    except Exception:
        pass
    
    current_time = time.time()
    
    # FASE A: POSICIÓN NEUTRA (5 segundos)
    if not baseline_acc_neutral_done:
        global baseline_acc_neutral_start_sent
        
        # Inicializar timestamp si no existe
        if acc_neutral_start_time is None:
            acc_neutral_start_time = current_time
            # Enviar evento de inicio (solo una vez)
            if not baseline_acc_neutral_start_sent:
                send_baseline_event("acc_neutral", "start", baseline_acc_neutral_duration)
                baseline_acc_neutral_start_sent = True
        
        elapsed = current_time - acc_neutral_start_time
        
        for a in acc:
            rng = acc_rng[a]
            # Guardar valores para calcular desviación estándar después
            rng['values'].append(acc[a])
            # Guardar min/max para posición neutral
            rng['neutral_min'] = acc[a] if rng.get('neutral_min') is None else min(rng.get('neutral_min'), acc[a])
            rng['neutral_max'] = acc[a] if rng.get('neutral_max') is None else max(rng.get('neutral_max'), acc[a])
        
        # Mostrar progreso NEUTRAL (basado en tiempo real)
        progress_pct = max(0, min(100, int((elapsed / baseline_acc_neutral_duration) * 100)))
        progress_bar = "█" * (progress_pct // 5) + "░" * (20 - progress_pct // 5)
        tiempo_restante = max(0, baseline_acc_neutral_duration - elapsed)
        
        # Enviar progreso
        send_baseline_event("acc_neutral", "progress", progress_pct)
        
        sys.stdout.write(f"\r[NEUTRAL] {progress_bar} {progress_pct:3d}% | ⏱️  {tiempo_restante:5.1f}s")
        sys.stdout.flush()
        
        if elapsed >= baseline_acc_neutral_duration:
            # Enviar evento de término
            send_baseline_event("acc_neutral", "end")
            baseline_acc_neutral_start_sent = False
            
            # Transición a FASE B (movimiento)
            baseline_acc_neutral_done = True
            acc_movement_start_time = current_time  # Inicializar tiempo para movimiento
            sys.stdout.write("\n")
            print("\n✅ Posición neutra CAPTURADA")
            print(f"\n🔄 Iniciando fase de RANGO DE MOVIMIENTO ({baseline_acc_movement_duration}s)...")
            print("   ¡Ahora MUEVE TU CABEZA en todas direcciones para calibrar rango!\n")
    
    # FASE B: RANGO DE MOVIMIENTO (10 segundos)
    elif not baseline_acc_movement_done:
        global baseline_acc_movement_start_sent
        
        # Inicializar timestamp si no existe
        if acc_movement_start_time is None:
            acc_movement_start_time = current_time
            # Enviar evento de inicio (solo una vez)
            if not baseline_acc_movement_start_sent:
                send_baseline_event("acc_movement", "start", baseline_acc_movement_duration)
                baseline_acc_movement_start_sent = True
        
        elapsed = current_time - acc_movement_start_time
        
        for a in acc:
            rng = acc_rng[a]
            # Guardar valores para calcular desviación estándar después
            rng['values'].append(acc[a])
            # Guardar min/max para rango de movimiento
            rng['min'] = acc[a] if rng['min'] is None else min(rng['min'], acc[a])
            rng['max'] = acc[a] if rng['max'] is None else max(rng['max'], acc[a])
        
        # Mostrar progreso MOVIMIENTO (basado en tiempo real)
        progress_pct = max(0, min(100, int((elapsed / baseline_acc_movement_duration) * 100)))
        progress_bar = "█" * (progress_pct // 5) + "░" * (20 - progress_pct // 5)
        tiempo_restante = max(0, baseline_acc_movement_duration - elapsed)
        
        # Enviar progreso
        send_baseline_event("acc_movement", "progress", progress_pct)
        
        sys.stdout.write(f"\r[MOVIMIENTO] {progress_bar} {progress_pct:3d}% | ⏱️  {tiempo_restante:5.1f}s")
        sys.stdout.flush()
        
        if elapsed >= baseline_acc_movement_duration:
            # Enviar evento de término
            send_baseline_event("acc_movement", "end")
            baseline_acc_movement_start_sent = False
            
            # Cerrar baseline ACC
            close_baseline_acc()
    
    # FASE C: OPERACIÓN NORMAL - Medir desviación respecto a baseline
    else:
        for a in acc:
            baseline_val = acc_baseline.get(a, 0.0)
            deviation = acc[a] - baseline_val
            v = scale(abs(deviation), 0, 0.5)  # Rango de movimiento típico
            set_cc('acc'+a, v)
            try:
                send_proc(f"/py/acc_{a}_deviation", float(deviation))
            except Exception:
                pass
        # Nota: refresh() no se llama desde handlers OSC para evitar threading issues


def muse_ppg(_, *args):
    """Recibe PPG (photoplethysmography) - heartbeat desde Muse
    El mensaje contiene 3 valores: (nan, ppg_value, nan)
    El segundo valor es un timestamp/amplitud que varía según el pulso cardíaco
    Estrategia: usar la variación relativa (derivada) como indicador de BPM
    """
    if not use_ppg or is_simulation: return
    
    # Muse envía 3 valores, el útil es el segundo (índice 1)
    if len(args) < 2:
        if debug_mode and baseline_done:
            print(f"[PPG] ⚠️ Formato incorrecto: esperaba 3 valores, recibió {len(args)}")
        return
    
    ppg_value = args[1]  # ← Extraer el segundo valor
    
    if ppg_value is None or (isinstance(ppg_value, float) and math.isnan(ppg_value)):
        if debug_mode and baseline_done:
            print(f"[PPG] ⚠️ Valor NaN recibido en índice 1")
        return
    
    ppg_value_float = float(ppg_value)
    ppg['raw'] = ppg_value_float
    
    # PPG: usar amplitud de la onda como proxy de BPM
    # Muse PPG: valores típicos 125M-126M, representan la amplitud fotopletismográfica
    # Estrategia: aplicar filtro de banda y estimar BPM desde variación
    
    # Mantener buffer de últimos 10 valores para calcular variación
    if 'buffer' not in ppg:
        ppg['buffer'] = deque(maxlen=10)
    
    ppg['buffer'].append(ppg_value_float)
    
    # Si hay suficientes muestras, calcular BPM estimado
    if len(ppg['buffer']) >= 5:
        # Calcular delta respecto a promedio móvil
        buf_array = np.array(list(ppg['buffer']))
        mean_val = np.mean(buf_array)
        std_val = np.std(buf_array)
        
        # Usar desviación estándar como indicador de amplitud de pulso
        # std_val típicamente 100,000-500,000 para pulso presente
        # Mapear a rango de BPM fisiológico (60-100 en reposo, 120+ en actividad)
        
        # Normalizar std a 0-1 (rango observado ~100k-500k)
        normalized_amplitude = min(1.0, std_val / 300000.0)
        
        # Mapear a BPM: 60 (reposo) a 140 (máximo)
        bpm_min = 60
        bpm_max = 140
        bpm = bpm_min + (normalized_amplitude * (bpm_max - bpm_min))
        
        ppg['bpm'] = float(bpm)
        
        try:
            send_proc("/py/ppg/bpm", float(bpm))
        except BlockingIOError:
            pass  # Socket no-bloqueante saturado
        except Exception:
            pass
        
        if baseline_done and debug_mode:
            print(f"[PPG] Amp: {std_val:.0f} → BPM: {bpm:.1f}")
        
        if baseline_done:
            # Actualizar CC (control change) para PPG en escala MIDI 0-127
            ppg_cc = int(scale(bpm, bpm_min, bpm_max))
            ppg['cc'] = ppg_cc
            # Nota: refresh() no se llama aquí para evitar conflictos de threading
            # El loop principal refrescará la pantalla
    
    try:
        # Enviar valor raw también
        send_proc("/py/ppg", ppg_value_float)
    except BlockingIOError:
        pass
    except Exception:
        pass


def muse_gyro(_, x, y, z):
    """Recibe datos del giróscopo desde Muse"""
    if not use_gyro or is_simulation: return
    
    if x is None or y is None or z is None or any(math.isnan(v) for v in (x,y,z)):
        if debug_mode and baseline_done:
            print(f"[GYRO] ⚠️ Valores NaN recibidos")
        return
    
    gyro.update(x=float(x), y=float(y), z=float(z))
    
    try:
        send_proc("/py/gyro", [float(x), float(y), float(z)])
    except Exception:
        pass
    
    # Nota: refresh() no se llama desde handlers OSC para evitar threading issues


def muse_jaw(_, jaw_clenched):
    """Recibe detección de jaw clench desde Muse"""
    if not use_jaw or is_simulation: return
    
    if jaw_clenched is None:
        return
    
    jaw['clenched'] = int(jaw_clenched)
    
    try:
        send_proc("/py/jaw", int(jaw_clenched))
    except Exception:
        pass
    
    # Nota: refresh() no se llama desde handlers OSC para evitar threading issues


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
    if use_dist: update_bio('dist', di)
    if use_temp_hum:
        hum['raw'], temp['raw'] = hu, te
        if bio_done: hum['cc']=c_hum=scale(hu,0,100); set_cc('hum',c_hum); temp['cc']=c_temp=scale(te,10,40); set_cc('temp',c_temp);
        try: send_proc("/py/hum", c_hum); send_proc("/py/temp", c_temp)
        except Exception: pass
        
    # No mostrar line_pre durante baseline con EEG (solo mostrar barra progreso)
    if use_eeg and not baseline_done: pass
    elif not (baseline_done and bio_done and dist_done): refresh(line_pre())
    else: refresh(line_post())

def update_bio(k, x): # ... (igual que v19) ...
    if is_simulation: return
    if not globals().get(f'use_{k}', False): return
    if math.isnan(x): return
    b = bio[k]; b['raw'] = x
    if not bio_done: b['min']=x if b['min'] is None else min(b['min'],x); b['max']=x if b['max'] is None else max(b['max'],x); b['sum']+=x; b['cnt']+=1
    elif bio_done and b['mu'] is not None and b['amp'] is not None:
        rect = abs(x - b['mu']); b['env'] = ALPHA_ENV*rect+(1-ALPHA_ENV)*b['env']; b['cc'] = c = scale(b['env'], 0, b['amp']); set_cc(k, c)
        try: send_proc(f"/py/{k}", c)
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
        try: send_proc("/py/dist", c)
        except Exception: pass

def serial_loop(): # ... (igual que v19) ...
    if is_simulation: return
    try:
        import serial
    except ImportError:
        print("Serial support not available; serial loop disabled.")
        return

    if not any((use_myo, use_plant1, use_plant2, use_temp_hum, use_dist)):
        print("Serial loop no iniciado.")
        return
    ser = None
    while threads_active:
        try:
            if ser is None or not getattr(ser, 'is_open', False):
                ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
                print(f"Puerto serial {SERIAL_PORT} abierto/reabierto.")
            if not threads_active: break
            ln = ser.readline()
            if ln: parse_serial(ln)
            else: time.sleep(0.01)
        except serial.SerialException as e:
            print(f"Error serial: {e}. Reconectando en 10s...")
        except Exception as e:
            print(f"Error inesperado serial: {e}")
        finally:
            if 'e' in locals() and isinstance(e, getattr(serial, 'SerialException', Exception)):
                if ser and getattr(ser, 'is_open', False):
                    ser.close(); ser = None; time.sleep(10)
            elif 'e' in locals():
                time.sleep(1)
    if ser and getattr(ser, 'is_open', False):
        ser.close(); print("Puerto serial cerrado.")
# ------------------------

# --- Cerrar Baselines Secuencial ---
def close_baseline_eeg():
    """Termina fase EEG, comienza ACC"""
    if is_simulation: return
    global baseline_eeg_done, frames_left_acc, baseline_eeg_values
    
    sys.stdout.write("\n")  # Nueva línea para separar
    baseline_mu_values = []
    print("\n✨ Calculando baseline MU/SD...\n")
    all_bands_valid = True
    
    for n in bands:
        arr = np.array(bands[n]['buf'])
        if arr.size > 0:
            mu_val = arr.mean()
            sd_val = arr.std() if arr.size > 1 else 1e-9
            min_val = float(np.min(arr))
            max_val = float(np.max(arr))
            bands[n]['mu'] = mu_val
            bands[n]['sd'] = sd_val
            # Guardar en variable global para CSV y TouchDesigner
            baseline_eeg_values[n] = {'mu': mu_val, 'sigma': sd_val, 'min': min_val, 'max': max_val}
            print(f"  ✓ {n:8s}: μ={mu_val:7.3f} σ={sd_val:7.3f} min={min_val:7.3f} max={max_val:7.3f} ({arr.size:4d} muestras)")
        else:
            print(f"  ⚠️ {n:8s}: SIN DATOS - usando valores por defecto")
            bands[n]['mu'] = 1.0
            bands[n]['sd'] = 1e-9
            baseline_eeg_values[n] = {'mu': 1.0, 'sigma': 1e-9, 'min': 1.0, 'max': 1.0}
            all_bands_valid = False
        bands[n]['buf'] = []
        baseline_mu_values.append(bands[n]['mu'])
    
    if all_bands_valid:
        print("\n✅ ¡Baseline EEG COMPLETADO!")
    else:
        print("\n⚠️ Baseline EEG con valores por defecto - revisar conexión Muse")
    
    try:
        if len(baseline_mu_values) == 5:
            print(f"\n📤 Enviando baseline a Processing: {[f'{x:.2f}' for x in baseline_mu_values]}")
            send_proc("/py/baseline_mu", baseline_mu_values, force=True)
            
            # Enviar desviación estándar para cada banda
            baseline_sigma_values = [baseline_eeg_values[n].get('sigma', 0.0) for n in ['delta', 'theta', 'alpha', 'beta', 'gamma']]
            send_proc("/py/baseline_sigma", baseline_sigma_values, force=True)
            print(f"📤 Enviando sigma (desv. estándar): {[f'{x:.3f}' for x in baseline_sigma_values]}")
            
            # Enviar valores mínimos para cada banda
            baseline_min_values = [baseline_eeg_values[n].get('min', 0.0) for n in ['delta', 'theta', 'alpha', 'beta', 'gamma']]
            send_proc("/py/baseline_min", baseline_min_values, force=True)
            print(f"📤 Enviando mínimos: {[f'{x:.3f}' for x in baseline_min_values]}")
            
            # Enviar valores máximos para cada banda
            baseline_max_values = [baseline_eeg_values[n].get('max', 0.0) for n in ['delta', 'theta', 'alpha', 'beta', 'gamma']]
            send_proc("/py/baseline_max", baseline_max_values, force=True)
            print(f"📤 Enviando máximos: {[f'{x:.3f}' for x in baseline_max_values]}")
    except Exception as e:
        print(f"Error enviando baseline estadísticas: {e}")
    
    baseline_eeg_done = True
    
    # Si hay ACC, iniciar su baseline; si no, marcar como listo
    if use_acc:
        frames_left_acc_neutral = int(baseline_acc_neutral_duration / (STEP / SRATE))
        print(f"\n🔄 Iniciando FASE 1: Posición Neutra ({baseline_acc_neutral_duration}s)...")
        print("   ⚠️ MANTÉN TU CABEZA EN POSICIÓN NEUTRAL (sin movimiento)\n")
    else:
        print("✅ Baseline ACC (no seleccionado)")

def close_baseline_acc():
    """Termina fases ACC (neutral + movimiento), comienza operación"""
    if is_simulation: return
    global baseline_acc_movement_done, baseline_acc_done
    global baseline_acc_x, baseline_acc_y, baseline_acc_z
    
    sys.stdout.write("\n")  # Nueva línea para separar
    print("\n✨ Calculando posición neutral, rango de movimiento y desviación estándar ACC...\n")
    
    # Calcular posición neutral como promedio de la FASE A (neutral)
    for a in acc:
        rng = acc_rng[a]
        
        # Posición neutral: promedio de lo capturado en FASE A
        if rng.get('neutral_min') is not None and rng.get('neutral_max') is not None:
            neutral_pos = (rng['neutral_min'] + rng['neutral_max']) / 2.0
            acc_baseline[a] = neutral_pos
            
            # Rango de movimiento: diferencia max-min de FASE B
            movement_range = rng['max'] - rng['min'] if (rng['min'] is not None and rng['max'] is not None) else 1.0
            movement_range = max(movement_range, 0.01)  # Evitar división por cero
            
            # Calcular desviación estándar de todos los valores capturados
            sigma = 0.0
            if rng.get('values') and len(rng['values']) > 1:
                sigma = float(np.std(rng['values']))
            
            print(f"  ✓ {a}: neutral={neutral_pos:+.4f} | rango=[{rng['min']:+.4f}, {rng['max']:+.4f}] (Δ={movement_range:.4f}) σ={sigma:.4f}")
            
            # Guardar en variables globales separadas para TouchDesigner (incluyendo sigma)
            if a == 'x':
                baseline_acc_x = {'neutral': neutral_pos, 'min': rng['min'], 'max': rng['max'], 'range': movement_range, 'sigma': sigma}
            elif a == 'y':
                baseline_acc_y = {'neutral': neutral_pos, 'min': rng['min'], 'max': rng['max'], 'range': movement_range, 'sigma': sigma}
            elif a == 'z':
                baseline_acc_z = {'neutral': neutral_pos, 'min': rng['min'], 'max': rng['max'], 'range': movement_range, 'sigma': sigma}
        else:
            acc_baseline[a] = 0.0
            print(f"  ⚠️ {a}: SIN DATOS - usando 0.0 como baseline")
            if a == 'x':
                baseline_acc_x = {'neutral': 0.0, 'min': 0.0, 'max': 0.0, 'range': 0.0, 'sigma': 0.0}
            elif a == 'y':
                baseline_acc_y = {'neutral': 0.0, 'min': 0.0, 'max': 0.0, 'range': 0.0, 'sigma': 0.0}
            elif a == 'z':
                baseline_acc_z = {'neutral': 0.0, 'min': 0.0, 'max': 0.0, 'range': 0.0, 'sigma': 0.0}
    
    baseline_acc_movement_done = True
    baseline_acc_done = True
    print("\n✅ Sistema COMPLETAMENTE CALIBRADO - Operación normal iniciada (env y raw en envío continuo).")
    
    # Enviar baseline ACC a TouchDesigner
    try:
        send_proc("/py/acc_x_neutral", baseline_acc_x['neutral'] if baseline_acc_x else 0.0, force=True)
        send_proc("/py/acc_x_range", baseline_acc_x['range'] if baseline_acc_x else 0.0, force=True)
        send_proc("/py/acc_x_min", baseline_acc_x['min'] if baseline_acc_x else 0.0, force=True)
        send_proc("/py/acc_x_max", baseline_acc_x['max'] if baseline_acc_x else 0.0, force=True)
        send_proc("/py/acc_x_sigma", baseline_acc_x['sigma'] if baseline_acc_x else 0.0, force=True)
        
        send_proc("/py/acc_y_neutral", baseline_acc_y['neutral'] if baseline_acc_y else 0.0, force=True)
        send_proc("/py/acc_y_range", baseline_acc_y['range'] if baseline_acc_y else 0.0, force=True)
        send_proc("/py/acc_y_min", baseline_acc_y['min'] if baseline_acc_y else 0.0, force=True)
        send_proc("/py/acc_y_max", baseline_acc_y['max'] if baseline_acc_y else 0.0, force=True)
        send_proc("/py/acc_y_sigma", baseline_acc_y['sigma'] if baseline_acc_y else 0.0, force=True)
        
        send_proc("/py/acc_z_neutral", baseline_acc_z['neutral'] if baseline_acc_z else 0.0, force=True)
        send_proc("/py/acc_z_range", baseline_acc_z['range'] if baseline_acc_z else 0.0, force=True)
        send_proc("/py/acc_z_min", baseline_acc_z['min'] if baseline_acc_z else 0.0, force=True)
        send_proc("/py/acc_z_max", baseline_acc_z['max'] if baseline_acc_z else 0.0, force=True)
        send_proc("/py/acc_z_sigma", baseline_acc_z['sigma'] if baseline_acc_z else 0.0, force=True)
        
        print("📤 Datos de baseline ACC (neutral, rango, min, max, sigma) enviados a TouchDesigner")
    except Exception as e:
        print(f"Error enviando baseline ACC: {e}")

def close_baseline_eeg_only():
    """Cierra baseline EEG cuando ACC no está seleccionado"""
    if is_simulation: return
    global baseline_eeg_done, baseline_done, baseline_acc_done
    close_baseline_eeg()
    baseline_eeg_done = True
    baseline_done = True
    # Si no hay ACC, marcar ACC como completo también
    if not use_acc:
        baseline_acc_done = True

def close_bio():
    if is_simulation: return
    global bio_done
    print("Cerrando baseline Bio...")
    for k, b in bio.items():
        if globals().get(f'use_{k}', False):
            if b['cnt'] == 0:
                print(f"Advertencia: No datos {k}")
                b['mu'], b['amp'] = 0, 1
            else:
                b['mu'] = b['sum'] / b['cnt']
                b_min = b['min'] if b['min'] is not None else b['mu']
                b_max = b['max'] if b['max'] is not None else b['mu']
                b['amp'] = max(b['mu'] - b_min, b_max - b['mu'])
                b['amp'] = max(b['amp'], 1e-9)
            b['env'] = 0
            print(f"Baseline {k}: mu={b['mu']:.2f}, amp={b['amp']:.2f} (min={b['min']}, max={b['max']})")
    bio_done = True
    print("✅ Baseline Myo/Plantas completado")

def close_dist():
    if is_simulation: return
    global dist_done
    print("Cerrando baseline Dist...")
    if dist['min'] is None or dist['max'] is None or dist['min'] >= dist['max']:
        print("Advertencia: No datos Dist")
        dist['min'], dist['max'] = 0, 100
    else:
        print(f"Baseline Dist: min={dist['min']:.1f}, max={dist['max']:.1f}")
    dist_done = True
    print("✅ Baseline Distancia completado")
# ---------------------

# --- Bucle de Simulación ---
# ... (igual que v19) ...
def simulation_loop():
    global baseline_done, bio_done, dist_done
    print("\n--- Iniciando Modo Simulación ---")
    print(f"Modo EEG: {eeg_processing_mode.upper()}")
    baseline_done = True; bio_done = True; dist_done = True
    baseline_mu_values = [MU_DEFAULTS.get(b, 1.0) for b in FILTS]
    try:
        send_proc("/py/baseline_mu", baseline_mu_values, force=True)
    except Exception as e:
        print(f"Error enviando baseline: {e}")
    t_sim = 0.0
    print("Simulación iniciada. Presiona Ctrl+C para detener.")
    while threads_active:
        try:
            row_start_time = time.time()
            # Generar datos
            s_env_delta=1.5*math.sin(0.2*t_sim)
            s_env_theta=1.8*math.sin(0.4*t_sim+1.5)
            s_env_alpha=2.0*math.sin(0.6*t_sim+3.0)
            s_env_beta=1.5*math.sin(1.0*t_sim+4.5)
            s_env_gamma=1.0*math.sin(1.5*t_sim+6.0)
            osc_signed = [s_env_delta, s_env_theta, s_env_alpha, s_env_beta, s_env_gamma]
            env_delta=0.1+((math.sin(0.22*t_sim)+1.0)/2.0)*(Z_MAX-0.2)
            env_theta=0.1+((math.sin(0.42*t_sim+1.7)+1.0)/2.0)*(Z_MAX-0.4)
            env_alpha=0.1+((math.sin(0.62*t_sim+3.2)+1.0)/2.0)*(Z_MAX-0.5)
            env_beta=0.1+((math.sin(1.02*t_sim+4.7)+1.0)/2.0)*(Z_MAX-1.0)
            env_gamma=0.1+((math.sin(1.52*t_sim+6.2)+1.0)/2.0)*(Z_MAX-1.5)
            osc_env = [env_delta, env_theta, env_alpha, env_beta, env_gamma]
            accX=0.8*math.sin(0.15*t_sim)
            accY=0.6*math.cos(0.12*t_sim+1.0)
            accZ=0.1*math.sin(0.08*t_sim+2.0)
            osc_acc = [accX, accY, accZ]
            
            # Actualizar estado
            for i, n in enumerate(FILTS.keys()):
                bands[n]['signed_env'] = osc_signed[i]
                bands[n]['env'] = osc_env[i]
                bands[n]['cc'] = scale(bands[n]['env'], 0, Z_MAX)
                set_cc(n, bands[n]['cc'])
            for i, a in enumerate(['x', 'y', 'z']):
                acc[a] = osc_acc[i]
                set_cc('acc'+a, scale(acc[a], -1.0, 1.0))
            
            # Generar valores raw simulados
            osc_raw = [
                MU_DEFAULTS.get('delta', 1.2) + 0.3*math.sin(0.25*t_sim),
                MU_DEFAULTS.get('theta', 1.0) + 0.2*math.sin(0.45*t_sim+1.5),
                MU_DEFAULTS.get('alpha', 1.0) + 0.25*math.sin(0.65*t_sim+3.0),
                MU_DEFAULTS.get('beta', 0.8) + 0.15*math.sin(1.05*t_sim+4.5),
                MU_DEFAULTS.get('gamma', 0.5) + 0.1*math.sin(1.55*t_sim+6.0)
            ]
            
            # 5. Enviar OSC
            send_proc("/py/bands_signed_env", osc_signed, force=True)
            send_proc("/py/bands_env", osc_env, force=True)
            send_proc("/py/bands_raw", osc_raw, force=True)
            send_proc("/py/acc", osc_acc, force=True)
            
            # Si modo multicanal, enviar también por canal
            if eeg_processing_mode == 'individual':
                for idx, ch_name in enumerate(EEG_CHANNELS):
                    ch_lower = ch_name.lower()
                    phase_offset = idx * 0.5
                    ch_env = [
                        0.1+((math.sin(0.22*t_sim+phase_offset)+1.0)/2.0)*(Z_MAX-0.2),
                        0.1+((math.sin(0.42*t_sim+1.7+phase_offset)+1.0)/2.0)*(Z_MAX-0.4),
                        0.1+((math.sin(0.62*t_sim+3.2+phase_offset)+1.0)/2.0)*(Z_MAX-0.5),
                        0.1+((math.sin(1.02*t_sim+4.7+phase_offset)+1.0)/2.0)*(Z_MAX-1.0),
                        0.1+((math.sin(1.52*t_sim+6.2+phase_offset)+1.0)/2.0)*(Z_MAX-1.5)
                    ]
                    ch_signed = [x * (1.0 if idx < 2 else -1.0) for x in ch_env]
                    send_proc(f"/py/{ch_lower}/bands_env", ch_env, force=True)
                    send_proc(f"/py/{ch_lower}/bands_signed_env", ch_signed, force=True)
                    send_proc(f"/py/{ch_lower}/bands_raw", [round(x*1.5, 3) for x in ch_env], force=True)
            # 6. Imprimir estado
            refresh(line_post())
            # 7. Incrementar tiempo y esperar
            t_sim += PERIOD; time_spent = time.time() - row_start_time; time.sleep(max(0, PERIOD - time_spent))
        except Exception as e: print(f"\n!!! Error en simulation_loop: {e}"); time.sleep(1)
# ---------------------------

# --- Logs, Servidor OSC, Timers ---
logging.getLogger('pythonosc').setLevel(logging.ERROR)

# Handler genérico para capturar TODOS los mensajes OSC (para debugging)
def catch_all_osc(unused_addr, *args):
    """Captura todos los mensajes OSC para debugging"""
    if debug_mode:
        print(f"[OSC RECEIVED] {unused_addr}: {args}")

disp = Dispatcher()

# Mapear catch-all primero
disp.set_default_handler(catch_all_osc)

if not is_simulation:
    if use_eeg:
        print(f"[OSC] ✓ Mapeando /desdemuse/eeg → muse_eeg()")
        disp.map("/desdemuse/eeg", muse_eeg)
    if use_acc:
        print(f"[OSC] ✓ Mapeando /desdemuse/acc → muse_acc()")
        disp.map("/desdemuse/acc", muse_acc)
    if use_ppg:
        print(f"[OSC] ✓ Mapeando /desdemuse/ppg → muse_ppg()")
        disp.map("/desdemuse/ppg", muse_ppg)
    if use_gyro:
        print(f"[OSC] ✓ Mapeando /desdemuse/gyro → muse_gyro()")
        disp.map("/desdemuse/gyro", muse_gyro)
    if use_jaw:
        print(f"[OSC] ✓ Mapeando /desdemuse/jaw → muse_jaw()")
        disp.map("/desdemuse/jaw", muse_jaw)
else:
    print(f"[OSC] Modo simulación - no se esperan datos reales")

if needs_baseline_calibration:
    print(f"► Iniciando baseline ({BASE_SEC}s).")
elif not is_simulation:
    print("► No se requiere baseline.")

if not is_simulation:
    # Baselines se controlan vía contadores (frames_left, frames_left_acc)
    # en muse_eeg() y muse_acc(), no mediante timers (más preciso)
    pass
# --------------------------------

# --- Lanzar Loops ---
threads_active = True
midi_thread = None; serial_thread = None
if any(sig in MIDI_OUT and not MIDI_OUT[sig].name.startswith("fake_") for sig in TARGET_CC): midi_thread = threading.Thread(target=midi_tick, daemon=True); midi_thread.start()
else: print("⚠️ No MIDI activo.")
if not is_simulation and any((use_myo, use_plant1, use_plant2, use_temp_hum, use_dist)): serial_thread = threading.Thread(target=serial_loop, daemon=True); serial_thread.start()
elif not is_simulation: print("⚠️ No Arduino activo.")

# Iniciar listener de atajos (Ctrl+B)
listener_thread = threading.Thread(target=listen_shortcuts, daemon=True)
listener_thread.start()

muse_selected = not is_simulation and (use_eeg or use_acc)
arduino_selected = not is_simulation and any((use_myo, use_plant1, use_plant2, use_temp_hum, use_dist))

print("\n--- Estado de Ejecución ---")
if is_simulation: print("Modo: SIMULACIÓN")
else: print(f"Modo: REAL (Muse: {muse_selected}, Arduino: {arduino_selected})")

server = None
main_loop_running = True
try:
    # Instrucciones de baseline si se va a usar EEG
    if use_eeg and not is_simulation:
        print("\n" + "="*60)
        print("⚙️  CALIBRACIÓN INICIAL DE ESTADO MENTAL")
        print("="*60)
        print(f"Duración: {BASE_SEC} segundos")
        print("\n📋 INSTRUCCIONES:")
        print("1. Asegúrate de que Muse está conectado y transmitiendo")
        print("2. Siéntate cómodamente en tu estado NEUTRAL/BASE")
        print("3. Mantén la cabeza quieta durante toda la calibración")
        print("4. No pienses en nada específico, simplemente RELÁJATE")
        print("\nEsta medición determinará tu estado mental inicial (baseline)")
        print("y permitirá el sistema ajustarse a TI.")
        print("="*60 + "\n")
    
    input("Presiona Enter para iniciar bucle principal...")

    if is_simulation:
        print("Entrando a simulation_loop...")
        simulation_loop()
    elif muse_selected:
        print("Iniciando servidor OSC...")
        print(f"[OSC] Escuchando en 0.0.0.0:{OSC_PORT}")
        print(f"[OSC] IMPORTANTE: Configura la app Muse para enviar a {MY_LOCAL_IP}:{OSC_PORT}")
        try:
            server = BlockingOSCUDPServer(("0.0.0.0", OSC_PORT), disp)
            print(f"[OSC] ✓ Servidor OSC iniciado correctamente")
            print(f"[OSC] Esperando datos de Muse...")
        except OSError as e:
            print(f"[OSC] ✗ Error al abrir puerto {OSC_PORT}: {e}")
            main_loop_running = False
            raise
        except Exception as e:
            safe_print(f"[OSC] ✗ Error inesperado: {e}")
            main_loop_running = False
            raise
        
        safe_print("Entrando a bucle OSC...")
        if use_eeg and not baseline_eeg_done:
            safe_print(f"\n🔄 INICIANDO CALIBRACIÓN ({BASE_SEC}s)...")
            safe_print("   Mantén una postura relajada y neutral\n")
        
        # Inicializar grabador de datos si está habilitado
        data_recorder = None
        baseline_metadata_written = False  # Guard para escribir metadatos solo una vez
        if save_data:
            data_recorder = DataRecorder()
            data_recorder.start()
        
        server.timeout = 0.05  # Timeout muy corto para responder rápido a Ctrl+C
        baseline_time = time.time()  # Marca el tiempo de inicio del baseline
        
        while main_loop_running:
            try:
                server.handle_request()
                
                # Escribir metadatos del baseline apenas se completa (una sola vez)
                if data_recorder and baseline_done and not baseline_metadata_written:
                    data_recorder.write_baseline_metadata()
                    baseline_metadata_written = True
                
                # Grabar datos si está habilitado y baseline está completo
                if data_recorder and baseline_done:
                    elapsed = time.time() - baseline_time
                    data_recorder.write_data(elapsed)
                    
            except KeyboardInterrupt:
                safe_print("\n\n✋ Ctrl+C detectado. Cerrando...")
                main_loop_running = False
                break
            except Exception as e:
                if main_loop_running:
                    safe_print(f"[OSC] Error: {e}")
                    time.sleep(0.1)
    
    elif arduino_selected:
        safe_print("Solo Arduino. Ctrl+C para salir.")
        while main_loop_running:
            try:
                time.sleep(0.5)
            except KeyboardInterrupt:
                safe_print("\n✋ Ctrl+C detectado. Cerrando...")
                main_loop_running = False
                break
    else:
        safe_print("No se seleccionaron sensores activos.")
        main_loop_running = False

except KeyboardInterrupt:
    safe_print("\n✋ Ctrl+C detectado. Saliendo...")
    main_loop_running = False
except Exception as e:
    safe_print(f"\n!!! ERROR: {e}")
    import traceback
    traceback.print_exc()
    main_loop_running = False

finally:
    threads_active = False
    main_loop_running = False
    safe_print("\nIniciando cierre...")
    
    # Cerrar grabador de datos si está activo
    if 'data_recorder' in locals() and data_recorder is not None:
        data_recorder.close()
    
    time.sleep(0.1)
    
    # Cerrar servidor OSC con timeout
    if server is not None:
        print("Cerrando servidor OSC...")
        try:
            # server.shutdown() puede bloquear; usar timeout
            server.timeout = 0.01
            server.shutdown()
            server.server_close()
            print("  ✓ Servidor OSC cerrado")
        except Exception as e:
            try:
                server.server_close()
            except:
                pass
            print(f"  ⚠️ Error al cerrar OSC (ignorado): {e}")
    
    # Dar tiempo a hilos daemon para limpiarse
    print("Esperando cierre de hilos...")
    time.sleep(0.2)
    
    print("\n✅ Programa finalizado correctamente.")
    sys.exit(0)
# --- FIN Lanzar Loops ---