import asyncio
from bs4 import BeautifulSoup
import urllib.parse
from qa_automation_audit import FlazioInterceptor, normalize_url, get_domain
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        interceptor = FlazioInterceptor()
        page.on("response", interceptor.handle_response)
        
        current_url = "https://usersteviescreativearts.flazio.com/about-sca"
        await page.goto(current_url, wait_until="load")
        await page.wait_for_timeout(3000)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        links = []
        link_contexts = {}
        
        def parse_component(comp):
            nonlocal links, link_contexts
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
                
            if "componenti" in comp:
                for child in comp["componenti"]:
                    parse_component(child)

        path = "/about-sca"
        if path in interceptor.intercepted_data:
            print("Found intercepted data")
            for json_data in interceptor.intercepted_data[path]:
                parse_component(json_data)
                
        print("Link Contexts:", link_contexts)
        await browser.close()

asyncio.run(debug())
