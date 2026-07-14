# Report di QA Automation - Migrazione Flazio (Analisi Deterministica Potenziata)

## Sintesi Iniziale
- **Totale anomalie riscontrate**: 38
- *Nota: Questa analisi matematica confronta pagine, quantità di testi e destinazione dei link tra sito originale e importato.*

## Tabella Dettagliata delle Discrepanze

| Elemento | Tipo di Errore | Gravità | Dettaglio / Suggerimento di correzione |
|----------|----------------|---------|----------------------------------------|
| Pagina /biografie | Errore Link (Cross-Domain) | Alta | Il link `https://www.steviescreativearts.de/faust` punta ancora al vecchio dominio originale. Da correggere. |
| Pagina /biografie | Errore Link (Cross-Domain) | Alta | Il link `https://www.steviescreativearts.de/faust` punta ancora al vecchio dominio originale. Da correggere. |
| Pagina /biografie | Errore Link (Cross-Domain) | Alta | Il link `https://www.steviescreativearts.de/faust` punta ancora al vecchio dominio originale. Da correggere. |
| Pagina /biografie | Errore Link (Cross-Domain) | Alta | Il link `https://www.steviescreativearts.de/voice` punta ancora al vecchio dominio originale. Da correggere. |
| Pagina /biografie | Errore Link (Cross-Domain) | Alta | Il link `https://www.steviescreativearts.de` punta ancora al vecchio dominio originale. Da correggere. |
| Pagina /biografie | Errore Link (Cross-Domain) | Alta | Il link `https://www.steviescreativearts.de` punta ancora al vecchio dominio originale. Da correggere. |
| Pagina / | Testo Mancante | Media | Il sito importato ha molto meno testo (2595 char) rispetto all'originale (6954 char). Controlla se mancano sezioni. |
| Pagina / | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 2 dell'originale. |
| Pagina /store-products-sitemap.xml | Pagina Mancante | Alta | Questa pagina esiste nel sito originale ma NON è stata trovata nell'importato. |
| Pagina /pages-sitemap.xml | Pagina Mancante | Alta | Questa pagina esiste nel sito originale ma NON è stata trovata nell'importato. |
| Pagina /musiker | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 3 dell'originale. |
| Pagina /referenzen | Testo Mancante | Media | Il sito importato ha molto meno testo (1298 char) rispetto all'originale (2488 char). Controlla se mancano sezioni. |
| Pagina /referenzen | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 2 dell'originale. |
| Pagina /about-sca | Testo Mancante | Media | Il sito importato ha molto meno testo (3070 char) rispetto all'originale (9013 char). Controlla se mancano sezioni. |
| Pagina /about-sca | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 2 dell'originale. |
| Pagina /voice | Testo Mancante | Media | Il sito importato ha molto meno testo (2620 char) rispetto all'originale (15346 char). Controlla se mancano sezioni. |
| Pagina /faust | Testo Mancante | Media | Il sito importato ha molto meno testo (1259 char) rispetto all'originale (17590 char). Controlla se mancano sezioni. |
| Pagina /faust | Video Mancanti | Alta | Trovati solo 1 video/iframe rispetto ai 7 dell'originale. |
| Pagina /faustreaktionen | Testo Mancante | Media | Il sito importato ha molto meno testo (1369 char) rispetto all'originale (10519 char). Controlla se mancano sezioni. |
| Pagina /faustreaktionen | Video Mancanti | Alta | Trovati solo 3 video/iframe rispetto ai 4 dell'originale. |
| Pagina /anfragen-faust | Testo Mancante | Media | Il sito importato ha molto meno testo (1557 char) rispetto all'originale (2988 char). Controlla se mancano sezioni. |
| Pagina /faust-agb | Testo Mancante | Media | Il sito importato ha molto meno testo (1233 char) rispetto all'originale (2770 char). Controlla se mancano sezioni. |
| Pagina /faust-agb | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 2 dell'originale. |
| Pagina /actor | Testo Mancante | Media | Il sito importato ha molto meno testo (1664 char) rispetto all'originale (3581 char). Controlla se mancano sezioni. |
| Pagina /fotos | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 3 dell'originale. |
| Pagina /vita | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 2 dell'originale. |
| Pagina /take-your-stage | Testo Mancante | Media | Il sito importato ha molto meno testo (1240 char) rispetto all'originale (10067 char). Controlla se mancano sezioni. |
| Pagina /take-your-stage | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 2 dell'originale. |
| Pagina /coaching | Testo Mancante | Media | Il sito importato ha molto meno testo (2338 char) rispetto all'originale (4265 char). Controlla se mancano sezioni. |
| Pagina /biografie | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 2 dell'originale. |
| Pagina /social-media-online-praesenzen | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 2 dell'originale. |
| Pagina /impressum | Testo Mancante | Media | Il sito importato ha molto meno testo (2323 char) rispetto all'originale (30195 char). Controlla se mancano sezioni. |
| Pagina /impressum | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 2 dell'originale. |
| Pagina /steffenspielt | Testo Mancante | Media | Il sito importato ha molto meno testo (1259 char) rispetto all'originale (17590 char). Controlla se mancano sezioni. |
| Pagina /steffenspielt | Video Mancanti | Alta | Trovati solo 1 video/iframe rispetto ai 7 dell'originale. |
| Pagina /backstagefotos | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 3 dell'originale. |
| Pagina /film-tv-fotos | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 3 dell'originale. |
| Pagina /theaterfotos | Video Mancanti | Alta | Trovati solo 0 video/iframe rispetto ai 3 dell'originale. |

## Azioni Correttive Prioritarie
- Risolvere tutti gli "Errori Link (Cross-Domain)" per evitare che gli utenti finiscano sul vecchio sito cliccando sui menu.
- Controllare le pagine segnalate come "Pagina Mancante" e importarle su Flazio.
- Verificare i testi segnalati come "Testo Mancante": potrebbero essersi persi dei paragrafi durante l'importazione.
