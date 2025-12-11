"""
Módulo para manejar las conexiones a la API de Facebook/Instagram con reintentos.
"""

import requests
from requests.adapters import HTTPAdapter, Retry
import time

def create_session():
    """
    Crear una sesión de requests con reintentos automáticos.
    """
    session = requests.Session()
    retries = Retry(
        total=5,  # número total de reintentos
        backoff_factor=1,  # factor para espera exponencial
        status_forcelist=[408, 429, 500, 502, 503, 504],  # códigos HTTP a reintentar
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def api_request(method, url, **kwargs):
    """
    Hacer una solicitud a la API con manejo de reintentos y errores.
    """
    session = create_session()
    
    # Establecer timeouts por defecto si no se especifican
    kwargs.setdefault('timeout', (5, 30))  # (connect timeout, read timeout)
    
    # Manejar reintentos manualmente para errores específicos
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                raise
            print(f"Timeout en intento {attempt + 1}/{max_retries}. Reintentando...")
            time.sleep(2 ** attempt)  # espera exponencial
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                raise
            print(f"Error de conexión en intento {attempt + 1}/{max_retries}. Reintentando...")
            time.sleep(2 ** attempt)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                if attempt == max_retries - 1:
                    raise
                retry_after = int(e.response.headers.get('Retry-After', 60))
                print(f"Rate limit alcanzado. Esperando {retry_after} segundos...")
                time.sleep(retry_after)
            else:
                raise

def get_request(url, **kwargs):
    """Helper para solicitudes GET."""
    return api_request('GET', url, **kwargs)

def post_request(url, **kwargs):
    """Helper para solicitudes POST."""
    return api_request('POST', url, **kwargs)