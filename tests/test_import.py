import importlib
import traceback

try:
    importlib.import_module('integrado.crew')
    print("✅ import integrado.crew: OK")
except Exception:
    traceback.print_exc()