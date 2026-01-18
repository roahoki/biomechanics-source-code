#!/usr/bin/env python3
"""
Script de diagnóstico: Detecta el formato de mensajes OSC de Muse
Muestra cuántos valores llegan en cada mensaje /desdemuse/eeg
"""

from pythonosc import dispatcher, osc_server
import time

message_count = 0
value_counts = {}

def handle_eeg(unused_addr, *vals):
    """Captura mensajes EEG y muestra formato"""
    global message_count, value_counts
    message_count += 1
    
    num_vals = len(vals)
    value_counts[num_vals] = value_counts.get(num_vals, 0) + 1
    
    # Mostrar primeros 10 mensajes completos
    if message_count <= 10:
        print(f"\n📨 Mensaje #{message_count}: {num_vals} valores")
        if num_vals <= 10:  # Solo mostrar valores si son pocos
            print(f"   Valores: {vals}")
    elif message_count == 11:
        print(f"\n... (siguientes mensajes se contarán silenciosamente)")
    
    # Cada 50 mensajes, mostrar resumen
    if message_count % 50 == 0:
        print(f"\n📊 Resumen después de {message_count} mensajes:")
        for num, count in sorted(value_counts.items()):
            pct = (count / message_count) * 100
            print(f"   {num} valores: {count} mensajes ({pct:.1f}%)")

def catch_all(addr, *vals):
    """Captura todos los demás mensajes OSC"""
    if addr != "/desdemuse/eeg":
        print(f"[OTRO] {addr}: {len(vals)} valores")

if __name__ == "__main__":
    print("="*60)
    print("🔍 DIAGNÓSTICO DE FORMATO MUSE")
    print("="*60)
    print("\n📋 Este script detectará:")
    print("   - Cuántos valores envía Muse por mensaje EEG")
    print("   - Si envía 1 valor (modo promedio)")
    print("   - Si envía 4 valores (modo multicanal)")
    print("\n⚙️ Configuración:")
    print("   Puerto: 5001")
    print("   Dirección: 0.0.0.0 (todas las interfaces)")
    print("\n⏳ Esperando datos de Muse...")
    print("   Presiona Ctrl+C cuando tengas suficiente información\n")
    
    disp = dispatcher.Dispatcher()
    disp.map("/desdemuse/eeg", handle_eeg)
    disp.set_default_handler(catch_all)
    
    server = osc_server.BlockingOSCUDPServer(("0.0.0.0", 5001), disp)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("📊 RESUMEN FINAL")
        print("="*60)
        print(f"\nTotal de mensajes EEG recibidos: {message_count}")
        
        if message_count > 0:
            print("\n📈 Distribución de valores por mensaje:")
            for num, count in sorted(value_counts.items()):
                pct = (count / message_count) * 100
                bar = "█" * int(pct / 5)
                print(f"   {num:4d} valores: {count:5d} mensajes ({pct:5.1f}%) {bar}")
            
            print("\n💡 INTERPRETACIÓN:")
            if 4 in value_counts and value_counts[4] > message_count * 0.8:
                print("   ✅ Muse está enviando 4 valores (MULTICANAL)")
                print("   → Cada mensaje contiene [TP9, AF7, AF8, TP10]")
                print("   → El script py-v26-multichannel.py debería funcionar correctamente")
            elif 1 in value_counts and value_counts[1] > message_count * 0.8:
                print("   ⚠️ Muse está enviando 1 valor (PROMEDIO)")
                print("   → Los 4 canales están siendo promediados")
                print("   → Necesitas configurar la app Muse para enviar canales separados")
                print("\n   📱 En la app Muse:")
                print("      - Settings → OSC Stream Target")
                print("      - Busca opción 'All Channels' o 'Individual Channels'")
            elif 256 in value_counts or 1024 in value_counts:
                print("   ℹ️ Muse está enviando paquetes grandes (256+ valores)")
                print("   → Posiblemente todos los samples de una ventana")
            else:
                print("   ❓ Formato inesperado detectado")
                print(f"   → Valores más comunes: {max(value_counts, key=value_counts.get)}")
        else:
            print("\n⚠️ No se recibieron mensajes EEG")
            print("\nVerifica:")
            print("   1. Muse está conectado y transmitiendo")
            print("   2. App Muse configurada para enviar a este IP:puerto")
            print("   3. Firewall no está bloqueando puerto 5001")
        
        print("\n" + "="*60)
        print("✅ Diagnóstico completado")
        print("="*60 + "\n")
