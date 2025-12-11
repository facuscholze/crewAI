import os
import sys
import shutil
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'integrado_conversations.db'
SRC_DIR = ROOT / 'src' / 'integrado'

# 0) Ensure workspace root is on sys.path so `src` imports work
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 1) Wipe conversation records via DB API
try:
    from src.integrado.database.mongodb_conversation import mongodb_conversation_db
    deleted = mongodb_conversation_db.delete_all()
    print(f"[DB] Conversaciones borradas vía API: {deleted}")
except Exception as e:
    print(f"[DB] No se pudo borrar vía API: {e}")

# 2) Remove SQLite DB file (fresh start)
try:
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[FS] Archivo DB eliminado: {DB_PATH}")
    else:
        print(f"[FS] Archivo DB no existe: {DB_PATH}")
except Exception as e:
    print(f"[FS] Error eliminando DB: {e}")

# 3) Remove __pycache__ folders across src/integrado
def remove_pycache(base: Path):
    for p in base.rglob('__pycache__'):
        try:
            shutil.rmtree(p)
            print(f"[FS] __pycache__ eliminado: {p}")
        except Exception as e:
            print(f"[FS] Error eliminando {p}: {e}")

remove_pycache(SRC_DIR)

# 4) Optional: clear temp/cache dirs if present
for candidate in ['.cache', '.rag_cache']:
    cpath = ROOT / candidate
    if cpath.exists():
        try:
            shutil.rmtree(cpath)
            print(f"[FS] Cache eliminado: {cpath}")
        except Exception as e:
            print(f"[FS] Error eliminando cache {cpath}: {e}")

print("✅ Cache y base de conversaciones limpiadas.")
