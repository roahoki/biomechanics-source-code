#!/usr/bin/env python3
"""
Script de Diagnóstico OSC - py-v26-multichannel
Verifica qué mensajes OSC se están enviando al puerto 5002
"""

import sys
import time
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

# Lista para rastrear mensajes recibidos
messages_received = {}
message_count = 0

def handle_all_messages(address, *args):
    """Captura todos los mensajes OSC"""
    global message_count
    message_count += 1
    
    if address not in messages_received:
        messages_received[address] = {
            'count': 0,
            'last_value': None,
            'first_seen': time.time()
        }
    
    messages_received[address]['count'] += 1
    messages_received[address]['last_value'] = args
    messages_received[address]['last_seen'] = time.time()

def print_summary():
    """Imprime resumen de mensajes recibidos"""
    print("\n" + "="*80)
    print(f"📊 RESUMEN DE MENSAJES OSC RECIBIDOS (Total: {message_count})")
    print("="*80)
    
    if not messages_received:
        print("❌ No se recibieron mensajes OSC")
        return
    
    # Agrupar por categoría
    categories = {
        'EEG': [],
        'ACC': [],
        'PPG': [],
        'BASELINE': [],
        'MULTICANAL': [],
        'OTROS': []
    }
    
    for address in sorted(messages_received.keys()):
        if 'bands' in address or 'eeg' in address:
            categories['EEG'].append(address)
        elif 'acc' in address:
            categories['ACC'].append(address)
        elif 'ppg' in address:
            categories['PPG'].append(address)
        elif 'baseline' in address:
            categories['BASELINE'].append(address)
        elif any(ch in address for ch in ['tp9', 'af7', 'af8', 'tp10']):
            categories['MULTICANAL'].append(address)
        else:
            categories['OTROS'].append(address)
    
    for category, addresses in categories.items():
        if addresses:
            print(f"\n🔹 {category}:")
            for addr in addresses:
                info = messages_received[addr]
                print(f"  ✓ {addr}")
                print(f"    - Recibido {info['count']} veces")
                print(f"    - Último valor: {info['last_value']}")
    
    print("\n" + "="*80)

def main():
    print("="*80)
    print("  🔍 DIAGNÓSTICO OSC - Escuchando en puerto 5002")
    print("="*80)
    print("\nEsperando mensajes OSC...")
    print("Presiona Ctrl+C para detener y ver resumen\n")
    
    dispatcher = Dispatcher()
    dispatcher.set_default_handler(handle_all_messages)
    
    server = BlockingOSCUDPServer(("127.0.0.1", 5002), dispatcher)
    
    try:
        while True:
            server.handle_request()
            
            # Mostrar contador cada 100 mensajes
            if message_count > 0 and message_count % 100 == 0:
                unique_addresses = len(messages_received)
                print(f"📨 {message_count} mensajes recibidos | {unique_addresses} rutas únicas")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Detenido por usuario")
        print_summary()

if __name__ == "__main__":
    main()
