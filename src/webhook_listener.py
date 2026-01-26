from flask import Flask, request, json
import pprint  # Para imprimir bonito en la consola

app = Flask(__name__)

# --- ¡CONFIGURA ESTO! ---
# Inventa tu propio token. Debe ser idéntico al que pones en el panel de Meta.
VERIFY_TOKEN = "43833793"
# -------------------------


@app.route('/webhook', methods=['GET', 'POST'])  # type: ignore
def webhook():
    if request.method == 'GET':
        # --- Verificación del Webhook de Meta (Paso GET) ---
        print("Recibiendo solicitud de verificación GET de Meta...")
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            print("¡Token verificado exitosamente!")
            return request.args.get('hub.challenge'), 200
        else:
            print(f"¡ERROR! Token de verificación no coincide.")
            print(f"Recibí: {request.args.get('hub.verify_token')}")
            print(f"Esperaba: {VERIFY_TOKEN}")
            return "Error, token incorrecto", 403

    elif request.method == 'POST':
        # --- Recepción de Mensajes (Paso POST) ---
        print("\n--- ¡NUEVO MENSAJE RECIBIDO (POST)! ---")

        data = request.json
        pprint.pprint(data)  # Imprime todo el JSON

        try:
            # Extrae el ID del remitente (el IGSID que buscas)
            sender_id = data['entry'][0]['messaging'][0]['sender']['id']
            message_text = data['entry'][0]['messaging'][0]['message']['text']

            print(f"\n>>> ID del Remitente (IGSID): {sender_id}")
            print(f">>> Mensaje: {message_text}")
        except Exception:
            print("\n(Notificación recibida, pero no es un mensaje de texto.)")

        print("----------------------------------\n")
        return "OK", 200


if __name__ == '__main__':
    # El script corre en el puerto 8080
    print("Iniciando servidor 'escuchador' en http://localhost:8080/webhook")
    app.run(port=8080, debug=True)
