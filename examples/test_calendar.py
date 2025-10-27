#!/usr/bin/env python3
"""
Ejemplo específico para probar Google Calendar con Service Account
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_calendar_tools():
    """Probar herramientas de Calendar directamente"""
    
    print("🗓️  Probando Google Calendar con Service Account")
    print("=" * 60)
    
    # Verificar variables de entorno
    required_vars = [
        'GOOGLE_SERVICE_ACCOUNT_FILE',
        'CALENDAR_ID'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Variables de entorno faltantes:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Variables de entorno configuradas")
    
    try:
        from integrado.tools.calendar_service_account import CalendarTool, CalendarSearchTool
        
        # Probar búsqueda de eventos
        print("\n🔍 Buscando eventos existentes...")
        search_tool = CalendarSearchTool()
        result = search_tool._run()
        print(f"Resultado: {result}")
        
        # Crear evento de prueba
        print("\n📅 Creando evento de prueba...")
        calendar_tool = CalendarTool()
        
        # Crear fecha para mañana
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        result = calendar_tool._run(
            title="🧪 Prueba Sistema Integrado",
            description="Evento de prueba creado por el sistema Integrado Omnicanal",
            start_datetime=start_time.isoformat(),
            end_datetime=end_time.isoformat(),
            location="Oficina Virtual",
            timezone="America/Argentina/Buenos_Aires"
        )
        
        print(f"Resultado: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando Calendar: {e}")
        return False

def test_calendar_with_crew():
    """Probar Calendar a través del crew"""
    
    print("\n🤖 Probando Calendar a través del Crew")
    print("-" * 40)
    
    try:
        from integrado.crew import Integrado
        
        crew = Integrado()
        
        # Crear fecha para mañana
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        event_details = {
            'title': '🎯 Reunión Crew AI',
            'description': 'Reunión de prueba con el sistema multiagente',
            'start_datetime': start_time.isoformat(),
            'end_datetime': end_time.isoformat(),
            'location': 'Sala de reuniones virtual',
            'timezone': 'America/Argentina/Buenos_Aires'
        }
        
        result = crew.schedule_calendar_event(
            user_id="test_user_calendar",
            event_details=event_details
        )
        
        print(f"✅ Resultado del Crew: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error probando Calendar con Crew: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 PRUEBA DE GOOGLE CALENDAR - SISTEMA INTEGRADO")
    print("=" * 60)
    
    # Verificar archivo de credenciales
    cred_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', './credenciales.json')
    if not os.path.exists(cred_file):
        print(f"❌ Archivo de credenciales no encontrado: {cred_file}")
        print("📝 Asegúrate de que el archivo credenciales.json esté en el directorio raíz")
        return
    
    print(f"✅ Archivo de credenciales encontrado: {cred_file}")
    
    # Probar herramientas directamente
    tools_ok = test_calendar_tools()
    
    if tools_ok:
        # Probar con crew
        crew_ok = test_calendar_with_crew()
        
        if crew_ok:
            print("\n🎉 ¡Todas las pruebas de Calendar pasaron exitosamente!")
        else:
            print("\n⚠️  Las herramientas funcionan pero hay problemas con el crew")
    else:
        print("\n❌ Hay problemas con las herramientas de Calendar")
    
    print("\n📋 Para más información:")
    print("   - Revisa los logs de error arriba")
    print("   - Verifica que el CALENDAR_ID sea correcto")
    print("   - Asegúrate de que el Service Account tenga permisos")

if __name__ == "__main__":
    main()






