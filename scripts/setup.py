#!/usr/bin/env python3
"""
Script de configuración e instalación para Integrado Omnicanal
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Imprimir banner de bienvenida"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🚀 INTEGRADO OMNICANAL - SISTEMA MULTIAGENTE             ║
║                                                              ║
║    Configuración e Instalación Automática                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """Verificar versión de Python"""
    print("🐍 Verificando versión de Python...")
    
    if sys.version_info < (3, 10):
        print("❌ Error: Se requiere Python 3.10 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_uv_installation():
    """Verificar e instalar UV si es necesario"""
    print("📦 Verificando instalación de UV...")
    
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ UV instalado: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("📥 Instalando UV...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv'], check=True)
        print("✅ UV instalado correctamente")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error instalando UV")
        return False

def install_dependencies():
    """Instalar dependencias del proyecto"""
    print("📦 Instalando dependencias...")
    
    try:
        # Instalar crewAI y dependencias
        subprocess.run(['crewai', 'install'], check=True)
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def setup_environment():
    """Configurar archivo de entorno"""
    print("⚙️  Configurando archivo de entorno...")
    
    project_root = Path(__file__).parent.parent
    env_example = project_root / "env.example"
    env_file = project_root / ".env"
    
    if env_file.exists():
        print("⚠️  Archivo .env ya existe")
        response = input("¿Deseas sobrescribirlo? (y/N): ")
        if response.lower() != 'y':
            print("📝 Manteniendo archivo .env existente")
            return True
    
    if env_example.exists():
        shutil.copy2(env_example, env_file)
        print("✅ Archivo .env creado desde env.example")
        print("📝 Por favor, edita el archivo .env con tus credenciales")
        return True
    else:
        print("❌ Archivo env.example no encontrado")
        return False

def create_directories():
    """Crear directorios necesarios"""
    print("📁 Creando directorios necesarios...")
    
    directories = [
        "temp_audio",
        "logs", 
        "data",
        "ssl"
    ]
    
    project_root = Path(__file__).parent.parent
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Directorio creado: {directory}")
    
    return True

def initialize_database():
    """Inicializar base de datos"""
    print("🗄️  Inicializando base de datos...")
    
    try:
        project_root = Path(__file__).parent.parent
        src_path = project_root / "src"
        sys.path.insert(0, str(src_path))
        
        from integrado.database.database import create_tables
        create_tables()
        print("✅ Base de datos inicializada")
        return True
    except Exception as e:
        print(f"⚠️  Error inicializando base de datos: {e}")
        print("   La base de datos se creará automáticamente al iniciar el servidor")
        return True

def test_installation():
    """Probar instalación"""
    print("🧪 Probando instalación...")
    
    try:
        project_root = Path(__file__).parent.parent
        src_path = project_root / "src"
        sys.path.insert(0, str(src_path))
        
        from integrado.crew import Integrado
        crew = Integrado()
        print("✅ Crew inicializado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en prueba de instalación: {e}")
        return False

def show_next_steps():
    """Mostrar próximos pasos"""
    print("""
🎉 ¡Instalación completada!

📋 Próximos pasos:

1. 📝 Configurar credenciales:
   - Edita el archivo .env con tus API keys
   - Configura al menos OPENAI_API_KEY

2. 🚀 Iniciar servidor:
   python scripts/start_server.py

3. 🧪 Probar sistema:
   python examples/example_usage.py

4. 📚 Documentación:
   - README.md: Guía completa
   - docs/architecture.md: Arquitectura del sistema

5. 🌐 Acceder a la API:
   - Servidor: http://localhost:8000
   - Documentación: http://localhost:8000/docs

🔧 Comandos útiles:
   - crewai run          # Iniciar con crewAI CLI
   - docker-compose up   # Iniciar con Docker
   - crewai test 10 gpt-4 # Ejecutar tests

📞 Soporte:
   - GitHub Issues: Para reportar bugs
   - Discord: Comunidad CrewAI
   - Documentación: docs.crewai.com
    """)

def main():
    """Función principal de configuración"""
    print_banner()
    
    steps = [
        ("Verificar Python", check_python_version),
        ("Instalar UV", check_uv_installation),
        ("Instalar dependencias", install_dependencies),
        ("Configurar entorno", setup_environment),
        ("Crear directorios", create_directories),
        ("Inicializar base de datos", initialize_database),
        ("Probar instalación", test_installation)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"🔄 {step_name}")
        print('='*60)
        
        if not step_func():
            failed_steps.append(step_name)
            print(f"❌ Falló: {step_name}")
        else:
            print(f"✅ Completado: {step_name}")
    
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE INSTALACIÓN")
    print('='*60)
    
    if failed_steps:
        print(f"❌ Pasos fallidos: {len(failed_steps)}")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n⚠️  Algunos pasos fallaron. Revisa los errores anteriores.")
    else:
        print("✅ Todos los pasos completados exitosamente!")
    
    show_next_steps()

if __name__ == "__main__":
    main()






