#!/usr/bin/env python3
"""
Script para configurar ngrok y webhooks para Integrado Omnicanal
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

def print_banner():
    """Imprimir banner de ngrok"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🌐 INTEGRADO OMNICANAL - CONFIGURACIÓN NGROK             ║
║                                                              ║
║    Configuración de túnel público para webhooks             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_ngrok_installation():
    """Verificar si ngrok está instalado"""
    print("🔍 Verificando instalación de ngrok...")
    
    try:
        result = subprocess.run(['ngrok', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ngrok instalado: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ ngrok no está instalado")
    print("\n📥 Para instalar ngrok:")
    print("1. Ve a https://ngrok.com/download")
    print("2. Descarga ngrok para tu sistema operativo")
    print("3. Extrae el archivo y agrégalo a tu PATH")
    print("4. Crea una cuenta gratuita en https://ngrok.com")
    print("5. Obtén tu authtoken desde el dashboard")
    
    return False

def setup_ngrok_auth():
    """Configurar autenticación de ngrok"""
    print("\n🔐 Configurando autenticación de ngrok...")
    
    auth_token = input("Ingresa tu ngrok authtoken (o presiona Enter para saltar): ").strip()
    
    if auth_token:
        try:
            subprocess.run(['ngrok', 'config', 'add-authtoken', auth_token], check=True)
            print("✅ Authtoken configurado correctamente")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error configurando authtoken")
            return False
    else:
        print("⚠️ Saltando configuración de authtoken")
        return True

def start_ngrok_tunnel(port=8000):
    """Iniciar túnel ngrok"""
    print(f"\n🚀 Iniciando túnel ngrok en puerto {port}...")
    
    try:
        # Iniciar ngrok en segundo plano
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Esperar un momento para que ngrok se inicie
        time.sleep(3)
        
        # Obtener la URL pública
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            if response.status_code == 200:
                tunnels = response.json()['tunnels']
                if tunnels:
                    public_url = tunnels[0]['public_url']
                    print(f"✅ Túnel ngrok iniciado:")
                    print(f"🌐 URL pública: {public_url}")
                    return public_url, ngrok_process
        except Exception as e:
            print(f"⚠️ No se pudo obtener la URL automáticamente: {e}")
            print("🔍 Revisa http://localhost:4040 para ver la URL")
            return None, ngrok_process
            
    except Exception as e:
        print(f"❌ Error iniciando ngrok: {e}")
        return None, None

def update_env_file(public_url):
    """Actualizar archivo .env con la URL de ngrok"""
    print(f"\n📝 Actualizando archivo .env con URL: {public_url}")
    
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        # Crear .env desde env.example
        env_example = project_root / "env.example"
        if env_example.exists():
            import shutil
            shutil.copy2(env_example, env_file)
            print("✅ Archivo .env creado desde env.example")
        else:
            print("❌ Archivo env.example no encontrado")
            return False
    
    # Leer archivo .env
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Actualizar WEBHOOK_BASE_URL
    updated_content = content.replace(
        'WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io',
        f'WEBHOOK_BASE_URL={public_url}'
    )
    
    # Escribir archivo actualizado
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Archivo .env actualizado con URL de ngrok")
    return True

def show_webhook_urls(public_url):
    """Mostrar URLs de webhooks"""
    print(f"\n🔗 URLs de Webhooks configuradas:")
    print(f"📱 WhatsApp: {public_url}/webhook/whatsapp")
    print(f"💬 Messenger: {public_url}/webhook/messenger")
    print(f"📸 Instagram: {public_url}/webhook/instagram")
    print(f"📧 Gmail: {public_url}/webhook/gmail")
    print(f"\n🌐 API Base: {public_url}")
    print(f"📚 Documentación: {public_url}/docs")

def show_next_steps():
    """Mostrar próximos pasos"""
    print("""
🎉 ¡Configuración de ngrok completada!

📋 Próximos pasos:

1. 🚀 Iniciar el servidor Integrado:
   python scripts/start_server.py

2. 🔧 Configurar webhooks en las plataformas:
   - WhatsApp Business: Usar la URL /webhook/whatsapp
   - Facebook Messenger: Usar la URL /webhook/messenger
   - Instagram: Usar la URL /webhook/instagram

3. 🧪 Probar el sistema:
   python examples/example_usage.py

4. 📱 Enviar mensaje de prueba desde WhatsApp/Messenger

⚠️  IMPORTANTE:
- Mantén ngrok corriendo mientras uses el sistema
- La URL cambiará cada vez que reinicies ngrok (a menos que tengas cuenta premium)
- Para producción, usa un dominio propio con SSL

🔧 Comandos útiles:
   - ngrok http 8000    # Reiniciar túnel
   - http://localhost:4040  # Dashboard de ngrok
    """)

def main():
    """Función principal"""
    print_banner()
    
    # Verificar instalación de ngrok
    if not check_ngrok_installation():
        return
    
    # Configurar autenticación
    setup_ngrok_auth()
    
    # Obtener puerto del .env o usar 8000 por defecto
    port = 8000
    try:
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('PORT='):
                        port = int(line.split('=')[1].strip())
                        break
    except:
        pass
    
    # Iniciar túnel
    public_url, ngrok_process = start_ngrok_tunnel(port)
    
    if public_url:
        # Actualizar archivo .env
        update_env_file(public_url)
        
        # Mostrar URLs
        show_webhook_urls(public_url)
        
        print(f"\n⏳ ngrok corriendo en segundo plano (PID: {ngrok_process.pid})")
        print("🛑 Para detener ngrok, presiona Ctrl+C")
        
        try:
            # Mantener el script corriendo
            ngrok_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo ngrok...")
            ngrok_process.terminate()
            print("✅ ngrok detenido")
    
    show_next_steps()

if __name__ == "__main__":
    main()






