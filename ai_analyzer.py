# pyrefly: ignore [missing-import]
from google import genai
import os
import time
import PIL.Image

def init_genai():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def call_gemini_with_retry(client, model_name, contents):
    max_retries = 6
    base_delay = 25
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "Quota" in err_str or "403" in err_str:
                if attempt < max_retries - 1:
                    print(f"    - [AI] Quota API superata (Rate Limit). Attendo {base_delay} secondi prima di riprovare (tentativo {attempt+1}/{max_retries})...")
                    time.sleep(base_delay)
                    base_delay *= 2  # Exponential backoff
                else:
                    raise e
            else:
                raise e

def analyze_visual_regression(orig_img_path, imp_img_path, diff_percent):
    client = init_genai()
    if not client:
        return "⚠️ Errore: API Key di Gemini non configurata. Salto analisi visiva."

    try:
        orig_img = PIL.Image.open(orig_img_path)
        imp_img = PIL.Image.open(imp_img_path)
    except Exception as e:
        return f"Errore nel caricamento delle immagini per l'analisi AI: {str(e)}"

    prompt = f"""
Sei un esperto di UX/UI e QA Automation. Sto confrontando due versioni dello stesso sito web.
L'immagine 1 è il sito originale. L'immagine 2 è il sito importato sulla nuova piattaforma.
Uno script matematico ha già rilevato una differenza visiva del {diff_percent:.1f}%.
Analizza attentamente entrambe le immagini e spiegami A PAROLE cosa è cambiato visivamente (es. elementi disallineati, colori sbagliati, font diversi, sezioni mancanti o tagliate, navbar diversa).
Sii conciso e diretto, elencando i problemi principali con dei bullet point. Evita introduzioni lunghe.
"""
    try:
        response = call_gemini_with_retry(client, 'gemini-3.5-flash', [prompt, orig_img, imp_img])
        return response.text.strip()
    except Exception as e:
        err_str = str(e).split("metadata {")[0].strip()
        return f"Errore durante l'analisi visiva AI: {err_str}"

def analyze_content_diff(orig_text, imp_text, path):
    client = init_genai()
    if not client:
        return "⚠️ Errore: API Key di Gemini non configurata."
        
    if not orig_text.strip():
        return "Nessun testo originale presente per questa pagina."

    prompt = f"""
Sei un revisore di siti web. Sto migrando la pagina "{path}".
Ecco il testo estratto dalla pagina originale:
---
{orig_text[:5000]} # Limitiamo per sicurezza sui token
---

Ecco il testo estratto dalla pagina importata:
---
{imp_text[:5000]}
---

Uno script ha rilevato che gran parte del testo è andata persa o è molto diversa.
Dimmi QUALI INFORMAZIONI IMPORTANTI (es. prezzi, indirizzi, descrizioni servizi, contatti) sono andate perse o differiscono significativamente.
Sii molto breve (max 2-3 frasi) e vai dritto al punto.
"""
    try:
        response = call_gemini_with_retry(client, 'gemini-3.5-flash', prompt)
        return response.text.strip()
    except Exception as e:
        err_str = str(e).split("metadata {")[0].strip()
        return f"Errore durante l'analisi testuale AI: {err_str}"

def generate_executive_summary(errors_text):
    client = init_genai()
    if not client:
        return "⚠️ *Errore: API Key di Gemini non configurata. Sintesi AI disabilitata.*"

    prompt = f"""
Sei un QA Lead. Ho eseguito un audit automatico su un sito migrato e ho trovato i seguenti errori (strutturali, link rotti e visivi):
{errors_text[:15000]}

Scrivi un "Executive Summary" di massimo 5-6 righe in cui riassumi la situazione generale del sito. 
Indica se la migrazione è andata bene, male o ha problemi critici, e consiglia le prime 3 azioni prioritarie da compiere (es. "Correggere subito i link rotti nel menu", "Ripristinare i testi mancanti in homepage"). Usa il grassetto per evidenziare i concetti chiave. Usa un tono professionale ma diretto.
"""
    try:
        response = call_gemini_with_retry(client, 'gemini-3.5-flash', prompt)
        return response.text.strip()
    except Exception as e:
        err_str = str(e).split("metadata {")[0].strip()
        return f"Errore durante la sintesi AI: {err_str}"
