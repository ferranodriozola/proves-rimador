"""
Ortografia de l'enclisi: verb + pronom feble.

Versió simplificada: només determina com s'escriu gràficament (guionet o apòstrof),
en genera el codi morfològic, i en calcula el nombre de síl·labes gràfiques.
"""

# ---------------------------------------------------------------- alfabets

VOCALS_GRAFIQUES = set("aeioàèéíòóúïü")

# ------------------------------------------------------- taula de l'enclisi

ENCLISI = {
    "em":  ("-me",  "'m"),
    "et":  ("-te",  "'t"),
    "es":  ("-se",  "'s"),
    "ens": ("-nos", "'ns"),
    "us":  ("-vos", "-us"),
    "el":  ("-lo",  "'l"),
    "la":  ("-la",  "-la"),
    "els": ("-los", "'ls"),
    "les": ("-les", "-les"),
    "li":  ("-li",  "-li"),
    "en":  ("-ne",  "'n"),
    "ho":  ("-ho",  "-ho"),
    "hi":  ("-hi",  "-hi"),
}

PRONOM_CODI = {
    "em": "EM", "et": "ET", "es": "ES", "ens": "NS", "us": "US",
    "el": "EL", "la": "LA", "els": "LS", "les": "LE", "li": "LI",
    "en": "NE", "ho": "HO", "hi": "HI",
}

ORDRE_PRONOMS = ["es", "et", "us", "em", "ens", "li", "els",
                 "el", "la", "les", "en", "hi", "ho"]

# ----------------------------------------------------------------- ortografia

def acaba_en_vocal(forma):
    return forma[-1].lower() in VOCALS_GRAFIQUES

def forma_enclitica(pronom, forma):
    plena, reduida = ENCLISI[pronom]
    return reduida if acaba_en_vocal(forma) else plena

def escriure(forma, enclitic):
    return forma + enclitic

# ----------------------------------------------------------------- síl·labes

def calcular_silabes(silabes_base, forma, enclitic):
    """
    L'enclític amb guionet suma una síl·laba; el d'apòstrof no.
    Excepció: '-hi' i '-ho' darrere vocal es fonen en semivocal i tampoc sumen.
    """
    if enclitic.startswith("'"):
        extra = 0
    elif enclitic in ("-hi", "-ho") and acaba_en_vocal(forma):
        extra = 0
    else:
        extra = 1
    return int(silabes_base) + extra

# ------------------------------------------------------------------- el codi

def construir_codi(forma_verbal, persona, pronoms):
    if forma_verbal not in ("N", "G", "M"):
        raise ValueError(f"forma verbal desconeguda: {forma_verbal!r}")
    if not 1 <= len(pronoms) <= 2:
        raise ValueError(f"calen 1 o 2 pronoms, no {len(pronoms)}")

    pers = "000" if persona is None else persona
    if len(pers) != 3:
        raise ValueError(f"la persona ha de fer 3 caràcters: {pers!r}")

    codis = [PRONOM_CODI[p] for p in pronoms]
    if len(codis) == 1:
        codis.append("00")

    codi = f"W{forma_verbal}{pers}{len(pronoms)}{''.join(codis)}"
    assert len(codi) == 10, codi
    return codi

def ordenar_pronoms(pronoms):
    return sorted(pronoms, key=ORDRE_PRONOMS.index)

# ------------------------------------------------------- tot d'una vegada

def generar_forma(forma, pronoms, forma_verbal, persona=None, silabes_base=0):
    pronoms = ordenar_pronoms(pronoms)
    if not 1 <= len(pronoms) <= 2:
        raise ValueError(f"Aquesta versió només accepta 1 o 2 pronoms. Rebut: {len(pronoms)}")

    paraula_actual = forma
    silabes_actuals = int(silabes_base)

    # Iterem sobre els pronoms per sumar l'enclític al resultat anterior pas a pas
    for pronom in pronoms:
        enclitic = forma_enclitica(pronom, paraula_actual)
        silabes_actuals = calcular_silabes(silabes_actuals, paraula_actual, enclitic)
        paraula_actual = escriure(paraula_actual, enclitic)

    return {
        "paraula": paraula_actual,
        "codi": construir_codi(forma_verbal, persona, pronoms),
        "silabes": silabes_actuals
    }