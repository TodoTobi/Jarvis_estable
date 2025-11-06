# stt_groq.py
import os
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from groq import Groq

# =======================
# CONFIG
# =======================
SAMPLE_RATE = 16000  # 16kHz, lo que usa whisper
DURATION_DEFAULT = 5  # segundos

# podés tomarla desde un config.py o directamente del entorno
try:
    from config import GROQ_API_KEY  # si tenés un config.py
except ImportError:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("Falta GROQ_API_KEY. Definila en config.py o en las variables de entorno.")

client = Groq(api_key=GROQ_API_KEY)


# =======================
# GRABAR DEL MIC
# =======================
def grabar_audio(segundos: int = DURATION_DEFAULT, archivo: str = "input.wav") -> str:
    """
    Graba audio del micrófono en mono a 16 kHz y lo guarda como WAV.
    """
    print(f"[STT] Grabando {segundos}s...")
    audio = sd.rec(int(segundos * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()

    # sounddevice devuelve float32 -1..1. Lo pasamos a int16 para wav "clásico"
    audio_int16 = np.int16(audio * 32767)

    write(archivo, SAMPLE_RATE, audio_int16)
    print(f"[STT] Grabación lista: {archivo}")
    return archivo


# =======================
# ENVIAR A GROQ
# =======================
def audio_a_texto(archivo: str = "input.wav") -> str:
    """
    Envía el archivo de audio a Groq (modelo whisper-large-v3-turbo) y devuelve el texto.
    """
    if not os.path.exists(archivo):
        raise FileNotFoundError(f"No existe el archivo de audio: {archivo}")

    with open(archivo, "rb") as f:
        try:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(archivo), f.read()),
                model="whisper-large-v3-turbo",
                temperature=0,
                response_format="json",
            )
        except Exception as e:
            raise RuntimeError(f"[STT] Error llamando a Groq: {e}")

    # el SDK suele dar .text
    text = getattr(transcription, "text", "") or transcription.get("text", "")
    print(f"[STT] Texto detectado: {text!r}")
    return text


# =======================
# PRUEBA RÁPIDA
# =======================
if __name__ == "__main__":
    wav_path = grabar_audio(5, "input.wav")
    texto = audio_a_texto(wav_path)
    print("Resultado final:", texto)
