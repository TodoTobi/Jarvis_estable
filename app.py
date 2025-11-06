# app.py
import os
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from groq import Groq
from brain_lmstudio import ask_brain
import actions_windows as actions

# Intentar obtener GROQ_API_KEY de config.py primero, luego de variables de entorno
try:
    from config import GROQ_API_KEY
except ImportError:
    GROQ_API_KEY = None

# Si no está en config.py, intentar desde variables de entorno
if not GROQ_API_KEY: 
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ejecutar_accion(parsed: dict) -> str:
    """Ejecuta una acción y devuelve un mensaje de confirmación."""
    action = parsed.get("action", "none")
    params = parsed.get("params", {})
    resultado = ""
    
    try:
        # ==================== OPERACIONES DE ARCHIVOS Y CARPETAS ====================
        if action == "crear_carpeta":
            ruta = params.get("ruta")
            if ruta:
                actions.crear_carpeta(ruta)
                resultado = f"✅ Carpeta creada: {ruta}"
            else:
                # Fallback: usar nombre y crear en escritorio
                nombre = params.get("nombre", "CarpetaIA")
                ruta = actions.crear_carpeta_en_escritorio(nombre)
                resultado = f"✅ Carpeta '{nombre}' creada en el escritorio."
        
        elif action == "listar_carpeta":
            ruta = params.get("ruta")
            filtro = params.get("filtro")
            items = actions.listar_carpeta(ruta, filtro)
            nombres = [item["nombre"] for item in items[:20]]  # Limitar a 20
            resultado = f"✅ Encontrados {len(items)} elementos:\n" + "\n".join(nombres)
            if len(items) > 20:
                resultado += f"\n... y {len(items) - 20} más"
        
        elif action == "leer_archivo":
            ruta = params.get("ruta")
            contenido = actions.leer_archivo(ruta)
            resultado = f"✅ Contenido de {ruta}:\n{contenido[:500]}"  # Limitar a 500 chars
            if len(contenido) > 500:
                resultado += "\n... (truncado)"
        
        elif action == "crear_txt":
            ruta = params.get("ruta")
            contenido = params.get("contenido", "")
            if ruta:
                actions.crear_txt(ruta, contenido)
                resultado = f"✅ Archivo creado: {ruta}"
            else:
                resultado = "❌ Error: falta la ruta del archivo."
        
        elif action == "editar_archivo":
            ruta = params.get("ruta")
            contenido = params.get("contenido", "")
            modo = params.get("modo", "sobrescribir")
            if ruta:
                actions.editar_archivo(ruta, contenido, modo)
                resultado = f"✅ Archivo editado: {ruta} (modo: {modo})"
            else:
                resultado = "❌ Error: falta la ruta del archivo."
        
        elif action == "copiar_archivo":
            origen = params.get("origen")
            destino = params.get("destino")
            if origen and destino:
                actions.copiar_archivo(origen, destino)
                resultado = f"✅ Copiado: {origen} → {destino}"
            else:
                resultado = "❌ Error: falta origen o destino."
        
        elif action == "mover_archivo":
            origen = params.get("origen")
            destino = params.get("destino")
            if origen and destino:
                actions.mover_archivo(origen, destino)
                resultado = f"✅ Movido: {origen} → {destino}"
            else:
                resultado = "❌ Error: falta origen o destino."
        
        elif action == "eliminar":
            ruta = params.get("ruta")
            permanente = params.get("permanente", False)
            if ruta:
                resultado = actions.eliminar(ruta, permanente)
                resultado = f"✅ {resultado}"
            else:
                resultado = "❌ Error: falta la ruta."
        
        elif action == "duplicar":
            ruta = params.get("ruta")
            nuevo_nombre = params.get("nuevo_nombre")
            if ruta:
                destino = actions.duplicar(ruta, nuevo_nombre)
                resultado = f"✅ Duplicado: {destino}"
            else:
                resultado = "❌ Error: falta la ruta."
        
        # ==================== CONTROL DE SISTEMA / APPS ====================
        elif action == "abrir_carpeta":
            ruta = params.get("ruta")
            if ruta:
                actions.abrir_carpeta(ruta)
                resultado = f"✅ Carpeta abierta: {ruta}"
            else:
                resultado = "❌ Error: falta la ruta de la carpeta."
        
        elif action == "abrir_app":
            nombre = params.get("nombre")
            if nombre:
                actions.abrir_app(nombre)
                resultado = f"✅ Aplicación '{nombre}' abierta."
            else:
                resultado = "❌ Error: falta el nombre de la aplicación."
        
        elif action == "cerrar_app":
            nombre = params.get("nombre")
            if nombre:
                actions.cerrar_app_por_nombre(nombre)
                resultado = f"✅ Aplicación '{nombre}' cerrada."
            else:
                resultado = "❌ Error: falta el nombre de la aplicación."
        
        elif action == "cerrar_ventana":
            actions.cerrar_ventana_activa()
            resultado = "✅ Ventana cerrada."
        
        elif action == "tomar_screenshot":
            ruta = params.get("ruta")
            ruta_guardada = actions.tomar_screenshot(ruta)
            resultado = f"✅ Screenshot guardado: {ruta_guardada}"
        
        # ==================== NAVEGADOR / WEB ====================
        elif action == "abrir_url":
            url = params.get("url")
            navegador = params.get("navegador")
            if url:
                actions.abrir_url(url, navegador=navegador)
                nav_text = f" en {navegador}" if navegador else ""
                resultado = f"✅ URL abierta{nav_text}: {url}"
            else:
                resultado = "❌ Error: falta la URL."
        
        elif action == "buscar_google":
            consulta = params.get("consulta")
            navegador = params.get("navegador")
            if consulta:
                actions.buscar_google(consulta)
                nav_text = f" en {navegador}" if navegador else ""
                resultado = f"✅ Buscando en Google{nav_text}: {consulta}"
            else:
                resultado = "❌ Error: falta la consulta."
        
        elif action == "buscar_youtube":
            consulta = params.get("consulta")
            navegador = params.get("navegador")
            if consulta:
                actions.buscar_youtube(consulta, navegador=navegador)
                nav_text = f" en {navegador}" if navegador else ""
                resultado = f"✅ Buscando en YouTube{nav_text}: {consulta}"
            else:
                resultado = "❌ Error: falta la consulta."
        
        elif action == "abrir_youtube_en_navegador":
            navegador = params.get("navegador")
            if navegador:
                actions.abrir_youtube_en_navegador(navegador)
                resultado = f"✅ YouTube abierto en {navegador}"
            else:
                resultado = "❌ Error: falta el nombre del navegador."
        
        # ==================== CONTROL DE PLATAFORMAS ====================
        elif action == "control_youtube":
            accion = params.get("accion")
            navegador = params.get("navegador")
            if accion:
                actions.control_youtube(accion, navegador)
                nav_text = f" en {navegador}" if navegador else ""
                resultado = f"✅ YouTube: {accion}{nav_text}"
            else:
                resultado = "❌ Error: falta la acción."
        
        elif action == "control_tiktok":
            accion = params.get("accion")
            navegador = params.get("navegador")
            if accion:
                actions.control_tiktok(accion, navegador)
                nav_text = f" en {navegador}" if navegador else ""
                resultado = f"✅ TikTok: {accion}{nav_text}"
            else:
                resultado = "❌ Error: falta la acción."
        
        elif action == "control_instagram":
            accion = params.get("accion")
            navegador = params.get("navegador")
            if accion:
                actions.control_instagram(accion, navegador)
                nav_text = f" en {navegador}" if navegador else ""
                resultado = f"✅ Instagram: {accion}{nav_text}"
            else:
                resultado = "❌ Error: falta la acción."
        
        # ==================== GOOGLE DOCS Y OFFICE ====================
        elif action == "crear_doc_google_docs":
            nombre = params.get("nombre")
            plantilla = params.get("plantilla")
            contenido = params.get("contenido")
            if nombre:
                resultado = actions.crear_doc_google_docs(nombre, plantilla, contenido)
            else:
                resultado = "❌ Error: falta el nombre del documento."
        
        elif action == "crear_docx":
            ruta = params.get("ruta")
            contenido = params.get("contenido", "")
            plantilla = params.get("plantilla")
            if ruta:
                ruta_creada = actions.crear_docx(ruta, contenido, plantilla)
                resultado = f"✅ Archivo DOCX creado: {ruta_creada}"
            else:
                resultado = "❌ Error: falta la ruta del archivo."
        
        elif action == "crear_ppt":
            ruta = params.get("ruta")
            titulo = params.get("titulo", "Presentación")
            plantilla = params.get("plantilla")
            if ruta:
                ruta_creada = actions.crear_ppt(ruta, titulo, plantilla)
                resultado = f"✅ Archivo PPT creado: {ruta_creada}"
            else:
                resultado = "❌ Error: falta la ruta del archivo."
        
        # ==================== INTEGRACIONES ====================
        elif action == "abrir_canva":
            actions.abrir_canva()
            resultado = "✅ Canva abierto"
        
        elif action == "abrir_gamma":
            actions.abrir_gamma()
            resultado = "✅ Gamma.app abierto"
        
        elif action == "control_spotify":
            accion = params.get("accion")
            if accion:
                actions.control_spotify(accion)
                resultado = f"✅ Spotify: {accion}"
            else:
                resultado = "❌ Error: falta la acción."
        
        elif action == "enviar_prompt_chatgpt":
            prompt = params.get("prompt")
            navegador = params.get("navegador")
            if prompt:
                actions.enviar_prompt_chatgpt(prompt, navegador)
                nav_text = f" en {navegador}" if navegador else ""
                resultado = f"✅ Prompt enviado a ChatGPT{nav_text}"
            else:
                resultado = "❌ Error: falta el prompt."
        
        elif action == "enviar_prompt_gemini":
            prompt = params.get("prompt")
            navegador = params.get("navegador")
            if prompt:
                actions.enviar_prompt_gemini(prompt, navegador)
                nav_text = f" en {navegador}" if navegador else ""
                resultado = f"✅ Prompt enviado a Gemini{nav_text}"
            else:
                resultado = "❌ Error: falta el prompt."
        
        elif action == "enviar_prompt_cursor":
            prompt = params.get("prompt")
            if prompt:
                actions.enviar_prompt_cursor(prompt)
                resultado = f"✅ Prompt enviado a Cursor"
            else:
                resultado = "❌ Error: falta el prompt."
        
        # ==================== ARCHIVOS AVANZADOS ====================
        elif action == "buscar_texto_en_archivos":
            ruta = params.get("ruta")
            texto = params.get("texto")
            extensiones = params.get("extensiones")
            if ruta and texto:
                resultados = actions.buscar_texto_en_archivos(ruta, texto, extensiones)
                if resultados:
                    resultado = f"✅ Encontrado '{texto}' en {len(resultados)} archivos:\n"
                    for r in resultados[:10]:
                        resultado += f"- {r['archivo']} (líneas: {r['lineas']})\n"
                    if len(resultados) > 10:
                        resultado += f"... y {len(resultados) - 10} archivos más"
                else:
                    resultado = f"✅ No se encontró '{texto}' en {ruta}"
            else:
                resultado = "❌ Error: falta ruta o texto a buscar."
        
        # ==================== DESARROLLO ====================
        elif action == "crear_proyecto":
            nombre = params.get("nombre")
            template = params.get("template", "basico")
            ruta = params.get("ruta")
            if nombre:
                ruta_creada = actions.crear_proyecto(nombre, template, ruta)
                resultado = f"✅ Proyecto '{nombre}' creado: {ruta_creada}"
            else:
                resultado = "❌ Error: falta el nombre del proyecto."
        
        elif action == "abrir_vscode":
            ruta = params.get("ruta")
            actions.abrir_vscode(ruta)
            resultado = f"✅ VSCode abierto{' en ' + ruta if ruta else ''}"
        
        elif action == "ejecutar_comando":
            comando = params.get("comando")
            directorio = params.get("directorio")
            if comando:
                output = actions.ejecutar_comando(comando, directorio)
                resultado = f"✅ Comando ejecutado:\n{output[:500]}"
                if len(output) > 500:
                    resultado += "\n... (truncado)"
            else:
                resultado = "❌ Error: falta el comando."
        
        # ==================== UTILIDADES ====================
        elif action == "listar_papelera":
            items = actions.listar_papelera()
            if items:
                resultado = f"✅ Papelera ({len(items)} archivos):\n"
                for item in items[:20]:
                    resultado += f"- {item['nombre']} ({item['fecha']})\n"
                if len(items) > 20:
                    resultado += f"... y {len(items) - 20} más"
            else:
                resultado = "✅ La papelera está vacía."
        
        elif action == "restaurar_desde_papelera":
            nombre_archivo = params.get("nombre_archivo")
            destino = params.get("destino")
            if nombre_archivo:
                ruta = actions.restaurar_desde_papelera(nombre_archivo, destino)
                resultado = f"✅ Archivo restaurado: {ruta}"
            else:
                resultado = "❌ Error: falta el nombre del archivo."
        
        # ==================== RESPUESTAS ====================
        elif action == "none":
            resultado = parsed.get("answer", "No entiendo qué quieres hacer.")
        
        else:
            resultado = f"❌ Acción desconocida: {action}"
        
        # Guardar log de la acción
        try:
            actions.guardar_log(action, params, resultado)
        except:
            pass  # No fallar si el logging tiene problemas
        
        return resultado
    
    except Exception as e:
        error_msg = f"❌ Error al ejecutar la acción: {str(e)}"
        try:
            actions.guardar_log(action, params, error_msg)
        except:
            pass
        return error_msg

@app.post("/chat")
def chat(message: str = Form(...), context: str = Form(None)):
    # Usar el brain para obtener la acción
    try:
        # Parsear contexto si existe
        conversation_context = []
        if context:
            try:
                conversation_context = json.loads(context)
            except:
                pass
        
        parsed = ask_brain(message, conversation_context)
        
        # Debug: mostrar qué se recibió (solo en desarrollo)
        # print(f"DEBUG - Parsed: {parsed}")
        
        # Verificar si hay múltiples acciones
        if "actions" in parsed and isinstance(parsed["actions"], list) and len(parsed["actions"]) > 0:
            # Ejecutar múltiples acciones secuencialmente
            resultados = []
            for i, accion in enumerate(parsed["actions"], 1):
                try:
                    resultado = ejecutar_accion(accion)
                    # Limpiar el resultado para evitar duplicar "✅"
                    if resultado.startswith("✅"):
                        resultado = resultado[1:].strip()
                    resultados.append(f"{i}. ✅ {resultado}")
                except Exception as e:
                    resultados.append(f"{i}. ❌ Error: {str(e)}")
            
            reply = "✅ Acciones completadas:\n\n" + "\n\n".join(resultados)
        elif "action" in parsed:
            # Ejecutar una sola acción
            if parsed["action"] == "none":
                # Es una respuesta del asistente, no una acción
                reply = parsed.get("answer", "No entiendo qué quieres hacer.")
            else:
                # Es una acción ejecutable
                reply = ejecutar_accion(parsed)
        else:
            # Si no tiene action ni actions, intentar mostrar el contenido
            if "answer" in parsed:
                reply = parsed["answer"]
            else:
                reply = f"❌ Formato de respuesta inválido del modelo.\n\nRecibido: {str(parsed)[:200]}"
        
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el mensaje: {e}")

@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    if not groq_client:
        raise HTTPException(
            status_code=500,
            detail="Falta GROQ_API_KEY. Hacé: set GROQ_API_KEY=TU_CLAVE y volvé a correr uvicorn",
        )

    audio_bytes = await file.read()
    filename = file.filename or "audio.webm"

    try:
        transcription = groq_client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3-turbo",
            temperature=0,
            response_format="json",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al llamar a Groq STT: {e}")

    text = getattr(transcription, "text", None) or transcription.get("text", "")
    return {"text": text}
