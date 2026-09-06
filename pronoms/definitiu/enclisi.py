"""
Ortografia de l'enclisi: verb + pronom feble.

Versió basada en regles gramaticals per blocs (1 o 2 pronoms).
Genera el codi morfològic i en calcula el nombre de síl·labes gràfiques.
"""

# ---------------------------------------------------------------- alfabets

VOCALS_GRAFIQUES = set("aeioàèéíòóúïü")

# ------------------------------------------------------- diccionaris base

ENCLISI = {
    # pronom: (darrere_consonant, darrere_vocal)
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

COMBINACIONS_2_PRONOMS = {
    # (p1, p2): (única_opció,)  O BÉ  (darrere_consonant, darrere_vocal)
    
    # Exemples inicials (a punt per ser omplert amb tota la gramàtica):
    ("em", "el"):  ("-me'l",),             # Si és igual per a consonant i vocal
    ("ens", "hi"): ("-nos-hi", "'ns-hi"),  # Si varia segons consonant o vocal
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

def aplicar_1_pronom(forma, pronom):
    """Aplica la regla estàndard per a un sol pronom."""
    plena, reduida = ENCLISI[pronom]
    enclitic = reduida if acaba_en_vocal(forma) else plena
    return forma + enclitic

def aplicar_2_pronoms(forma, p1, p2):
    """
    Aplica les regles gramaticals de 2 pronoms consultant el diccionari.
    Té en compte si hi ha una sola variant comuna o dues de diferenciades.
    """
    parella = (p1, p2)
    vocal = acaba_en_vocal(forma)

    # 1. Comprovem si la parella ja està definida al nostre diccionari
    if parella in COMBINACIONS_2_PRONOMS:
        opcions = COMBINACIONS_2_PRONOMS[parella]
        
        if len(opcions) == 1:
            # Només hi ha una opció (serveix tant per vocal com consonant)
            enclitic = opcions[0]
        else:
            # Hi ha dues opcions: (forma_consonant, forma_vocal)
            forma_consonant, forma_vocal = opcions
            enclitic = forma_vocal if vocal else forma_consonant
            
        return forma + enclitic

    # 2. FALLBACK TEMPORAL (Pla B)
    # Si encara no hem bolcat aquesta parella al diccionari, 
    # ho processem d'un en un perquè el programa no es trenqui.
    forma_parcial = aplicar_1_pronom(forma, p1)
    return aplicar_1_pronom(forma_parcial, p2)


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

    # Ara tractem les mides de pronoms per separat de forma unificada
    if len(pronoms) == 1:
        paraula_actual = aplicar_1_pronom(forma, pronoms[0])
    else:  # Cas de 2 pronoms
        p1, p2 = pronoms[0], pronoms[1]
        paraula_actual = aplicar_2_pronoms(forma, p1, p2)

    return {
        "paraula": paraula_actual,
        "codi": construir_codi(forma_verbal, persona, pronoms),
        "silabes": silabes_base
    }