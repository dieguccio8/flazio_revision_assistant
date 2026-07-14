import json
import os

har_file = 'file_har/usersteviescreativearts.flazio.com.har'
os.makedirs("flazio_xml_data", exist_ok=True)

try:
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
        
    count = 0
    for entry in har_data.get('log', {}).get('entries', []):
        url = entry.get('request', {}).get('url', '')
        if '.xml' in url:
            # Flazio uses JSON syntax inside .xml extensions sometimes
            content = entry.get('response', {}).get('content', {}).get('text', '')
            if content:
                # Extract clean filename
                filename = url.split('/')[-1].split('?')[0]
                # Avoid duplicates
                output_path = os.path.join("flazio_xml_data", f"{count}_{filename}")
                with open(output_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(content)
                count += 1
                
    print(f"[+] Estratti {count} file XML di configurazione dal file HAR!")
except Exception as e:
    print(f"[!] Errore: {e}")
