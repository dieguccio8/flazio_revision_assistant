import os
import base64
import urllib.request
import time

os.makedirs("flazio_components_js", exist_ok=True)

# Read component names
with open('componenti_flazio_trovati.txt', 'r') as f:
    lines = f.readlines()

components = [line.strip().replace('- ', '') for line in lines if line.startswith('- ')]

print(f"[*] Avvio download forzato per {len(components)} componenti...")

success_count = 0
for component in components:
    encoded = base64.b64encode(component.encode('utf-8')).decode('utf-8').rstrip('=')
    js_url = f"https://flazio.org/componenti/cc/{encoded}.js"
    output_path = os.path.join("flazio_components_js", f"{component}.js")
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        success_count += 1
        continue
        
    try:
        req = urllib.request.Request(js_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read()
            if content:
                with open(output_path, 'wb') as out_f:
                    out_f.write(content)
                success_count += 1
        time.sleep(0.1) # Be nice to their servers
    except Exception as e:
        print(f"  [X] Impossibile scaricare {component} ({js_url}) - {e}")

print(f"\n[+] Scaricati con successo {success_count}/{len(components)} componenti!")
