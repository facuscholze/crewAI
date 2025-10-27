# 🚀 Configuración de WhatsApp Business API

## ❌ Problema Actual
Error `131030`: "Recipient phone number not in allowed list"

Tu número `5493755629953` no está en la lista de destinatarios permitidos.

## ✅ Solución Paso a Paso

### 1. Acceder a Meta Business Manager
1. Ve a: https://business.facebook.com/
2. Inicia sesión con tu cuenta de Meta Business

### 2. Navegar a WhatsApp Business
1. En el menú lateral, busca **"WhatsApp"** o **"WhatsApp Business"**
2. Selecciona tu aplicación de WhatsApp Business

### 3. Configurar Números de Teléfono
1. Ve a **"Configuración"** o **"Settings"**
2. Busca la sección **"Números de teléfono"** o **"Phone Numbers"**
3. Selecciona tu número de WhatsApp Business: `15551649758`

### 4. Agregar a Lista de Destinatarios
1. Busca **"Lista de destinatarios"** o **"Recipients"**
2. Busca **"Destinatarios de prueba"** o **"Test Recipients"**
3. Haz clic en **"Agregar destinatario"** o **"Add Recipient"**
4. Ingresa tu número: `+5493755629953`
5. Haz clic en **"Agregar"** o **"Add"**

### 5. Verificar Estado
1. Confirma que tu número aparezca en la lista
2. El estado debe ser **"Activo"** o **"Active"**
3. Espera 5-10 minutos para que se active

## 🔍 Verificación

Después de agregar tu número, ejecuta:

```bash
python debug_whatsapp.py
```

Deberías ver:
```
✅ ÉXITO
📨 Message ID: wamid.xxx
```

## 📱 URLs de Configuración

- **Meta Business Manager**: https://business.facebook.com/
- **WhatsApp Business API**: https://developers.facebook.com/apps/
- **Tu App ID**: 710101288155256

## 🆘 Si No Funciona

1. **Verifica permisos**: Asegúrate de tener permisos de administrador en la app
2. **Modo desarrollo**: En desarrollo, solo funcionan números en la lista
3. **Tiempo de activación**: Puede tardar hasta 15 minutos
4. **Formato correcto**: Usa `+5493755629953` (con +)

## 🎯 Próximos Pasos

Una vez que funcione:
1. Reinicia el servidor: `python scripts/start_with_ngrok.py`
2. Envía un mensaje desde WhatsApp a tu bot
3. Verifica que recibas respuesta automática

---
**Fecha**: $(date)
**Estado**: Pendiente de configuración






