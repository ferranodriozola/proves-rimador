import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_SEPARAT = os.path.join(BASE_DIR, "..", "diccionaris", "separat")
FITXER_SORTIDA = os.path.join(BASE_DIR, "infinitius_hi_en.txt")

CODI_INFINITIU = "VMN00000"

HI_SEMIVOCAL_DARRERE_VOCAL = True #Ara mateix: /véndraj/ (vendre-hi)

VOCALS_GRAFIQUES = set("aeioàèéíòóú")

VOCALS_AFI = set("aeiouəɛɔ")

FORMA_CODI = "N"
PERSONA_CODI = "000"

PRONOM_CODI = {
    "em": "EM", "et": "ET", "es": "ES", "ens": "NS", "us": "US",
    "el": "EL", "la": "LA", "els_ac": "EA", "les": "LE",
    "li": "LI", "els_dat": "ED",
    "en": "EN", "ho": "HO", "hi": "HI",
}


def construir_codi(pronoms):
    lletres = "".join(PRONOM_CODI[p] for p in pronoms)
    return f"W{FORMA_CODI}{PERSONA_CODI}{len(pronoms)}{lletres}"


def llegir_columna(n):
    ruta = os.path.join(DIR_SEPARAT, f"col_{n}.txt")
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def comprovar_transcripcions(col):
    dolents = [col[0][i] for i in range(len(col[0]))
               if col[2][i] == CODI_INFINITIU and col[9][i].endswith("r")]
    if dolents:
        raise SystemExit(
            f"Hi ha {len(dolents)} infinitius amb la -r transcrita al diccionari, "
            f"i no hi haurien de ser: {', '.join(dolents[:8])}"
            f"{'...' if len(dolents) > 8 else ''}\n"
            "Corregeix-los a col_10 abans de generar res."
        )


def acaba_en_vocal(forma):
    return forma[-1].lower() in VOCALS_GRAFIQUES


def forma_enclitica(pronom, forma):
    if pronom == "hi":
        return "-hi"  # 'hi' no té forma reduïda: sempre amb guionet
    if pronom == "en":
        return "'n" if acaba_en_vocal(forma) else "-ne"
    raise ValueError(pronom)


def transcriure(forma, transcripcio, enclitic):
    if enclitic == "-hi":
        fonema = "i"
    elif enclitic == "-ne":
        fonema = "nə"
    elif enclitic == "'n":
        fonema = "n"
    else:
        raise ValueError(enclitic)

    comenca_en_vocal = fonema[0] in VOCALS_AFI

    # (1) la -r de l'infinitiu
    if forma[-1].lower() == "r":
        transcripcio += "ɾ" if comenca_en_vocal else "r"

    # (2) semivocalització de '-hi' darrere vocal
    if (enclitic == "-hi"
            and HI_SEMIVOCAL_DARRERE_VOCAL
            and transcripcio
            and transcripcio[-1] in VOCALS_AFI):
        fonema = "j"

    return transcripcio + fonema, fonema


def calcular_rimes(transcripcio):
    """Mateix càlcul que 'creador_rima + dicc (a partir de col_10).py', perquè no divergeixin."""
    consonant = transcripcio.split("ˈ")[-1]
    assonant = "".join(l for l in consonant if l in "ɔəaeiou@Eɛˈ")
    return consonant, assonant


def silabes(silabes_base, enclitic, fonema):
    """L'enclític amb guionet suma una síl·laba; el d'apòstrof no (cf. abans-d'ahir = 4)."""
    return int(silabes_base) + (0 if enclitic.startswith("'") or fonema == "j" else 1)


def generar():
    col = {n: llegir_columna(n) for n in range(10)}

    total = len(col[0])
    if any(len(col[n]) != total for n in col):
        raise SystemExit("Les columnes no tenen el mateix nombre de línies: no es pot continuar.")

    comprovar_transcripcions(col)

    linies = []
    comptador = Counter()

    for i in range(total):
        if col[2][i] != CODI_INFINITIU:
            continue

        forma = col[0][i]
        transcripcio_base = col[9][i]
        if not forma or not transcripcio_base:
            comptador["saltats (sense forma o transcripció)"] += 1
            continue

        for pronom in ("hi", "en"):
            codi = construir_codi([pronom])
            enclitic = forma_enclitica(pronom, forma)
            transcripcio, fonema = transcriure(forma, transcripcio_base, enclitic)
            consonant, assonant = calcular_rimes(transcripcio)

            linies.append("$".join([
                forma + enclitic,        # 0 paraula
                col[1][i],               # 1 d'on ve (el lema del verb)
                codi,                    # 2 codi
                consonant,               # 3 rima consonant
                assonant,                # 4 rima assonant
                str(silabes(col[5][i], enclitic, fonema)),  # 5 síl·labes
                col[6][i],               # 6 Vicc   ) hereten els del verb: els enllaços
                col[7][i],               # 7 Viq    ) de la UI apunten al lema (col_1),
                col[8][i],               # 8 Diec   ) que continua sent el verb
                transcripcio,            # 9 transcripció
            ]))
            comptador[enclitic] += 1

    with open(FITXER_SORTIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(linies) + "\n")

    print(f"Fet! {len(linies)} línies a {os.path.relpath(FITXER_SORTIDA, BASE_DIR)}")
    print(f"  infinitius processats: {len(linies) // 2}")
    for enclitic, n in sorted(comptador.items()):
        print(f"  {enclitic}: {n}")


if __name__ == "__main__":
    generar()