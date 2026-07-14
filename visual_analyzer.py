from PIL import Image, ImageChops
import os

def compare_screenshots(orig_path, imp_path, output_diff_path, threshold=15):
    """
    Confronta due screenshot e genera un'immagine diff con le differenze in rosso.
    Ritorna la percentuale di differenza visiva (0-100).
    """
    if not os.path.exists(orig_path) or not os.path.exists(imp_path):
        return -1.0
        
    try:
        img1 = Image.open(orig_path).convert("RGB")
        img2 = Image.open(imp_path).convert("RGB")
        
        # Ridimensiona img2 (Flazio) per adattarlo all'altezza di img1 se differiscono
        # (Spesso i siti importati hanno altezze leggermente diverse)
        width1, height1 = img1.size
        width2, height2 = img2.size
        
        # Trova la dimensione minima per confrontare i pixel comuni
        min_width = min(width1, width2)
        min_height = min(height1, height2)
        
        img1_crop = img1.crop((0, 0, min_width, min_height))
        img2_crop = img2.crop((0, 0, min_width, min_height))
        
        # Calcola la differenza assoluta
        diff = ImageChops.difference(img1_crop, img2_crop)
        
        # Converti a scala di grigi per calcolare la distanza
        diff_gray = diff.convert("L")
        
        # Applica una soglia per ignorare differenze microscopiche (anti-aliasing, compressione)
        diff_bw = diff_gray.point(lambda p: 255 if p > threshold else 0)
        
        # Calcola percentuale di pixel diversi
        diff_pixels = sum(1 for p in diff_bw.getdata() if p == 255)
        total_pixels = min_width * min_height
        diff_percent = (diff_pixels / total_pixels) * 100
        
        # Se c'è una differenza sostanziale (es. > 1%), genera l'immagine diff
        if diff_percent > 1.0:
            # Crea un'immagine con base l'originale sbiadito
            base = img1_crop.copy()
            base = base.point(lambda p: int(p * 0.3)) # Sbiadisce del 70%
            
            # Crea layer rosso per le differenze
            red_layer = Image.new("RGB", base.size, (255, 0, 0))
            
            # Applica il layer rosso solo dove ci sono differenze (usando diff_bw come maschera)
            diff_image = Image.composite(red_layer, base, diff_bw)
            diff_image.save(output_diff_path)
            
        return diff_percent
        
    except Exception as e:
        print(f"Errore in visual regression per {orig_path}: {e}")
        return -1.0
