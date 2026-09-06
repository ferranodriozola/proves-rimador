"""
Ortografia de l'enclisi: verb + pronom feble.

Versió simplificada: només determina com s'escriu gràficament (guionet o apòstrof)
i en genera el codi morfològic. S'ha ignorat tota la lògica de transcripció
fonètica, rimes i síl·labes.
"""

# ---------------------------------------------------------------- alfabets

# Vocals GRÀFIQUES, per decidir guionet o apòstrof. La 'u' en queda fora
# expressament: la regla normativa és "forma plena darrere consonant O DIFTONG",
# i una -u final sempre fa diftong (canteu-me, no *canteu'm).
#
# La dièresi hi ÉS justament perquè marca el contrari: que la vocal no fa
# diftong. Els 396 imperatius de vostè acabats en -ï (actuï, canviï, estudiï)
# acaben en vocal plena i demanen la forma reduïda -- actuï'l, no *actuï-lo.
VOCALS_GRAFIQUES = set("aeioàèéíòóúïü")


# ------------------------------------------------------- taula de l'enclisi

# pronom -> (forma darrere consonant o diftong, forma darrere vocal)
# Verificat contra el quadre normatiu (CPNL, GEIEC 13.4.2); vegeu pla.md §2.1.
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


# Codi de 2 lletres per pronom, tret de la forma enclítica per ser mnemònic i
# no xocar (-ne -> NE, -nos -> NS, -los -> LS). Vegeu pla_un_pronom.md §4.
PRONOM_CODI = {
    "em": "EM", "et": "ET", "es": "ES", "ens": "NS", "us": "US",
    "el": "EL", "la": "LA", "els": "LS", "les": "LE", "li": "LI",
    "en": "NE", "ho": "HO", "hi": "HI",
}


# Ordre gramatical de col·locació, per escriure els codis de 2 pronoms sempre
# igual (pla_un_pronom.md §4). Amb 1 pronom només serveix per ordenar la sortida.
ORDRE_PRONOMS = ["es", "et", "us", "em", "ens", "li", "els",
                 "el", "la", "les", "en", "hi", "ho"]


# ----------------------------------------------------------------- ortografia

def acaba_en_vocal(forma):
    """Regla gràfica de l'enclisi: mira l'última lletra del verb ESCRIT."""
    return forma[-1].lower() in VOCALS_GRAFIQUES


def forma_enclitica(pronom, forma):
    """
    Forma plena (guionet) darrere consonant o diftong; reduïda (apòstrof)
    darrere vocal. 'hi', 'ho', 'la', 'les' i 'li' no tenen forma reduïda.
    """
    plena, reduida = ENCLISI[pronom]
    return reduida if acaba_en_vocal(forma) else plena


def escriure(forma, enclitic):
    """La forma gràfica sencera. L'apòstrof i el guionet ja venen a l'enclític."""
    return forma + enclitic


# ------------------------------------------------------------------- el codi

def construir_codi(forma_verbal, persona, pronoms):
    """
    Codi propi, amplada fixa de 10 caràcters i posicional (pla_un_pronom.md §4):

        W  F  PPP  N  A1A2  B1B2
        0  1  2-4  5  6-7   8-9

    forma_verbal: 'N' infinitiu, 'G' gerundi, 'M' imperatiu
    persona:      None o '000' per a infinitiu/gerundi; '02S'/'01P'/'02P'/'03S'/'03P'
    pronoms:      llista d'1 o 2 pronoms, en ordre gramatical
    """
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
    """Ordre gramatical de col·locació, perquè el codi sigui sempre el mateix."""
    return sorted(pronoms, key=ORDRE_PRONOMS.index)


# ------------------------------------------------------- tot d'una vegada

def generar_forma(forma, pronoms, forma_verbal, persona=None, 
                  transcripcio=None, silabes_base=None):
    """
    S'ha eliminat la necessitat d'introduir paràmetres de fonètica. S'accepten
    per mantenir la compatibilitat amb qui faci la crida, però no s'utilitzen.

    Retorna un dict amb "paraula" i "codi".
    """
    pronoms = ordenar_pronoms(pronoms)
    if len(pronoms) != 1:
        raise ValueError(f"Aquesta versió només accepta 1 pronom. Reburt: {len(pronoms)}")

    enclitic = forma_enclitica(pronoms[0], forma)

    return {
        "paraula": escriure(forma, enclitic),
        "codi": construir_codi(forma_verbal, persona, pronoms),
    }