#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar el escalamiento humano
Envía un mensaje de prueba al número de escalamiento configurado
"""

import os
import sys
import io
from pathlib import Path
from dotenv import load_dotenv

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Agregar src al path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

load_dotenv()

from integrado.tools.human_escalation_tool import HumanEscalationTool


def test_human_escalation():
    """Test de escalamiento humano"""
    
    print("TEST DE ESCALAMIENTO HUMANO")
    print("=" * 60)
    
    # Número de prueba (tu número)
    test_user_id = "5493755629953"  # Cambia esto por tu número si quieres
    test_message = "Mensaje de prueba del sistema de escalamiento humano"
    test_reason = "test_system"
    
    print(f"\nUsuario de prueba: {test_user_id}")
    print(f"Mensaje: {test_message}")
    print(f"Razon: {test_reason}")
    
    # Obtener número de escalamiento
    clinic_number = os.getenv('HUMAN_ESCALATION_NUMBER', '54375515585557')
    print(f"\nNumero de escalamiento: {clinic_number}")
    
    # Crear herramienta
    escalation_tool = HumanEscalationTool()
    
    print(f"\nEjecutando escalamiento...")
    print("-" * 60)
    
    try:
        result = escalation_tool._run(
            user_id=test_user_id,
            user_message=test_message,
            conversation_summary="Test de escalamiento humano desde script de prueba",
            reason=test_reason
        )
        
        print(f"\nRESULTADO:")
        print(result)
        print("\n" + "=" * 60)
        
        # Verificar si hay errores específicos de WhatsApp
        if "131030" in result or "not in allowed list" in result.lower():
            print("ADVERTENCIA: El numero no esta en la lista permitida (modo desarrollo)")
            print("SOLUCION: Agrega el numero 543755585557 a la lista de numeros permitidos")
            print("en tu cuenta de WhatsApp Business API (Meta Business Suite)")
            return False
        elif "131026" in result or "rate limit" in result.lower():
            print("ADVERTENCIA: Rate limit alcanzado, el mensaje se enviara mas tarde")
            return True
        elif "exitoso" in result.lower() or "enviada" in result.lower():
            print("TEST EXITOSO: El mensaje se envio correctamente")
            print("\nNOTA: Si no recibiste el mensaje, verifica:")
            print("1. Que el numero 543755585557 este en la lista permitida de WhatsApp Business API")
            print("2. Que el numero tenga WhatsApp activo")
            print("3. Revisa la consola de Meta Business Suite para ver el estado del mensaje")
            return True
        else:
            print("TEST CON ADVERTENCIAS: Revisa el resultado")
            return False
            
    except Exception as e:
        print(f"\nERROR EN EL TEST:")
        print(f"   {str(e)}")
        print("\n" + "=" * 60)
        return False


if __name__ == "__main__":
    success = test_human_escalation()
    sys.exit(0 if success else 1)

