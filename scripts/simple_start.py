#!/usr/bin/env python3
"""
Script simple para iniciar el servidor Integrado
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Iniciar servidor de forma simple"""
    
    print("🚀 Iniciando Integrado Omnicanal...")
    
    # Agregar src al path
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))
    
    # Importar y ejecutar
    try:
        from integrado.main import app
        import uvicorn
        
        host = "0.0.0.0"
        port = 8000
        
        print(f"🌐 Servidor iniciado en: http://{host}:{port}")
        print(f"📚 Documentación: http://{host}:{port}/docs")
        print("🛑 Para detener, presiona Ctrl+C")
        
        # Ejecutar servidor
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n✅ Servidor detenido")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()






