import json
import re

har_file = 'file_har/editor.flazio.com2.har'
components = set()

print(f"[*] Analizzando {har_file}...")

try:
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
        
    for entry in har_data.get('log', {}).get('entries', []):
        url = entry.get('request', {}).get('url', '')
        
        # Method 1: from component preview images in the store
        # e.g., https://static.globaluserfiles.com/componenti/plugins/StoreNew/img/componenti/anchor.jpg
        match = re.search(r'/componenti/plugins/StoreNew/img/componenti/([^/.]+)\.(jpg|png|svg|gif)', url)
        if match:
            components.add(match.group(1))
            
except Exception as e:
    print(f"[!] Errore: {e}")

# Save to file
components_list = sorted(list(components))
with open('componenti_flazio_trovati.txt', 'w') as f:
    f.write("=== COMPONENTI FLAZIO TROVATI ===\n\n")
    for c in components_list:
        f.write(f"- {c}\n")

print(f"[+] Trovati {len(components_list)} componenti unici!")
print("[+] Salvati nel file 'componenti_flazio_trovati.txt'.")
