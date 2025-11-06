# main.py
from brain_lmstudio import ask_brain
import actions_windows as actions
from stt_groq import grabar_audio, audio_a_texto

def ejecutar_accion(parsed: dict):
    action = parsed.get("action", "none")
    params = parsed.get("params", {})

    if action == "crear_carpeta":
        nombre = params.get("nombre", "CarpetaIA")
        actions.crear_carpeta_en_escritorio(nombre)

    elif action == "crear_txt":
        ruta = params.get("ruta")
        contenido = params.get("contenido", "")
        if ruta:
            actions.crear_txt(ruta, contenido)

    elif action == "abrir_carpeta":
        ruta = params.get("ruta")
        if ruta:
            actions.abrir_carpeta(ruta)

    elif action == "abrir_app":
        nombre = params.get("nombre")
        if nombre:
            actions.abrir_app(nombre)

    elif action == "abrir_url":
        url = params.get("url")
        if url:
            actions.abrir_url(url)

    elif action == "cerrar_app":
        nombre = params.get("nombre")
        if nombre:
            actions.cerrar_app_por_nombre(nombre)

    elif action == "cerrar_ventana":
        actions.cerrar_ventana_activa()

    else:
        # si el modelo quiso responder algo
        if "answer" in parsed:
            print("[IA]:", parsed["answer"])
        else:
            print("[Jarvis]: no hay accion para ejecutar.")

def main():
    print("Jarvis escuchando… Ctrl+C para salir.")
    while True:
        # 1. grabar voz
        audio_file = grabar_audio(segundos=5)
        texto = audio_a_texto(audio_file)
        if not texto:
            print("No se entendio.")
            continue

        print(f"[Usuario]: {texto}")

        # 2. pedirle al modelo que lo transforme en acción
        parsed = ask_brain(texto)
        print("[Modelo]:", parsed)

        # 3. ejecutar
        ejecutar_accion(parsed)

if __name__ == "__main__":
    main()
