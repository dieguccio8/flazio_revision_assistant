import argparse
import asyncio
import os
import urllib.parse
import urllib.request
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

def get_domain(url):
    return urllib.parse.urlparse(url).netloc

def get_path(url):
    parsed = urllib.parse.urlparse(url)
    return parsed.path if parsed.path else "/"

def normalize_url(base_url, link_href):
    return urllib.parse.urljoin(base_url, link_href)

async def crawl_site(page, start_url, max_pages=50):
    domain = get_domain(start_url)
    visited = set()
    queue = [start_url]
    site_data = {} # path -> data
    
    print(f"[*] Inizio discovery e crawling del dominio: {domain}")
    
    # 1. TENTATIVO LETTURA SITEMAP
    sitemap_url = urllib.parse.urljoin(start_url, "/sitemap.xml")
    try:
        print(f"    - Tentativo lettura sitemap: {sitemap_url}")
        
        # Usiamo urllib invece di Playwright per evitare che il browser blocchi i file XML come download
        req = urllib.request.Request(sitemap_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            sitemap_content = response.read().decode('utf-8')
            
        sitemap_soup = BeautifulSoup(sitemap_content, "html.parser")
        
        locs = sitemap_soup.find_all("loc")
            
        if locs:
            print(f"    - Trovati {len(locs)} URL nella sitemap!")
            for loc in locs:
                url_sitemap = loc.text.strip()
                if get_domain(url_sitemap) == domain and url_sitemap not in queue:
                    queue.append(url_sitemap)
    except Exception as e:
        print(f"    - Sitemap non trovata o illeggibile. Si procede col crawling standard.")
    
    while queue and len(visited) < max_pages:
        current_url = queue.pop(0)
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        print(f"    - Scraping pagina: {current_url}")
        
        try:
            # wait_until="load" è molto più stabile
            await page.goto(current_url, wait_until="load", timeout=30000)
            
            # Essenziale per Flazio: attendiamo che JavaScript costruisca la pagina prima di leggere l'HTML
            await page.wait_for_timeout(3000)
            
            # NON FACCIAMO PIU' SCREENSHOT -> Lo scraper ora è molto più veloce
            html_content = await page.content()
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract links and videos
            links = []
            videos = len(soup.find_all(['iframe', 'video', 'embed']))
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                
                # Supporto per i menu proprietari di Flazio (javascript:main.btnClickTesto('nomepagina$id'))
                if href.startswith("javascript:main.btnClickTesto"):
                    match = re.search(r"btnClickTesto\('([^'$]+)", href)
                    if match:
                        page_path = match.group(1)
                        full_link = urllib.parse.urljoin(current_url, f"/{page_path}")
                    else:
                        continue
                elif href.startswith("mailto:") or href.startswith("tel:") or href.startswith("javascript:"):
                    continue
                else:
                    full_link = normalize_url(current_url, href)
                    
                links.append(full_link)
                
                # Add to queue if it's same domain
                if get_domain(full_link) == domain and full_link not in visited and full_link not in queue:
                    # Skip assets
                    if not full_link.lower().endswith(('.pdf', '.jpg', '.png', '.zip', '.mp4')):
                        queue.append(full_link)
            
            # Extract text (pulizia aggressiva di script, stili e metadata invisibili)
            for element in soup(["script", "style", "noscript", "meta", "link", "head"]):
                element.extract()
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Se la pagina è completamente vuota o è un PDF (che Playwright talvolta prova a parsare prima del download)
            if len(text_content) < 5 and len(links) == 0:
                print(f"    - [Avviso] Pagina vuota o non testuale saltata: {current_url}")
                continue
            
            path = get_path(current_url)
            site_data[path] = {
                "url": current_url,
                "html": html_content,
                "links": links,
                "videos": videos,
                "text": text_content,
                "title": soup.title.string if soup.title else "Nessun Titolo"
            }
            
        except Exception as e:
            if "Download is starting" not in str(e):
                print(f"    [!] Errore nel caricamento di {current_url}: {e}")
            continue
            
    return site_data

def analyze_links(original_domain, imported_site_data):
    errors = []
    
    for path, data in imported_site_data.items():
        for link in data["links"]:
            link_domain = get_domain(link)
            # Se un link nel sito IMPORTATO punta al dominio ORIGINALE, è un errore grave (utente esce dal nuovo sito)
            if link_domain == original_domain:
                errors.append(f"| Pagina {path} | Errore Link (Cross-Domain) | Alta | Il link `{link}` punta ancora al vecchio dominio originale. Da correggere. |")
    return errors

def analyze_structure(original_site_data, imported_site_data):
    errors = []
    
    for path, orig_data in original_site_data.items():
        if path not in imported_site_data:
            errors.append(f"| Pagina {path} | Pagina Mancante | Alta | Questa pagina esiste nel sito originale ma NON è stata trovata nell'importato. |")
            continue
            
        imp_data = imported_site_data[path]
        
        # Check similarità lunghezza testo (heuristic check)
        orig_len = len(orig_data['text'])
        imp_len = len(imp_data['text'])
        
        if orig_len > 0:
            diff_ratio = (imp_len / orig_len) * 100
            if diff_ratio < 60:
                errors.append(f"| Pagina {path} | Testo Mancante | Media | Il sito importato ha molto meno testo ({imp_len} char) rispetto all'originale ({orig_len} char). Controlla se mancano sezioni. |")
                
        # Check Video
        orig_vid = orig_data.get('videos', 0)
        imp_vid = imp_data.get('videos', 0)
        if orig_vid > imp_vid:
            errors.append(f"| Pagina {path} | Video Mancanti | Alta | Trovati solo {imp_vid} video/iframe rispetto ai {orig_vid} dell'originale. |")

        # (Rimosso il controllo sul numero dei link perché Flazio usa <li> con Javascript invece di <a>,
        # generando falsi positivi nel confronto matematico)

    return errors

def generate_report(link_errors, structure_errors):
    total_errors = len(link_errors) + len(structure_errors)
    
    report = f"""# Report di QA Automation - Migrazione Flazio (Analisi Deterministica Potenziata)

## Sintesi Iniziale
- **Totale anomalie riscontrate**: {total_errors}
- *Nota: Questa analisi matematica confronta pagine, quantità di testi e destinazione dei link tra sito originale e importato.*

## Tabella Dettagliata delle Discrepanze

| Elemento | Tipo di Errore | Gravità | Dettaglio / Suggerimento di correzione |
|----------|----------------|---------|----------------------------------------|
"""
    
    if link_errors:
        report += "\n".join(link_errors) + "\n"
        
    if structure_errors:
        report += "\n".join(structure_errors) + "\n"
        
    if total_errors == 0:
        report += "| N/A | Nessun Errore | N/A | Non sono state trovate discrepanze strutturali o link rotti! |\n"
        
    report += """
## Azioni Correttive Prioritarie
- Risolvere tutti gli "Errori Link (Cross-Domain)" per evitare che gli utenti finiscano sul vecchio sito cliccando sui menu.
- Controllare le pagine segnalate come "Pagina Mancante" e importarle su Flazio.
- Verificare i testi segnalati come "Testo Mancante": potrebbero essersi persi dei paragrafi durante l'importazione.
"""
    return report

async def main():
    parser = argparse.ArgumentParser(description="Web QA Automation Script for Flazio Migrations (Deterministic Mode)")
    parser.add_argument("--original", required=False, help="URL della Home del sito originale")
    parser.add_argument("--imported", required=False, help="URL della Home del sito importato su Flazio")
    parser.add_argument("--max-pages", type=int, default=50, help="Numero massimo di pagine da scansionare (default: 50)")
    args = parser.parse_args()

    original_url = args.original
    if not original_url:
        print("-" * 60)
        original_url = input("🔗 Inserisci l'URL del Sito Originale (es. https://www.vecchiosito.it): ").strip()
        
    imported_url = args.imported
    if not imported_url:
        imported_url = input("🔗 Inserisci l'URL del Sito Importato su Flazio (es. https://nuovo.flazio.com): ").strip()
        print("-" * 60)

    if not original_url or not imported_url:
        print("[!] Errore: Entrambi i link sono obbligatori per avviare il confronto.")
        return

    print(f"\n[*] Inizio analisi comparativa STRUTTURALE (Senza AI)...")
    print(f"[*] Originale: {original_url}")
    print(f"[*] Importato: {imported_url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context() # Niente viewport fisso, non scattiamo foto
        page = await context.new_page()
        
        original_site_data = await crawl_site(page, original_url, max_pages=args.max_pages)
        imported_site_data = await crawl_site(page, imported_url, max_pages=args.max_pages)
        
        await browser.close()
        
    original_domain = get_domain(original_url)
    
    print("[*] Ricerca link rotti e riferimenti al vecchio dominio...")
    link_errors = analyze_links(original_domain, imported_site_data)
    
    print("[*] Analisi strutturale e confronto contenuti in corso...")
    structure_errors = analyze_structure(original_site_data, imported_site_data)
    
    print("[*] Generazione del report in corso...")
    report = generate_report(link_errors, structure_errors)
    
    # Usa il percorso assoluto della cartella dello script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Creazione della cartella results/<sito_originale>
    safe_domain_name = original_domain.replace("www.", "")
    output_dir = os.path.join(script_dir, "results", safe_domain_name)
    os.makedirs(output_dir, exist_ok=True)
    
    report_path = os.path.join(output_dir, "report_audit.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"[+] Analisi completata! Il report è stato salvato in: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
