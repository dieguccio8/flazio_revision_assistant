import asyncio
from playwright.async_api import async_playwright
import json
import re

async def investigate_flazio():
    url = "https://usersteviescreativearts.flazio.com/"
    print(f"[*] Avvio investigazione su: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url, wait_until="load")
        
        print("\n--- 1. ANALISI DEI LINK ---")
        links = await page.evaluate('''() => {
            const anchors = Array.from(document.querySelectorAll('a'));
            return anchors.map(a => ({
                text: a.innerText.trim(),
                href: a.href,
                className: a.className,
                onclick: a.getAttribute('onclick')
            }));
        }''')
        
        for link in links:
            if link['href'] or link['onclick']:
                print(f"Testo: '{link['text']}' | Href: {link['href']} | OnClick: {link['onclick']}")

        print("\n--- 2. RICERCA DI VARIABILI GLOBALI (Routing/Dati) ---")
        # Molti site builder come Flazio salvano i dati delle pagine in variabili JS globali
        global_vars = await page.evaluate('''() => {
            const keys = Object.keys(window);
            return keys.filter(k => k.toLowerCase().includes('flazio') || k.toLowerCase().includes('page') || k.toLowerCase().includes('data'));
        }''')
        print("Possibili variabili globali interessanti:", global_vars)
        
        print("\n--- 3. ESTRAZIONE MENU / NAVIGAZIONE ---")
        # Cerchiamo elementi che potrebbero essere voci di menu
        nav_items = await page.evaluate('''() => {
            const items = Array.from(document.querySelectorAll('[class*="menu"], [class*="nav"], li'));
            return items.map(el => el.outerHTML.substring(0, 150)).slice(0, 10);
        }''')
        for item in nav_items:
            print(item)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(investigate_flazio())
