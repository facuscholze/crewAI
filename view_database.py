#!/usr/bin/env python3
"""
Script para ver el contenido de la base de datos
"""

import sqlite3
import os
from datetime import datetime

def view_database():
    """Ver el contenido de la base de datos"""
    
    db_path = "integrado_conversations.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    print("🗄️ CONTENIDO DE LA BASE DE DATOS")
    print("=" * 60)
    print(f"📁 Archivo: {os.path.abspath(db_path)}")
    print(f"📊 Tamaño: {os.path.getsize(db_path)} bytes")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ver tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("📋 TABLAS EN LA BASE DE DATOS:")
        for table in tables:
            print(f"   - {table[0]}")
        print()
        
        # Ver conversaciones
        if tables:
            print("💬 CONVERSACIONES ALMACENADAS:")
            print("-" * 40)
            
            for table_name in tables:
                if 'conversation' in table_name[0].lower():
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name[0]}")
                    count = cursor.fetchone()[0]
                    print(f"📊 Tabla {table_name[0]}: {count} registros")
                    
                    # Ver algunos registros
                    cursor.execute(f"SELECT * FROM {table_name[0]} LIMIT 3")
                    records = cursor.fetchall()
                    
                    if records:
                        print(f"📝 Primeros 3 registros:")
                        for i, record in enumerate(records, 1):
                            print(f"   {i}. {record}")
                        print()
        
        # Ver mensajes recientes
        try:
            cursor.execute("""
                SELECT session_id, message_type, content, timestamp 
                FROM conversations 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            recent_messages = cursor.fetchall()
            
            if recent_messages:
                print("📱 MENSAJES RECIENTES:")
                print("-" * 40)
                for msg in recent_messages:
                    session_id, msg_type, content, timestamp = msg
                    print(f"👤 {session_id} ({msg_type}): {content[:50]}...")
                    print(f"   ⏰ {timestamp}")
                    print()
        except Exception as e:
            print(f"⚠️ No se pudieron obtener mensajes recientes: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")

if __name__ == "__main__":
    view_database()




