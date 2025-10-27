#!/usr/bin/env python3
"""
Script para diagnosticar y reparar problemas con CrewAI
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n🔧 {description}")
    print(f"Ejecutando: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - ÉXITO")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"❌ {description} - ERROR")
            if result.stderr:
                print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False

def main():
    """Diagnostica y repara CrewAI"""
    print("🔍 DIAGNÓSTICO Y REPARACIÓN DE CREWAI")
    print("=" * 50)
    
    # Verificar versión actual
    run_command("pip show crewai", "Verificando versión actual de CrewAI")
    
    # Verificar dependencias
    run_command("pip list | grep -E '(crewai|langchain|openai)'", "Verificando dependencias relacionadas")
    
    # Limpiar cache de pip
    run_command("pip cache purge", "Limpiando cache de pip")
    
    # Reinstalar CrewAI
    print("\n🔄 REINSTALANDO CREWAI...")
    run_command("pip uninstall crewai -y", "Desinstalando CrewAI")
    run_command("pip install --upgrade --force-reinstall crewai", "Reinstalando CrewAI")
    
    # Verificar instalación
    run_command("pip show crewai", "Verificando nueva instalación")
    
    # Probar importación
    print("\n🧪 PROBANDO IMPORTACIÓN...")
    try:
        import crewai
        print(f"✅ CrewAI importado exitosamente - Versión: {crewai.__version__}")
    except Exception as e:
        print(f"❌ Error importando CrewAI: {e}")
    
    print("\n🎯 DIAGNÓSTICO COMPLETADO")
    print("Si aún hay problemas, intenta:")
    print("1. Recrear el entorno virtual")
    print("2. Usar start_server_direct.py en lugar de crewai train")

if __name__ == "__main__":
    main()



