#!/usr/bin/env python3
"""
Herramienta de prueba para subir una canción a la API de tracks
"""
import requests
import base64
import json
import sys
import os

# Configuración
API_URL = os.getenv('HOST_PT', 'http://localhost:8083')
TRACK_ENDPOINT = f"{API_URL}/track/upload"

def encode_audio_file(file_path):
    """
    Lee un archivo de audio y lo convierte a base64
    """
    if not os.path.exists(file_path):
        print(f"Error: El archivo '{file_path}' no existe")
        return None
    
    try:
        with open(file_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            return audio_base64
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None

def upload_track(file_path, token=None):
    """
    Sube una canción a la API
    """
    print(f"📁 Leyendo archivo: {file_path}")
    audio_base64 = encode_audio_file(file_path)
    
    if not audio_base64:
        return None
    
    file_size_kb = len(audio_base64) / 1024
    print(f"✅ Archivo codificado en base64 ({file_size_kb:.2f} KB)")
    
    # Preparar el payload
    payload = {
        "track": audio_base64
    }
    
    # Preparar headers y cookies
    headers = {
        "Content-Type": "application/json"
    }
    
    cookies = {}
    if token:
        cookies['oversound_auth'] = token
    
    print(f"🚀 Enviando a {TRACK_ENDPOINT}...")
    
    try:
        response = requests.post(
            TRACK_ENDPOINT,
            json=payload,
            headers=headers,
            cookies=cookies
        )
        
        print(f"📡 Respuesta: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Track creado exitosamente!")
            print(f"   ID: {data.get('idtrack')}")
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Mensaje: {error_data}")
            except:
                print(f"   Respuesta: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor. ¿Está corriendo la API?")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def download_track(track_id, output_path, token=None):
    """
    Descarga una canción de la API
    """
    url = f"{TRACK_ENDPOINT}/{track_id}"
    print(f"📥 Descargando track ID {track_id} desde {url}...")
    
    cookies = {}
    if token:
        cookies['oversound_auth'] = token
    
    try:
        response = requests.get(url, cookies=cookies)
        
        if response.status_code == 200:
            data = response.json()
            track_base64 = data.get('track')
            
            if track_base64:
                # Decodificar base64 a bytes
                audio_bytes = base64.b64decode(track_base64)
                
                # Guardar en archivo
                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                
                file_size_kb = len(audio_bytes) / 1024
                print(f"✅ Track descargado: {output_path} ({file_size_kb:.2f} KB)")
                return True
            else:
                print("❌ Error: No se encontró el campo 'track' en la respuesta")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                print(f"   Mensaje: {response.json()}")
            except:
                print(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """
    Función principal
    """
    print("=" * 60)
    print("🎵 Herramienta de prueba para subir canciones")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUso:")
        print(f"  Subir:     python {sys.argv[0]} upload <archivo_audio> [token]")
        print(f"  Descargar: python {sys.argv[0]} download <track_id> <archivo_salida> [token]")
        print("\nEjemplo:")
        print(f"  python {sys.argv[0]} upload cancion.mp3")
        print(f"  python {sys.argv[0]} upload cancion.mp3 mi_token_auth")
        print(f"  python {sys.argv[0]} download 1 descargada.mp3")
        return
    
    command = sys.argv[1].lower()
    
    if command == "upload":
        if len(sys.argv) < 3:
            print("❌ Error: Debes especificar el archivo a subir")
            return
        
        file_path = sys.argv[2]
        token = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = upload_track(file_path, token)
        
        if result:
            print(f"\n✨ Para descargar este track:")
            print(f"   python {sys.argv[0]} download {result.get('idtrack')} cancion_descargada.mp3")
    
    elif command == "download":
        if len(sys.argv) < 4:
            print("❌ Error: Debes especificar el ID del track y el archivo de salida")
            return
        
        track_id = sys.argv[2]
        output_path = sys.argv[3]
        token = sys.argv[4] if len(sys.argv) > 4 else None
        
        download_track(track_id, output_path, token)
    
    else:
        print(f"❌ Comando desconocido: {command}")
        print("   Comandos disponibles: upload, download")

if __name__ == "__main__":
    main()
