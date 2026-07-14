import json
import os

def analyze_har(file_path):
    print(f"[*] Analizzando il file HAR: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
        
    entries = har_data.get('log', {}).get('entries', [])
    print(f"[*] Trovate {len(entries)} richieste di rete.\n")
    
    interesting_urls = []
    
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        
        # Filtriamo le richieste interessanti
        if '.xml' in url or '.json' in url or 'api' in url or 'pages' in url or 'componenti' in url:
            
            content = response.get('content', {})
            text = content.get('text', '')
            mime = content.get('mimeType', '')
            
            if text and len(text) > 50 and ('json' in mime or 'xml' in mime or 'text' in mime):
                interesting_urls.append((url, mime, text))

    print(f"[*] Filtrate {len(interesting_urls)} richieste rilevanti.\n")
    
    # Raggruppiamo e stampiamo
    for url, mime, text in interesting_urls:
        if 'css' in mime or 'svg' in url or 'js' in mime:
            continue # skip css/js/svg
            
        print(f"=== URL: {url} ===")
        print(f"MIME: {mime}")
        
        # Se è JSON, proviamo a stamparne la struttura (le chiavi)
        if text.startswith('{') or text.startswith('['):
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    print("JSON Keys:", list(data.keys()))
                elif isinstance(data, list) and len(data) > 0:
                    print("JSON Array of", type(data[0]))
            except:
                pass
                
        preview = text[:800].replace('\n', ' ')
        print(f"Preview: {preview}...\n")

if __name__ == "__main__":
    analyze_har('editor.flazio.com.har')
