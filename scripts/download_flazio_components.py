import re
import base64
import urllib.request
import os
import glob

os.makedirs("flazio_components_js", exist_ok=True)
components_found = set()
har_files = glob.glob('file_har/*.har')

for har_file in har_files:
    print(f"[*] Analizzando {har_file}...")
    try:
        with open(har_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        urls = re.findall(r'flazio\.org/componenti/cc/([A-Za-z0-9+/=]+)\.js', content)
        for base64_part in urls:
            try:
                padded = base64_part + '=' * (-len(base64_part) % 4)
                decoded = base64.b64decode(padded).decode('utf-8')
                for c in decoded.split('|'):
                    if c: components_found.add(c)
            except Exception as e:
                pass
    except Exception as e:
        print(f"[!] Errore lettura HAR {har_file}: {e}")

print(f"\n[+] Trovati {len(components_found)} componenti unici!")

for component in components_found:
    print(f"    - Scaricando JS per: {component}...")
    encoded = base64.b64encode(component.encode('utf-8')).decode('utf-8').rstrip('=')
    js_url = f"https://flazio.org/componenti/cc/{encoded}.js"
    output_path = os.path.join("flazio_components_js", f"{component}.js")
    
    if os.path.exists(output_path):
        continue
        
    try:
        req = urllib.request.Request(js_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(output_path, 'w') as out_f:
                out_f.write(response.read().decode('utf-8'))
    except Exception as e:
        print(f"      [X] Errore download {component}: {e}")

print("\n[+] Download completato! I file sono nella cartella 'flazio_components_js'.")
