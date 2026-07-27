import requests
import json
import base64
import time
import PIL.Image
from io import BytesIO

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llava"

def image_to_base64(image: PIL.Image.Image) -> str:
    buffered = BytesIO()
    if image.mode != 'RGB':
        image = image.convert('RGB')
        
    # Ottimizzazione 1: Riduciamo la risoluzione se è troppo grande per l'AI
    max_w = 1200
    if image.width > max_w:
        ratio = max_w / image.width
        new_size = (max_w, int(image.height * ratio))
        image = image.resize(new_size, PIL.Image.Resampling.LANCZOS)
        
    image.save(buffered, format="JPEG", quality=80)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def call_ollama(prompt, images=None):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    if images:
        payload["images"] = [image_to_base64(img) for img in images]
        
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return "⚠️ Errore: Impossibile connettersi a Ollama. Assicurati che Ollama sia avviato (esegui './ollama serve' o avvia l'app)."
    except Exception as e:
        return f"Errore durante la chiamata a Ollama: {str(e)}"

def analyze_visual_regression(orig_img_path, imp_img_path, diff_percent):
    try:
        orig_img = PIL.Image.open(orig_img_path)
        imp_img = PIL.Image.open(imp_img_path)
    except Exception as e:
        return f"Errore nel caricamento delle immagini per l'analisi AI: {str(e)}"

    CHUNK_HEIGHT = 3000 # Increased to reduce chunks, LlaVA can handle taller images since width is downscaled

    width1, height1 = orig_img.size
    width2, height2 = imp_img.size
    max_height = max(height1, height2)
    
    if max_height <= CHUNK_HEIGHT:
        prompt = f"""
Sei un esperto di UX/UI e QA Automation. Sto confrontando due versioni dello stesso sito web.
L'immagine 1 è il sito originale. L'immagine 2 è il sito importato sulla nuova piattaforma.
Uno script matematico ha già rilevato una differenza visiva del {diff_percent:.1f}%.
Analizza attentamente entrambe le immagini e spiegami A PAROLE cosa è cambiato visivamente (es. elementi disallineati, colori sbagliati, font diversi, sezioni mancanti o tagliate, navbar diversa).
ATTENZIONE IMPORTANTISSIMA: Sii estremamente preciso e non inventare problemi inesistenti (no allucinazioni). Verifica con molta cura se gli elementi che ti sembrano mancanti (es. box, icone, tasti) non siano in realtà presenti nell'immagine 2 ma semplicemente spostati o con uno stile/colore diverso. Dichiara che un elemento è mancante SOLO se sei assolutamente certo che non esista da nessuna parte nell'immagine 2.
Sii conciso e diretto, elencando i problemi principali con dei bullet point. Evita introduzioni lunghe.
"""
        return call_ollama(prompt, images=[orig_img, imp_img])

    # Se l'immagine è troppo lunga, la tagliamo in chunk
    num_chunks = (max_height // CHUNK_HEIGHT) + 1
    aggregated_feedback = []
    
    for i in range(num_chunks):
        y_start = i * CHUNK_HEIGHT
        y_end = min((i + 1) * CHUNK_HEIGHT, max_height)
        
        # Ritagliamo in modo sicuro
        c_orig = orig_img.crop((0, y_start, width1, min(y_end, height1))) if y_start < height1 else None
        c_imp = imp_img.crop((0, y_start, width2, min(y_end, height2))) if y_start < height2 else None
        
        if not c_orig and not c_imp:
            continue
            
        # Compensiamo altezze asimmetriche
        if not c_orig: c_orig = PIL.Image.new("RGB", (width1, y_end - y_start), (255, 255, 255))
        if not c_imp: c_imp = PIL.Image.new("RGB", (width2, y_end - y_start), (255, 255, 255))
        
        prompt = f"""
Sei un esperto di UX/UI e QA Automation. Stiamo analizzando la SEZIONE {i+1} di {num_chunks} di una pagina web molto lunga.
L'immagine 1 è la sezione originale. L'immagine 2 è la sezione importata.
Spiegami A PAROLE cosa è cambiato visivamente in QUESTA SEZIONE (es. elementi disallineati, testi tagliati).
ATTENZIONE IMPORTANTISSIMA: Non inventare problemi. Se la sezione appare vuota o corretta in entrambe le immagini, rispondi solo "NESSUN PROBLEMA".
Sii conciso e usa bullet point.
"""
        ans = call_ollama(prompt, images=[c_orig, c_imp])
        if ans and "NESSUN PROBLEMA" not in ans.upper():
            aggregated_feedback.append(f"**Sezione {i+1} (da pixel {y_start} a {y_end})**:\n{ans}")
            
    if not aggregated_feedback:
        return "Nessuna differenza visiva evidente trovata nei vari blocchi."
        
    return "\n\n".join(aggregated_feedback)

def analyze_content_diff(orig_text, imp_text, path):
    if not orig_text.strip():
        return "Nessun testo originale presente per questa pagina."

    prompt = f"""
Sei un revisore di siti web. Sto migrando la pagina "{path}".
Ecco il testo estratto dalla pagina originale:
---
{orig_text[:2000]}
---

Ecco il testo estratto dalla pagina importata:
---
{imp_text[:2000]}
---

Uno script ha rilevato che gran parte del testo è andata persa o è molto diversa.
Dimmi QUALI INFORMAZIONI IMPORTANTI (es. prezzi, indirizzi, descrizioni servizi, contatti) sono andate perse o differiscono significativamente.
Sii molto breve (max 2-3 frasi) e vai dritto al punto. Rispondi in italiano.
"""
    return call_ollama(prompt)

def generate_executive_summary(errors_text):
    prompt = f"""
Sei un QA Lead. Ho eseguito un audit automatico su un sito migrato e ho trovato i seguenti errori (strutturali, link rotti e visivi):
{errors_text[:4000]}

Scrivi un "Executive Summary" di massimo 5-6 righe in cui riassumi la situazione generale del sito. 
Indica se la migrazione è andata bene, male o ha problemi critici, e consiglia le prime 3 azioni prioritarie da compiere (es. "Correggere subito i link rotti nel menu", "Ripristinare i testi mancanti in homepage"). Usa il grassetto per evidenziare i concetti chiave. Usa un tono professionale ma diretto. Rispondi in italiano.
"""
    return call_ollama(prompt)
