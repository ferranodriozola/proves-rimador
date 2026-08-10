import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_SEPARAT = os.path.join(BASE_DIR, "..", "..", "diccionaris", "separat")
FITXER_SORTIDA = os.path.join(BASE_DIR, "gerundis_hi_en.txt")

CODI_GERUNDI = "VMG00000"

VOCALS_AFI = set("aeiouəɛɔ")

FORMA_CODI = "G"
PERSONA_CODI = "00"

PRONOM_CODI = {
    "em": "EM", "et": "ET", "es": "ES", "ens": "NS", "us": "US",
    "el": "EL", "la": "LA", "els_ac": "EA", "les": "LE",
    "li": "LI", "els_dat": "ED",
    "en": "EN", "ho": "HO", "hi": "HI",
}

def construir_codi(pronoms):
    lletres = "".join(PRONOM_CODI[p] for p in pronoms)
    return f"W{FORMA_CODI}{PERSONA_CODI}_{len(pronoms)}{lletres}"


def llegir_columna(n):
    ruta = os.path.join(DIR_SEPARAT, f"col_{n}.txt")
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def comprovar_transcripcions(col):
    dolents = [col[0][i] for i in range(len(col[0]))
               if col[2][i] == CODI_GERUNDI
               and "-" not in col[0][i]
               and col[9][i].count("ˈ") != 1]
    if dolents:
        raise SystemExit(
            f"Hi ha {len(dolents)} gerundis amb un nombre d'accents primaris estrany "
            f"al diccionari: {', '.join(dolents[:8])}"
            f"{'...' if len(dolents) > 8 else ''}\n"
            "Corregeix-los a col_10 abans de generar res."
        )
    no_acaben_consonant = [col[0][i] for i in range(len(col[0]))
                            if col[2][i] == CODI_GERUNDI and col[0][i][-1].lower() != "t"]
    if no_acaben_consonant:
        raise SystemExit(
            f"Hi ha {len(no_acaben_consonant)} gerundis que no acaben en 't': "
            f"{', '.join(no_acaben_consonant[:8])}\n"
            "Aquest script assumeix que tots els gerundis acaben en consonant "
            "(guionet sempre, mai apòstrof); revisa la dada abans de continuar."
        )


def forma_enclitica(pronom):
    if pronom == "hi":
        return "-hi"
    if pronom == "en":
        return "-ne"
    raise ValueError(pronom)


def transcriure(transcripcio, pronom):
    """
    Munta la transcripció AFI del grup gerundi+pronom a partir de la del verb sol.

    La -t final de '-nt' és muda quan el gerundi va sol (cantant -> kəntˈan) i
    es recupera o no segons què ve darrere, exactament com la -r de l'infinitiu:

      · davant enclític vocàlic, sona [t]:      cantant-hi -> kəntˈanti
        (precedent al diccionari: 'vint-i-set' -> bˈintisˈɛt, la t de "vint"
        sona davant la "i")
      · davant enclític consonàntic, cau:        cantant-ne -> kəntˈannə
        (precedent: 'Mont-real' -> mˈonreˈal, 'Nogent-sur-Marne' -> nuʒˈensˈurmˈarnə;
        la doble n resultant és una grafia normal al diccionari: 'connectar' -> kunnəktˈa)

    A diferència de l'infinitiu, aquí '-hi' mai queda darrere vocal (el que el
    precedeix sempre és la 't' recuperada o la 'n' pròpia del gerundi), per
    tant no hi ha semivocalització de '-hi' en aquest cas.
    """
    if pronom == "hi":
        return transcripcio + "ti"
    if pronom == "en":
        return transcripcio + "nə"
    raise ValueError(pronom)


def calcular_rimes(transcripcio):
    """Mateix càlcul que 'creador_rima + dicc (a partir de col_10).py', perquè no divergeixin."""
    consonant = transcripcio.split("ˈ")[-1]
    assonant = "".join(l for l in consonant if l in "ɔəaeiou@Eɛˈ")
    return consonant, assonant


def generar():
    col = {n: llegir_columna(n) for n in range(10)}

    total = len(col[0])
    if any(len(col[n]) != total for n in col):
        raise SystemExit("Les columnes no tenen el mateix nombre de línies: no es pot continuar.")

    comprovar_transcripcions(col)

    linies = []
    comptador = Counter()

    for i in range(total):
        if col[2][i] != CODI_GERUNDI:
            continue

        forma = col[0][i]
        transcripcio_base = col[9][i]
        if not forma or not transcripcio_base:
            comptador["saltats (sense forma o transcripció)"] += 1
            continue

        for pronom in ("hi", "en"):
            codi = construir_codi([pronom])
            enclitic = forma_enclitica(pronom)
            transcripcio = transcriure(transcripcio_base, pronom)
            consonant, assonant = calcular_rimes(transcripcio)

            linies.append("$".join([
                forma + enclitic,        # 0 paraula
                col[1][i],               # 1 d'on ve (el lema del verb)
                codi,                    # 2 codi
                consonant,               # 3 rima consonant
                assonant,                # 4 rima assonant
                str(int(col[5][i]) + 1),  # 5 síl·labes: el guionet sempre en suma 1
                col[6][i],               # 6 Vicc   ) hereten els del verb: els enllaços
                col[7][i],               # 7 Viq    ) de la UI apunten al lema (col_1),
                col[8][i],               # 8 Diec   ) que continua sent el verb
                transcripcio,            # 9 transcripció
            ]))
            comptador[enclitic] += 1

    with open(FITXER_SORTIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(linies) + "\n")

    print(f"Fet! {len(linies)} línies a {os.path.relpath(FITXER_SORTIDA, BASE_DIR)}")
    print(f"  gerundis processats: {len(linies) // 2}")
    for enclitic, n in sorted(comptador.items()):
        print(f"  {enclitic}: {n}")


if __name__ == "__main__":
    generar()
