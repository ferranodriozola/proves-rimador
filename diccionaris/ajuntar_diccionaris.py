import glob
import os
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FITXER_BASE = os.path.join(BASE_DIR, "diccionari.5.2.3.txt")
FITXER_SORTIDA = os.path.join(BASE_DIR, "diccionari.6.0.txt")

# Fitxers .txt o carpetes a ajuntar amb FITXER_BASE. Cada entrada pot ser un
# .txt concret o una carpeta (se n'agafen tots els .txt de dins, vegeu
# expandir_entrades). Edita aquesta llista abans d'executar l'script.
ENTRADES = [
    os.path.join(BASE_DIR, "..", "pronoms", "txt_fets"),
]

NOMBRE_CAMPS = 10


def llegir_linies(cami):
    try:
        with open(cami, "r", encoding="utf-8") as f:
            linies = [linia for linia in f.read().splitlines() if linia]
    except FileNotFoundError:
        raise SystemExit(f"No s'ha trobat el fitxer: {cami}")

    dolentes = [linia for linia in linies if linia.count("$") != NOMBRE_CAMPS - 1]
    if dolentes:
        raise SystemExit(
            f"{cami}: {len(dolentes)} línies no tenen {NOMBRE_CAMPS} camps separats per '$', "
            f"per exemple: {dolentes[0]!r}"
        )
    return linies


def clau_ordenacio(linia):
    """Ordena per la paraula (camp 0), ignorant accents i diacrítics (à=a, ç=c...).
    Com a desempat, la paraula original (amb accents i majúscules intactes): així
    'Índia' (majúscula) queda abans que 'índia', igual que ja ho fa el diccionari."""
    paraula = linia.split("$", 1)[0]
    sense_accents = "".join(
        c for c in unicodedata.normalize("NFD", paraula.lower())
        if unicodedata.category(c) != "Mn"
    )
    return (sense_accents, paraula)


def expandir_entrades(entrades):
    """Cada entrada pot ser un fitxer .txt concret o una carpeta: si és una
    carpeta, s'hi agafen tots els .txt que conté directament (no busca dins
    de subcarpetes). diccionari.5.2.3.txt i diccionari.6.0.txt es descarten
    si apareixen dins d'una carpeta, per no ajuntar-los amb ells mateixos."""
    exclosos = {os.path.abspath(FITXER_BASE), os.path.abspath(FITXER_SORTIDA)}
    fitxers = []
    for entrada in entrades:
        if os.path.isdir(entrada):
            trobats = sorted(glob.glob(os.path.join(entrada, "*.txt")))
            trobats = [f for f in trobats if os.path.abspath(f) not in exclosos]
            if not trobats:
                print(f"Avís: cap .txt trobat a la carpeta {entrada}")
            fitxers += trobats
        elif os.path.isfile(entrada):
            fitxers.append(entrada)
        else:
            raise SystemExit(f"No existeix ni com a fitxer ni com a carpeta: {entrada}")
    return fitxers


def ajuntar(entrades):
    fitxers_extra = expandir_entrades(entrades)

    linies = llegir_linies(FITXER_BASE)
    print(f"{os.path.basename(FITXER_BASE)}: {len(linies)} línies")

    for cami in fitxers_extra:
        noves = llegir_linies(cami)
        print(f"{os.path.basename(cami)}: {len(noves)} línies")
        linies += noves

    linies.sort(key=clau_ordenacio)

    with open(FITXER_SORTIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(linies) + "\n")

    print(f"Fet! {len(linies)} línies a {os.path.relpath(FITXER_SORTIDA, BASE_DIR)}")


if __name__ == "__main__":
    if not ENTRADES:
        raise SystemExit(
            "ENTRADES és buida: afegeix-hi almenys un fitxer .txt o una carpeta "
            f"per ajuntar amb {os.path.basename(FITXER_BASE)}."
        )
    ajuntar(ENTRADES)
