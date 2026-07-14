import re

with open("qa_automation_audit.py", "r") as f:
    content = f.read()

# 1. Import visual_analyzer
content = "import visual_analyzer\nimport os\n" + content

# 2. Add domain parameter to analyze_structure
content = content.replace("def analyze_structure(original_site_data, imported_site_data):", "def analyze_structure(original_site_data, imported_site_data, original_domain):")

# 3. Add visual regression to analyze_structure
visual_code = """        # Check immagini (Aspect Ratio)
        orig_ratios = orig_data.get('images_ratios', [])
        imp_ratios = imp_data.get('images_ratios', [])
        
        if orig_ratios and imp_ratios:
            # Conta quanti aspect ratio originali non trovano una corrispondenza tollerabile (±0.15) nel sito importato
            distorted = 0
            for o_r in orig_ratios:
                if not any(abs(o_r - i_r) < 0.15 for i_r in imp_ratios):
                    distorted += 1
            
            # Se più del 30% delle immagini ha un aspect ratio non trovato, segnala possibile crop
            if distorted > 0 and (distorted / len(orig_ratios)) > 0.3:
                errors.append(f"| Pagina {path} | Immagini Distorte/Tagliate | Media | Rilevate {distorted} immagini con proporzioni originali (Aspect Ratio) perse nel nuovo sito. Controlla ritagli o deformazioni. |")

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
            errors.append(f"| Pagina {path} | Visual Regression | Media | Trovata forte deviazione grafica ({diff_percent:.1f}% di pixel diversi). [Vedi Diff]({diff_abs_path}) |")

        # (Rimosso il controllo sul numero dei link perché Flazio usa <li> con Javascript invece di <a>,"""
content = content.replace("        # Check immagini (Aspect Ratio)\n        orig_ratios = orig_data.get('images_ratios', [])\n        imp_ratios = imp_data.get('images_ratios', [])\n        \n        if orig_ratios and imp_ratios:\n            # Conta quanti aspect ratio originali non trovano una corrispondenza tollerabile (±0.15) nel sito importato\n            distorted = 0\n            for o_r in orig_ratios:\n                if not any(abs(o_r - i_r) < 0.15 for i_r in imp_ratios):\n                    distorted += 1\n            \n            # Se più del 30% delle immagini ha un aspect ratio non trovato, segnala possibile crop\n            if distorted > 0 and (distorted / len(orig_ratios)) > 0.3:\n                errors.append(f\"| Pagina {path} | Immagini Distorte/Tagliate | Media | Rilevate {distorted} immagini con proporzioni originali (Aspect Ratio) perse nel nuovo sito. Controlla ritagli o deformazioni. |\")\n\n        # (Rimosso il controllo sul numero dei link perché Flazio usa <li> con Javascript invece di <a>,", visual_code)

# 4. Update the call to analyze_structure in main()
content = content.replace("structure_errors = analyze_structure(original_site_data, imported_site_data)", "structure_errors = analyze_structure(original_site_data, imported_site_data, original_domain)")

with open("qa_automation_audit.py", "w") as f:
    f.write(content)
