import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_SEPARAT = os.path.join(BASE_DIR, "..", "..", "diccionaris", "separat")
FITXER_SORTIDA = os.path.join(BASE_DIR, "imperatius_hi_en.txt")

VOCALS_GRAFIQUES = set("aeioàèéíòóú")
VOCALS_AFI = set("aeiouəɛɔ")

FORMA_CODI = "M"

PRONOM_CODI = {
    "em": "EM", "et": "ET", "es": "ES", "ens": "NS", "us": "US",
    "el": "EL", "la": "LA", "els_ac": "EA", "les": "LE",
    "li": "LI", "els_dat": "ED",
    "en": "EN", "ho": "HO", "hi": "HI",
}

# Codi font (EAGLES) -> persona pròpia. Es fusionen aquí les variants que la
# font marca de manera diferent però que són la mateixa persona gramatical:
#   · el sufix "Y" marca que la forma és homògrafa d'una altra cel·la del
#     paradigma (subjuntiu, per a vostè/vostès; present d'indicatiu, per a
#     alguns verbs en -ir de la "tu": obre, omple...) — no canvia la persona.
#   · "VMM03S00"/"VMM03P00" (càpiga, sàpiga...) són la mateixa persona que
#     "...0Y" però sense la marca, per una inconsistència del càlcul d'origen.
#   · "VSM*" és el verb 'ser', etiquetat amb un tercer tipus de verb principal
#     (paral·lel a "VAM"/"VMM") que ja fa servir aquest mateix diccionari als
#     seus propis filtres (js/script.js: crearCriterisTriples('Imperatiu',
#     'VAM','VSM','VMM')).
# S'ha comprovat que cap lema queda repetit dues vegades dins la mateixa
# persona un cop fetes aquestes fusions.
CODIS_FONT = {
    "VMM02S00": "02S", "VMM02S0Y": "02S", "VSM02S00": "02S",
    "VMM01P00": "01P",                    "VSM01P00": "01P",
    "VMM02P00": "02P", "VMM02P0X": "02P", "VSM02P00": "02P",
    "VMM03S00": "03S", "VMM03S0Y": "03S", "VSM03S0Y": "03S",
    "VMM03P00": "03P", "VMM03P0Y": "03P", "VSM03P0Y": "03P",
}


def construir_codi(persona, pronoms):
    lletres = "".join(PRONOM_CODI[p] for p in pronoms)
    return f"W{FORMA_CODI}{persona}_{len(pronoms)}{lletres}"


def llegir_columna(n):
    ruta = os.path.join(DIR_SEPARAT, f"col_{n}.txt")
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def comprovar_transcripcions(col):
    """
    Cada forma d'imperatiu ha de dur com a màxim un accent primari (tret dels
    compostos amb guionet propi, que en poden dur més d'un legítimament, un
    per component). Es va trobar 1 cas amb 2 accents ('desment', de
    'desmentir': dˈesmˈen en comptes de dəzmˈen, pel mateix tipus de
    contaminació que ja es va corregir als infinitius i que encara hi ha als
    gerundis). No es flagen les formes SENSE cap accent (94 monosíl·labs, la
    majoria SÍ en porten un ('bat' -> bˈat) però 2 no ('bull' -> bwl): no és
    un error, calcular_rimes() funciona igual sense la marca en un monosíl·lab.
    """
    dolents = [col[0][i] for i in range(len(col[0]))
               if col[2][i] in CODIS_FONT
               and "-" not in col[0][i]
               and col[9][i].count("ˈ") > 1]
    if dolents:
        raise SystemExit(
            f"Hi ha {len(dolents)} imperatius amb un nombre d'accents primaris estrany "
            f"al diccionari: {', '.join(dolents[:8])}"
            f"{'...' if len(dolents) > 8 else ''}\n"
            "Corregeix-los a col_10 abans de generar res."
        )


def acaba_en_vocal(forma):
    """Regla gràfica de l'enclisi: mira l'última lletra del verb ESCRIT."""
    return forma[-1].lower() in VOCALS_GRAFIQUES


def forma_enclitica(pronom, forma):
    """Forma plena (guionet) darrere consonant o diftong; reduïda (apòstrof) darrere vocal."""
    if pronom == "hi":
        return "-hi"  # 'hi' no té forma reduïda: sempre amb guionet
    if pronom == "en":
        return "'n" if acaba_en_vocal(forma) else "-ne"
    raise ValueError(pronom)


def transcriure(transcripcio, enclitic):
    """
    Munta la transcripció AFI del grup imperatiu+pronom a partir de la del
    verb sol. A diferència de l'infinitiu i el gerundi, l'imperatiu no té una
    única terminació: acaba en qualsevol consonant o vocal segons la persona
    i el verb, així que aquí NOMÉS s'aplica la regla de sàndhi que té
    precedent clar i general en català (i al mateix diccionari):

      · la -s final es sonoritza en [z] davant de qualsevol dels dos pronoms,
        perquè tots dos comencen per so sonor ('hi' per vocal, '-ne'/''n' per
        la nasal 'n'): digues-hi -> dˈiɣəzi, digues-ne -> dˈiɣəznə.
        Precedent: 'esdevenir' -> əzðəβənˈi, 'esmena' -> əzmˈɛnə,
        'despús-ahir' -> dəspˈuzəˈi.

      · darrere vocal, '-hi' es realitza com a semivocal [j] (mateixa regla
        que infinitius i gerundis: HI_SEMIVOCAL_DARRERE_VOCAL).

    NO s'apliquen més transformacions a altres consonants finals (t, k, p,
    ʃ...). Als compostos que ja hi ha al diccionari el comportament és
    inconsistent segons la paraula ('blanc-i-blau' recupera la k, 'alt-alemany'
    elideix la t; 'baix-alemany' sonoritza la ʃ en ʒ, però és l'únic exemple
    que n'hi ha), i cap d'aquests casos és una combinació verb+pronom feble,
    així que no hi ha una regla neta per triar. Es concatenen tal qual.

    Retorna (transcripcio_completa, fonema_de_l'enclitic).
    """
    if enclitic == "-hi":
        fonema = "i"
    elif enclitic == "-ne":
        fonema = "nə"
    elif enclitic == "'n":
        fonema = "n"
    else:
        raise ValueError(enclitic)

    if transcripcio.endswith("s"):
        transcripcio = transcripcio[:-1] + "z"

    if enclitic == "-hi" and transcripcio and transcripcio[-1] in VOCALS_AFI:
        fonema = "j"

    return transcripcio + fonema, fonema


def calcular_rimes(transcripcio):
    """Mateix càlcul que 'creador_rima + dicc (a partir de col_10).py', perquè no divergeixin."""
    consonant = transcripcio.split("ˈ")[-1]
    assonant = "".join(l for l in consonant if l in "ɔəaeiou@Eɛˈ")
    return consonant, assonant


def silabes(silabes_base, enclitic, fonema):
    """L'enclític amb guionet suma una síl·laba; el d'apòstrof no. La semivocal
    [j] de '-hi' darrere vocal es fon amb la vocal anterior i tampoc no en suma."""
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
        persona = CODIS_FONT.get(col[2][i])
        if persona is None:
            continue

        forma = col[0][i]
        transcripcio_base = col[9][i]
        if not forma or not transcripcio_base:
            comptador["saltats (sense forma o transcripció)"] += 1
            continue

        for pronom in ("hi", "en"):
            codi = construir_codi(persona, [pronom])
            enclitic = forma_enclitica(pronom, forma)
            transcripcio, fonema = transcriure(transcripcio_base, enclitic)
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
            comptador[f"{persona} {enclitic}"] += 1

    with open(FITXER_SORTIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(linies) + "\n")

    print(f"Fet! {len(linies)} línies a {os.path.relpath(FITXER_SORTIDA, BASE_DIR)}")
    print(f"  formes d'imperatiu processades: {len(linies) // 2}")
    for clau, n in sorted(comptador.items()):
        print(f"  {clau}: {n}")


if __name__ == "__main__":
    generar()
