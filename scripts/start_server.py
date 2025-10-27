#!/usr/bin/env python3
"""
Script para iniciar el servidor Integrado Omnicanal
"""

import os
import sys
import uvicorn
from pathlib import Path

# Agregar el directorio src al path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def check_environment():
    """Verificar configuración del entorno"""
    print("🔍 Verificando configuración del entorno...")
    
    # Verificar archivo .env
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  Archivo .env no encontrado")
        print("📋 Copia env.example a .env y configura tus credenciales:")
        print(f"   cp {project_root}/env.example {project_root}/.env")
        return False
    
    # Verificar variables críticas
    required_vars = ['OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Variables de entorno faltantes:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nConfigura estas variables en tu archivo .env")
        return False
    
    print("✅ Configuración del entorno verificada")
    return True

def initialize_database():
    """Inicializar base de datos"""
    print("🗄️  Inicializando base de datos...")
    
    try:
        from integrado.database.database import create_tables
        create_tables()
        print("✅ Base de datos inicializada")
        return True
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False

def start_server():
    """Iniciar servidor FastAPI"""
    print("🚀 Iniciando servidor Integrado Omnicanal...")
    
    # Configuración del servidor
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Servidor iniciado en: http://{host}:{port}")
    print(f"🔧 Modo debug: {'Activado' if debug else 'Desactivado'}")
    print("\n📚 Endpoints disponibles:")
    print("   - GET  /                    # Información de la API")
    print("   - GET  /health              # Health check")
    print("   - POST /api/message         # Procesar mensajes")
    print("   - POST /api/calendar/schedule # Programar eventos")
    print("   - POST /webhook/{channel}   # Webhooks")
    print("\n📖 Documentación automática:")
    print(f"   - Swagger UI: http://{host}:{port}/docs")
    print(f"   - ReDoc: http://{host}:{port}/redoc")
    print("\n" + "="*60)
    
    try:
        uvicorn.run(
            "integrado.main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")

def main():
    """Función principal"""
    print("🚀 Integrado Omnicanal - Sistema Multiagente")
    print("="*60)
    
    # Verificar entorno
    if not check_environment():
        print("\n❌ Configuración incompleta. Por favor, revisa los errores anteriores.")
        sys.exit(1)
    
    # Inicializar base de datos
    if not initialize_database():
        print("\n⚠️  Continuando sin base de datos...")
    
    # Iniciar servidor
    start_server()

if __name__ == "__main__":
    main()






