import visual_analyzer
import os
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

import json

class FlazioInterceptor:
    def __init__(self):
        self.current_page = None
        self.intercepted_data = {}
        self.master_data = []

    async def handle_response(self, response):
        try:
            url = response.url
            if ".xml" in url and ("flazio.com" in url or "flazio.org" in url):
                if response.status == 200:
                    text = await response.text()
                    try:
                        data = json.loads(text)
                        if "masterPage" in url or "global" in url.lower():
                            self.master_data.append(data)
                        elif self.current_page:
                            if self.current_page not in self.intercepted_data:
                                self.intercepted_data[self.current_page] = []
                            self.intercepted_data[self.current_page].append(data)
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass


async def crawl_site(page, start_url, max_pages=50, is_flazio=False):
    domain = get_domain(start_url)
    visited = set()
    queue = [start_url]
    site_data = {} # path -> data
    
    interceptor = FlazioInterceptor()
    if is_flazio:
        page.on("response", interceptor.handle_response)
    
    print(f"[*] Inizio discovery e crawling del dominio: {domain}")
    
    # Crea cartelle screenshot
    import os
    safe_domain = domain.replace("www.", "")
    screenshot_dir = os.path.join("results", safe_domain, "screenshots", "flazio" if is_flazio else "original")
    os.makedirs(screenshot_dir, exist_ok=True)
    
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
        
        path = get_path(current_url)
        interceptor.current_page = path
        
        try:
            # wait_until="load" è molto più stabile
            await page.goto(current_url, wait_until="load", timeout=30000)
            
            if is_flazio:
                # Diamo tempo alle chiamate JSON di completarsi (2 secondi bastano, networkidle spesso si blocca su SPA)
                await page.wait_for_timeout(2000)
            else:
                # Per il sito classico aspettiamo il rendering
                await page.wait_for_timeout(3000)
            
            html_content = await page.content()
            
            # --- Graphical Analysis ---
            # 1. Screenshot
            safe_path = path.replace("/", "_")
            if not safe_path or safe_path == "_": safe_path = "_home"
            await page.screenshot(path=os.path.join(screenshot_dir, f"{safe_path}.png"), full_page=True)
            
            # 2. Design System
            design_system = {}
            try:
                design_system = await page.evaluate('''() => {
                    let fonts = new Set();
                    let colors = new Set();
                    let bgColors = new Set();
                    document.querySelectorAll('h1, h2, h3, p, button, a').forEach(el => {
                        let style = window.getComputedStyle(el);
                        if (style.fontFamily) fonts.add(style.fontFamily);
                        if (style.color && style.color !== 'rgba(0, 0, 0, 0)') colors.add(style.color);
                        if (style.backgroundColor && style.backgroundColor !== 'rgba(0, 0, 0, 0)') bgColors.add(style.backgroundColor);
                    });
                    return {
                        fonts: Array.from(fonts),
                        colors: Array.from(colors),
                        bgColors: Array.from(bgColors)
                    };
                }''')
            except Exception:
                pass
            # --------------------------
            
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract links
            links = []
            link_contexts = {}
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                
                # Supporto per i menu proprietari di Flazio
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
                
                # Add to queue se è stesso dominio
                if get_domain(full_link) == domain and full_link not in visited and full_link not in queue:
                    if not full_link.lower().endswith(('.pdf', '.jpg', '.png', '.zip', '.mp4')):
                        queue.append(full_link)
            
            if is_flazio:
                # Estrazione NATIVA dal JSON di Flazio intercettato
                videos = 0
                text_content = ""
                images_ratios = []
                
                def parse_component(comp):
                    nonlocal videos, text_content, links, images_ratios, link_contexts
                    t = comp.get("t", "")
                    if t in ["video", "youtube", "vimeo"]:
                        videos += 1
                    elif t in ["immagine", "galleria", "slider"]:
                        try:
                            w = float(comp.get("w", 0))
                            h = float(comp.get("h", 0))
                            if w > 10 and h > 10:
                                images_ratios.append({'w': w, 'h': h, 'ratio': round(w / h, 2)})
                        except (ValueError, TypeError):
                            pass
                    elif t == "testo":
                        # Flazio salva il testo in c_testo come HTML
                        html_text = comp.get("c_testo", "")
                        if html_text:
                            inner_soup = BeautifulSoup(html_text, "html.parser")
                            clean_text = inner_soup.get_text(separator=' ', strip=True)
                            text_content += clean_text + " "
                            
                            # Estrazione link dal testo
                            for a_tag in inner_soup.find_all("a", href=True):
                                href = a_tag["href"]
                                if not href.startswith(("mailto:", "tel:", "javascript:")):
                                    fl = normalize_url(current_url, href)
                                    
                                    # Create context from the text inside the link, or the surrounding text
                                    link_text = a_tag.get_text(strip=True)
                                    if not link_text:
                                        link_text = clean_text[:30] + "..."
                                    ctx = f"Testo: '{link_text}'"
                                    
                                    if fl not in links:
                                        links.append(fl)
                                        link_contexts[fl] = ctx
                                    else:
                                        # If it's already there, we only override if it doesn't have a better context
                                        if fl not in link_contexts or link_contexts[fl] == "":
                                            link_contexts[fl] = ctx
                                        
                                    if get_domain(fl) == domain and fl not in visited and fl not in queue:
                                        if not fl.lower().endswith(('.pdf', '.jpg', '.png', '.zip', '.mp4')):
                                            queue.append(fl)
                    
                    # Estrazione link dai bottoni, menu e immagini
                    d_links = []
                    for btn in comp.get("buttons", []):
                        if btn.get("d"): d_links.append((btn.get("d"), "Pulsante '" + str(btn.get("n", "Sconosciuto")) + "'"))
                        
                    indfile = comp.get("indfile", {})
                    if isinstance(indfile, dict) and isinstance(indfile.get("attr"), dict):
                        if indfile["attr"].get("d"): d_links.append((indfile["attr"]["d"], "Immagine/File"))
                        
                    param = comp.get("param", {})
                    if isinstance(param, dict) and "voci" in param:
                        for voce in param["voci"]:
                            if voce.get("d"): d_links.append((voce.get("d"), "Menu '" + str(voce.get("n", "Voce")) + "'"))
                            
                    for d, ctx in d_links:
                        if d.startswith("http"):
                            fl = d
                        elif d.startswith("popup:") or d.startswith("mailto:") or d.startswith("tel:"):
                            continue
                        else:
                            page_path = d.split("$")[0]
                            fl = urllib.parse.urljoin(current_url, f"/{page_path}")
                            
                        if fl not in links:
                            links.append(fl)
                            link_contexts[fl] = ctx
                        else:
                            link_contexts[fl] = ctx
                            
                        if get_domain(fl) == domain and fl not in visited and fl not in queue:
                            if not fl.lower().endswith(('.pdf', '.jpg', '.png', '.zip', '.mp4')):
                                queue.append(fl)
                    
                    if "componenti" in comp:
                        for child in comp["componenti"]:
                            parse_component(child)
                

                if interceptor.master_data:
                    for json_data in interceptor.master_data:
                        parse_component(json_data)
                
                if path in interceptor.intercepted_data:
                    for json_data in interceptor.intercepted_data[path]:
                        parse_component(json_data)
                        
            else:
                # Estrazione HTML classica
                videos = 0
                for tag in soup.find_all(['iframe', 'video', 'embed']):
                    if tag.name == 'video':
                        videos += 1
                        continue
                    src = tag.get('src', '').lower()
                    # Filtra iframe usati per tracking, chat (Wix), mappe, o captcha
                    if not src or any(x in src for x in ['wixapps', 'visitor-analytics', 'chat', 'maps', 'recaptcha', 'cookie', 'analytics']):
                        continue
                    videos += 1
                
                images_ratios = []
                try:
                    js_ratios = await page.evaluate('''() => {
                                                return Array.from(document.querySelectorAll('img')).map(img => {
                            let w = img.width || img.clientWidth || img.naturalWidth;
                            let h = img.height || img.clientHeight || img.naturalHeight;
                            return (w > 10 && h > 10) ? {w: Math.round(w), h: Math.round(h), ratio: Number((w / h).toFixed(2))} : null;
                        }).filter(r => r !== null);
                    }''')
                    images_ratios = js_ratios
                except Exception:
                    pass
                
                for element in soup(["script", "style", "noscript", "meta", "link", "head"]):
                    element.extract()
                text_content = soup.get_text(separator=' ', strip=True)
            
            if len(text_content) < 5 and len(links) == 0:
                print(f"    - [Avviso] Pagina vuota o non testuale saltata: {current_url}")
                continue
            
            site_data[path] = {
                "url": current_url,
                "html": html_content,
                "links": links,
                "link_contexts": link_contexts,
                "videos": videos,
                "images_ratios": images_ratios,
                "design_system": design_system,
                "text": text_content,
                "title": soup.title.string if soup.title else "Nessun Titolo"
            }
            
        except Exception as e:
            if "Download is starting" not in str(e):
                print(f"    [!] Errore nel caricamento di {current_url}: {e}")
            continue
            
    if is_flazio:
        page.remove_listener("response", interceptor.handle_response)
            
    return site_data

def analyze_links(original_domain, imported_site_data):
    errors = []
    internal_links = set()
    
    for path, data in imported_site_data.items():
        for link in data["links"]:
            link_domain = get_domain(link)
            if link_domain == original_domain:
                ctx = data.get("link_contexts", {}).get(link, "")
                ctx_str = f" in **{ctx}**" if ctx else ""
                errors.append(f"| Pagina {path} | <span style='color: #dc3545; font-weight: bold;'>🔴 Errore Link (Cross-Domain)</span> | Alta | Il link `{link}`{ctx_str} punta ancora al vecchio dominio originale. Da correggere. |")
            elif "flazio.com" in link_domain or "flazio.org" in link_domain:
                internal_links.add((path, link))
                
    # Check 404 per i link interni
    import urllib.request
    import urllib.error
    
    checked = {}
    for path, link in internal_links:
        if link not in checked:
            try:
                req = urllib.request.Request(link, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    checked[link] = response.status
            except urllib.error.HTTPError as e:
                checked[link] = e.code
            except Exception:
                checked[link] = 500
                
        if checked[link] in [404, 500]:
            ctx = imported_site_data[path].get("link_contexts", {}).get(link, "")
            ctx_str = f" in **{ctx}**" if ctx else ""
            errors.append(f"| Pagina {path} | <span style='color: #dc3545; font-weight: bold;'>🔴 Link Rotto (404)</span> | Critica | Il link interno `{link}`{ctx_str} porta a una pagina inesistente o in errore. |")
            
    return errors

def analyze_structure(original_site_data, imported_site_data, original_domain):
    errors = []
    
    for path, orig_data in original_site_data.items():
        if path not in imported_site_data:
            errors.append(f"| Pagina {path} | <span style='color: #fd7e14; font-weight: bold;'>🟠 Pagina Mancante</span> | Alta | Questa pagina esiste nel sito originale ma NON è stata trovata nell'importato. |")
            continue
            
        imp_data = imported_site_data[path]
        
        # Check similarità lunghezza testo (heuristic check)
        orig_len = len(orig_data['text'])
        imp_len = len(imp_data['text'])
        
        if orig_len > 0:
            diff_ratio = (imp_len / orig_len) * 100
            if diff_ratio < 60:
                errors.append(f"| Pagina {path} | <span style='color: #fd7e14; font-weight: bold;'>🟠 Testo Mancante</span> | Media | Il sito importato ha molto meno testo ({imp_len} char) rispetto all'originale ({orig_len} char). Controlla se mancano sezioni. |")
                
        # Check Video
        orig_vid = orig_data.get('videos', 0)
        imp_vid = imp_data.get('videos', 0)
        if orig_vid > imp_vid:
            errors.append(f"| Pagina {path} | <span style='color: #0d6efd; font-weight: bold;'>🔵 Video Mancanti</span> | Alta | Trovati solo {imp_vid} video/iframe rispetto ai {orig_vid} dell'originale. |")

        
        # Check Design System
        orig_ds = orig_data.get('design_system', {})
        imp_ds = imp_data.get('design_system', {})
        
        if orig_ds and imp_ds:
            orig_fonts = set([f.split(',')[0].strip().strip('\'"') for f in orig_ds.get('fonts', [])])
            imp_fonts = set([f.split(',')[0].strip().strip('\'"') for f in imp_ds.get('fonts', [])])
            
            # Se la pagina originale aveva dei font primari che non sono presenti su Flazio
            missing_fonts = orig_fonts - imp_fonts
            # Flazio potrebbe usare nomi simili o web-safe, ma se non c'è match esatto avvisiamo
            if len(missing_fonts) > 0 and len(imp_fonts) > 0:
                # Controlliamo solo se differiscono *completamente* (nessun font in comune)
                if len(orig_fonts.intersection(imp_fonts)) == 0:
                    errors.append(f"| Pagina {path} | <span style='color: #6f42c1; font-weight: bold;'>🟣 Design System (Font)</span> | Bassa | I font sembrano essere cambiati. Originale usava: `{', '.join(orig_fonts)}`, Flazio usa: `{', '.join(imp_fonts)}`. |")

        # Check immagini (Aspect Ratio)
        orig_ratios = orig_data.get('images_ratios', [])
        imp_ratios = imp_data.get('images_ratios', [])
        
        if orig_ratios and imp_ratios:
            # Conta quanti aspect ratio originali non trovano una corrispondenza tollerabile (±0.15) nel sito importato
            distorted = 0
            distorted_details = []
            for o_img in orig_ratios:
                if not any(abs(o_img['ratio'] - i_img['ratio']) < 0.15 for i_img in imp_ratios):
                    distorted += 1
                    distorted_details.append(f"{int(o_img['w'])}x{int(o_img['h'])}")
            
            # Se più del 30% delle immagini ha un aspect ratio non trovato, segnala possibile crop
            if distorted > 0 and (distorted / len(orig_ratios)) > 0.3:
                imp_sizes = ", ".join([f"{int(i['w'])}x{int(i['h'])}" for i in imp_ratios[:5]])
                errors.append(f"| Pagina {path} | <span style='color: #0d6efd; font-weight: bold;'>🔵 Immagini Distorte/Tagliate</span> | Media | Rilevate {distorted} immagini deformate. Misure originali perse: `{', '.join(distorted_details[:5])}`. Trovate su Flazio: `{imp_sizes}`... Controlla i ritagli. |")

        # --- VISUAL REGRESSION ---
        safe_domain = original_domain.replace("www.", "")
        safe_path = path.replace("/", "_")
        if not safe_path or safe_path == "_": safe_path = "_home"
        
        orig_img_path = os.path.join("results", safe_domain, "screenshots", "original", f"{safe_path}.png")
        imp_img_path = os.path.join("results", safe_domain, "screenshots", "flazio", f"{safe_path}.png")
        diff_img_path = os.path.join("results", safe_domain, "screenshots", f"{safe_path}_diff.png")
        
        diff_percent = visual_analyzer.compare_screenshots(orig_img_path, imp_img_path, diff_img_path)
        
        if diff_percent > 15.0:
            diff_abs_path = os.path.abspath(diff_img_path)
            errors.append(f"| Pagina {path} | <span style='color: #6f42c1; font-weight: bold;'>🟣 Visual Regression</span> | Media | Trovata forte deviazione grafica ({diff_percent:.1f}% di pixel diversi). [Vedi Diff]({diff_abs_path}) |")

        # (Rimosso il controllo sul numero dei link perché Flazio usa <li> con Javascript invece di <a>,
        # generando falsi positivi nel confronto matematico)

    return errors

def generate_report(link_errors, structure_errors):
    total_errors = len(link_errors) + len(structure_errors)
    
    report = f"""# Report di QA Automation - Migrazione Flazio (Analisi Deterministica Potenziata)

<style>
  table {{
    width: 100% !important;
    table-layout: fixed;
  }}
  th, td {{
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal;
  }}
  th:nth-child(1) {{ width: 20%; }} /* Elemento */
  th:nth-child(2) {{ width: 15%; }} /* Tipo di Errore */
  th:nth-child(3) {{ width: 10%; }} /* Gravità */
  th:nth-child(4) {{ width: 55%; }} /* Dettaglio */
</style>

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

    while True:
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
            # Clear args for the next iteration if we continue
            args.original = None
            args.imported = None
            continue

        print(f"\n[*] Inizio analisi comparativa STRUTTURALE (Senza AI)...")
        print(f"[*] Originale: {original_url}")
        print(f"[*] Importato: {imported_url}\n")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context() # Niente viewport fisso, non scattiamo foto
            page = await context.new_page()
            
            original_site_data = await crawl_site(page, original_url, max_pages=args.max_pages)
            imported_site_data = await crawl_site(page, imported_url, max_pages=args.max_pages, is_flazio=True)
            
            await browser.close()
            
        original_domain = get_domain(original_url)
        
        print("[*] Ricerca link rotti e riferimenti al vecchio dominio...")
        link_errors = analyze_links(original_domain, imported_site_data)
        
        print("[*] Analisi strutturale e confronto contenuti in corso...")
        structure_errors = analyze_structure(original_site_data, imported_site_data, original_domain)
        
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
        
        # Chiedi all'utente se vuole continuare
        print("-" * 60)
        while True:
            choice = input("Vuoi avviare la revisione di un altro sito? (y/n): ").strip().lower()
            if choice in ['y', 'n']:
                break
            print("Scelta non valida. Inserisci 'y' per sì o 'n' per no.")
            
        if choice == 'n':
            print("Chiusura dello script in corso... Arrivederci!")
            break
        else:
            # Resetta i parametri originali per richiedere l'input al prossimo giro
            args.original = None
            args.imported = None
            print("\n" * 2)

if __name__ == "__main__":
    asyncio.run(main())
