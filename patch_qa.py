import re

with open("qa_automation_audit.py", "r") as f:
    content = f.read()

# 1. Create screenshots directory in crawl_site
init_code = """    print(f"[*] Inizio discovery e crawling del dominio: {domain}")
    
    # Crea cartelle screenshot
    import os
    safe_domain = domain.replace("www.", "")
    screenshot_dir = os.path.join("results", safe_domain, "screenshots", "flazio" if is_flazio else "original")
    os.makedirs(screenshot_dir, exist_ok=True)"""
content = content.replace('    print(f"[*] Inizio discovery e crawling del dominio: {domain}")', init_code)

# 2. Add screenshot and design system extraction
inject_code = """            html_content = await page.content()
            
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
            
            soup = BeautifulSoup(html_content, "html.parser")"""
content = content.replace('            html_content = await page.content()\n            soup = BeautifulSoup(html_content, "html.parser")', inject_code)

# 3. Save design_system in site_data
content = content.replace('"images_ratios": images_ratios,', '"images_ratios": images_ratios,\n                "design_system": design_system,')

# 4. Add Design System check in analyze_structure
design_check = """
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
                    errors.append(f"| Pagina {path} | Design System (Font) | Bassa | I font sembrano essere cambiati. Originale usava: `{', '.join(orig_fonts)}`, Flazio usa: `{', '.join(imp_fonts)}`. |")

        # Check immagini (Aspect Ratio)"""
content = content.replace('# Check immagini (Aspect Ratio)', design_check)

with open("qa_automation_audit.py", "w") as f:
    f.write(content)
