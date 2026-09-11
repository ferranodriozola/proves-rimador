"""
Quins pronoms admet cada verb, i quins admet cada persona de l'imperatiu.

Aquest mòdul respon una sola pregunta, però és la que decideix tot el volum
de la generació:

    permet(lema, pronom, persona) -> True / False

Les regles i els números surten de pronoms/pla_un_pronom.md (§1, §2 i §3.4),
i les decisions P1-P6 hi estan totes aplicades.

No sap res d'ortografia ni de fonètica: d'això se n'encarrega enclisi.py.
"""

import json
import os
import sys
from collections import Counter
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# verbs_anotats_num.json és a pronoms/docs/, no pas al costat d'aquest fitxer.
FITXER_VERBS = os.path.join(os.path.dirname(BASE_DIR), "docs", "verbs_anotats_num.json")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
import enclisi
from enclisi import ORDRE_PRONOMS   # l'ordre viu en un sol lloc


# ----------------------------------------------------------- classes de verb

SENSE_INFO = "sense_info"      # el DIEC no en diu res
INHERENT   = "inherent"        # totes les construccions són pronominals
TRANSITIU  = "transitiu"       # té alguna construcció transitiva no pronominal
INTR_PRON  = "intr_pron"       # intransitiu, però amb construcció pronominal
INTR_PUR   = "intr_pur"        # intransitiu i prou


# -------------------------------------------------------- grups de pronoms

# Datius (em/et/ens/us/li/els) + hi + en: oberts a tots els verbs.
# Els quatre primers són alhora acusatius, però com que són EL MATEIX string
# per a totes dues funcions i el datiu és obert, la unió mana i la restricció
# de transitivitat hi queda inoperant (pla_un_pronom.md §1).
UNIVERSALS = ["em", "et", "ens", "us", "li", "els", "hi", "en"]

# Els únics pronoms sense cap ús datiu: aquests sí que demanen verb transitiu.
ACUSATIUS = ["el", "la", "les", "ho"]

# El reflexiu de 3a. Demana verb transitiu o pronominal, mai intransitiu pur:
# qualsevol transitiu es pot reflexivitzar (rentar-se) o portar el 'se'
# impersonal (vendre's), però *ploure's o *abastar-se no existeixen.
REFLEXIU = ["es"]

# La casella del reflexiu, amb totes les persones. És l'únic que admeten els
# verbs inherentment pronominals: penedir-me/-te/-se/-nos/-vos.
SLOT_REFLEXIU = ["es", "et", "us", "em", "ens"]


# ------------------------------------------- matrius de concordança (P6)

# Imperatiu: un pronom de 1a/2a persona només és vàlid si el seu referent
# COINCIDEIX exactament amb el subjecte (lectura reflexiva) o n'és DISJUNT.
# El solapament parcial és agramatical: *cantem-me (jo soc dins de nosaltres).
# Els altres pronoms (li, els, el, la, les, ho, hi, en) no hi surten perquè
# el seu referent és sempre de 3a persona o no personal: mai no solapa.
MATRIU_PERSONA = {
    "02S": {"em": True,  "ens": True, "et": True,  "us": False, "es": False},
    "01P": {"em": False, "ens": True, "et": True,  "us": True,  "es": False},
    "02P": {"em": True,  "ens": True, "et": False, "us": True,  "es": False},
    "03S": {"em": True,  "ens": True, "et": False, "us": False, "es": True},
    "03P": {"em": True,  "ens": True, "et": False, "us": False, "es": True},
}

# Els verbs inherentment pronominals no tenen lectura de datiu ni d'acusatiu:
# l'únic pronom possible és el reflexiu, i a l'imperatiu el subjecte ja el fixa.
# Per això *penedeix-me és incorrecte i penedeix-te no (pla_un_pronom.md §2.4).
REFLEXIU_EXACTE = {"02S": "et", "01P": "ens", "02P": "us", "03S": "es", "03P": "es"}


# ------------------------------------------------------------ càrrega i parse

_verbs = None      # lema -> classe
_amb_cd = None     # lemes amb ALGUNA construcció transitiva, pronominal o no


def _construccions(categories):
    """
    Descompon les categories del DIEC en construccions atòmiques.

    'v. tr. i intr. pron.' declara DUES construccions ('tr' i 'intr. pron'),
    no una de sola, i això canvia la classificació del verb.
    """
    out = set()
    for cat in categories:
        cat = cat.replace("v.", "").strip(" .")
        for tros in cat.split(" i "):
            tros = tros.strip().rstrip(".")
            if tros:
                out.add(tros)
    return out


def _es_transitiva(construccio):
    """
    Si una construcció atòmica és transitiva. 'tr' i 'tr. pron' sí; 'intr',
    'intr. pron', 'aux'... no (compte: "intr" conté "tr" com a substring).
    """
    return construccio.split()[0].rstrip(".") == "tr"


def classificar(categories):
    """De les categories del DIEC a una de les 5 classes."""
    cs = _construccions(categories)
    if not cs:
        return SENSE_INFO
    if all("pron" in c for c in cs):
        return INHERENT
    if any(c == "tr" for c in cs):
        return TRANSITIU
    if any("pron" in c for c in cs):
        return INTR_PRON
    return INTR_PUR


def carregar(ruta=None):
    """Llegeix verbs_anotats_num.json i classifica tots els verbs."""
    global _verbs, _amb_cd
    if _verbs is not None and ruta is None:
        return _verbs
    with open(ruta or FITXER_VERBS, "r", encoding="utf-8") as f:
        dades = json.load(f)
    _verbs = {verb: classificar(info.get("categories", []))
              for verb, info in dades.items()}
    _amb_cd = {verb for verb, info in dades.items()
               if any(_es_transitiva(c)
                      for c in _construccions(info.get("categories", [])))}
    return _verbs


def classe(lema):
    """Classe d'un lema. Un lema desconegut es tracta com si no en sabéssim res."""
    return carregar().get(lema, SENSE_INFO)


def admet_cd(lema):
    """
    Si el verb té ALGUNA construcció transitiva, encara que sigui pronominal.

    Per a les altres classes no aporta res (un TRANSITIU ja té els acusatius
    i un INTR_PUR no en tindrà mai), però separa els 13 inherents que el DIEC
    dona com a 'v. tr. pron.' (endur, empassar, aparroquianar...) dels 379
    que són 'v. intr. pron.': només aquells poden dur un CD de 2n pronom.
    """
    carregar()
    return lema in _amb_cd


# --------------------------------------------------------- què admet cada verb

@lru_cache(maxsize=None)      # només hi ha 9.016 lemes i es consulten milions de cops
def pronoms_permesos(lema):
    """
    Els pronoms que admet aquest verb, sense mirar encara la persona.
    Retornats en l'ordre gramatical de col·locació.
    """
    cl = classe(lema)

    # --- P1: verbs sense informació al DIEC (413 no trobats + 9 sense
    # categories = 422). De moment se salten i no generen res, per no
    # inventar-los la transitivitat. Si algun dia es decideix una altra
    # cosa, és aquest 'if' i prou: retornar UNIVERSALS els donaria els
    # datius, 'hi' i 'en'; retornar la llista sencera els tractaria com
    # a transitius.
    if cl == SENSE_INFO:
        return []
    # --- fi de P1

    if cl == INHERENT:
        permesos = SLOT_REFLEXIU
    elif cl == TRANSITIU:
        permesos = UNIVERSALS + ACUSATIUS + REFLEXIU
    elif cl == INTR_PRON:
        permesos = UNIVERSALS + REFLEXIU
    else:                                   # INTR_PUR
        permesos = UNIVERSALS

    return _ordenar(permesos)


def _ordenar(pronoms):
    conjunt = set(pronoms)
    return [p for p in ORDRE_PRONOMS if p in conjunt]


def permet(lema, pronom, persona=None):
    """
    La pregunta que fa servir el generador.

    persona: None per a infinitiu i gerundi (el subjecte no està fixat i no
             hi ha concordança que valgui); '02S'/'01P'/'02P'/'03S'/'03P'
             per a l'imperatiu.
    """
    if pronom not in pronoms_permesos(lema):
        return False

    if persona is None:
        return True

    if classe(lema) == INHERENT:
        # només el reflexiu que concorda amb el subjecte
        return pronom == REFLEXIU_EXACTE[persona]

    return MATRIU_PERSONA[persona].get(pronom, True)


# --------------------------------------------------- Quadre 8.9: 2 pronoms
#
# Transcripció literal del "Quadre 8.9 — Combinacions binàries de pronoms
# febles" (font aportada per l'usuari, agost del 2026): totes les parelles
# de pronoms que existeixen a la llengua, amb la seva forma escrita exacta
# darrere del verb. Substitueix qualsevol algorisme derivat: on el quadre
# dona una resposta, la resposta és la del quadre, no la que es dedueixi
# per lògica.
#
# Cada clau és (primer_pronom, segon_pronom). "els" com a primer pronom es
# desdobla en dues claus ("els_dat", "els_ac") perquè es comporten diferent
# (només el datiu admet les 7 columnes; l'acusatiu només 'hi'/'en'), encara
# que siguin la mateixa paraula i el mateix codi de sortida (LS).
#
# El valor és (escrit, (fonema1, fonema2)): la fonètica va PARTIDA en els dos
# pronoms a posta, perquè enclisi._generar_forma_2() hi pugui aplicar el
# sàndhi al límit que hi ha entre ells (los+hi -> /luzi/, com digues-hi
# -> /dˈiɣəzi/ amb 1 pronom). Quan la fila del primer pronom varia segons si
# el que precedeix acaba en vocal o consonant (us, ens, els_dat, els_ac --
# exactament les mateixes 4 files que ja ho fan per a 1 sol pronom a
# ENCLISI), tots dos camps són una parella (consonant, vocal).
#
# El quadre només dona l'ortografia, no l'AFI: els fragments són els mateixos
# que ja fa servir FONEMA per a 1 pronom, més uns quants de nous per a les
# formes "nues" (sense elidir) que apareixen com a segon pronom darrere d'un
# primer pronom acabat en consonant -- 'los-EN' es pronuncia /luzən/, no
# /lusnə/, perquè "en" hi manté la seva forma lliure, no la lligada "-ne"
# (es veu igual a les 4 files on "en"/"el"/"els" hi surten com a 2n pronom
# rere consonant: us, ens, els_dat, els_ac).
_F = enclisi.FONEMA

# fragments nous: formes "nues" (article/pronom sol, no lligat) i les
# consonants soltes de es/et/em elidits davant hi/ho.
_S, _T, _M = "s", "t", "m"
_EN_NU, _EL_NU, _ELS_NU = "ən", "əl", "əls"
_EM_NU, _ET_NU, _ENS_NU = "əm", "ət", "əns"

PARELLES = {
    # --- es (sempre "-se", excepte elisió pròpia davant hi/ho) ---
    ("es", "hi"):  ("-s'hi",   (_S, _F["-hi"])),
    ("es", "en"):  ("-se'n",   (_F["-se"], _F["'n"])),
    ("es", "ho"):  ("-s'ho",   (_S, _F["-ho"])),
    ("es", "les"): ("-se-les", (_F["-se"], _F["-les"])),
    ("es", "la"):  ("-se-la",  (_F["-se"], _F["-la"])),
    ("es", "els"): ("-se'ls",  (_F["-se"], _F["'ls"])),
    ("es", "el"):  ("-se'l",   (_F["-se"], _F["'l"])),
    ("es", "li"):  ("-se-li",  (_F["-se"], _F["-li"])),
    ("es", "ens"): ("-se'ns",  (_F["-se"], _F["'ns"])),
    ("es", "em"):  ("-se'm",   (_F["-se"], _F["'m"])),
    ("es", "us"):  ("-se-us",  (_F["-se"], _F["-us"])),
    ("es", "et"):  ("-se't",   (_F["-se"], _F["'t"])),

    # --- et (mateix patró que es) ---
    ("et", "hi"):  ("-t'hi",   (_T, _F["-hi"])),
    ("et", "en"):  ("-te'n",   (_F["-te"], _F["'n"])),
    ("et", "ho"):  ("-t'ho",   (_T, _F["-ho"])),
    ("et", "les"): ("-te-les", (_F["-te"], _F["-les"])),
    ("et", "la"):  ("-te-la",  (_F["-te"], _F["-la"])),
    ("et", "els"): ("-te'ls",  (_F["-te"], _F["'ls"])),
    ("et", "el"):  ("-te'l",   (_F["-te"], _F["'l"])),
    ("et", "li"):  ("-te-li",  (_F["-te"], _F["-li"])),
    ("et", "ens"): ("-te'ns",  (_F["-te"], _F["'ns"])),
    ("et", "em"):  ("-te'm",   (_F["-te"], _F["'m"])),

    # --- em (mateix patró que es/et) ---
    ("em", "hi"):  ("-m'hi",   (_M, _F["-hi"])),
    ("em", "en"):  ("-me'n",   (_F["-me"], _F["'n"])),
    ("em", "ho"):  ("-m'ho",   (_M, _F["-ho"])),
    ("em", "les"): ("-me-les", (_F["-me"], _F["-les"])),
    ("em", "la"):  ("-me-la",  (_F["-me"], _F["-la"])),
    ("em", "els"): ("-me'ls",  (_F["-me"], _F["'ls"])),
    ("em", "el"):  ("-me'l",   (_F["-me"], _F["'l"])),
    ("em", "li"):  ("-me-li",  (_F["-me"], _F["-li"])),

    # --- us (varia amb el verb: -vos/-us; el 2n pronom hi va "nu") ---
    ("us", "hi"):  (("-vos-hi", "-us-hi"),   ((_F["-vos"], _F["-hi"]), (_F["-us"], _F["-hi"]))),
    ("us", "en"):  (("-vos-en", "-us-en"),   ((_F["-vos"], _EN_NU),    (_F["-us"], _EN_NU))),
    ("us", "ho"):  (("-vos-ho", "-us-ho"),   ((_F["-vos"], _F["-ho"]), (_F["-us"], _F["-ho"]))),
    ("us", "les"): (("-vos-les", "-us-les"), ((_F["-vos"], _F["-les"]), (_F["-us"], _F["-les"]))),
    ("us", "la"):  (("-vos-la", "-us-la"),   ((_F["-vos"], _F["-la"]), (_F["-us"], _F["-la"]))),
    ("us", "els"): (("-vos-els", "-us-els"), ((_F["-vos"], _ELS_NU),   (_F["-us"], _ELS_NU))),
    ("us", "el"):  (("-vos-el", "-us-el"),   ((_F["-vos"], _EL_NU),    (_F["-us"], _EL_NU))),
    ("us", "li"):  (("-vos-li", "-us-li"),   ((_F["-vos"], _F["-li"]), (_F["-us"], _F["-li"]))),
    ("us", "ens"): (("-vos-ens", "-us-ens"), ((_F["-vos"], _ENS_NU),   (_F["-us"], _ENS_NU))),
    ("us", "em"):  (("-vos-em", "-us-em"),   ((_F["-vos"], _EM_NU),    (_F["-us"], _EM_NU))),

    # --- ens (varia amb el verb: -nos/'ns; el 2n pronom hi va "nu") ---
    ("ens", "hi"):  (("-nos-hi", "'ns-hi"),   ((_F["-nos"], _F["-hi"]), (_F["'ns"], _F["-hi"]))),
    ("ens", "en"):  (("-nos-en", "'ns-en"),   ((_F["-nos"], _EN_NU),    (_F["'ns"], _EN_NU))),
    ("ens", "ho"):  (("-nos-ho", "'ns-ho"),   ((_F["-nos"], _F["-ho"]), (_F["'ns"], _F["-ho"]))),
    ("ens", "les"): (("-nos-les", "'ns-les"), ((_F["-nos"], _F["-les"]), (_F["'ns"], _F["-les"]))),
    ("ens", "la"):  (("-nos-la", "'ns-la"),   ((_F["-nos"], _F["-la"]), (_F["'ns"], _F["-la"]))),
    ("ens", "els"): (("-nos-els", "'ns-els"), ((_F["-nos"], _ELS_NU),   (_F["'ns"], _ELS_NU))),
    ("ens", "el"):  (("-nos-el", "'ns-el"),   ((_F["-nos"], _EL_NU),    (_F["'ns"], _EL_NU))),
    ("ens", "li"):  (("-nos-li", "'ns-li"),   ((_F["-nos"], _F["-li"]), (_F["'ns"], _F["-li"]))),

    # --- li (general): només en/ho/hi es queden amb "li"; el/la/els/les
    # es transformen (vegeu parella_efectiva més avall) ---
    ("li", "hi"): ("-li-hi", (_F["-li"], _F["-hi"])),
    ("li", "en"): ("-li'n",  (_F["-li"], _F["'n"])),
    ("li", "ho"): ("-li-ho", (_F["-li"], _F["-ho"])),

    # --- els datiu (com "li" per a 7 columnes, sense transformar-se) ---
    ("els_dat", "hi"):  (("-los-hi", "'ls-hi"),   ((_F["-los"], _F["-hi"]), (_F["'ls"], _F["-hi"]))),
    ("els_dat", "en"):  (("-los-en", "'ls-en"),   ((_F["-los"], _EN_NU),    (_F["'ls"], _EN_NU))),
    ("els_dat", "ho"):  (("-los-ho", "'ls-ho"),   ((_F["-los"], _F["-ho"]), (_F["'ls"], _F["-ho"]))),
    ("els_dat", "les"): (("-los-les", "'ls-les"), ((_F["-los"], _F["-les"]), (_F["'ls"], _F["-les"]))),
    ("els_dat", "la"):  (("-los-la", "'ls-la"),   ((_F["-los"], _F["-la"]), (_F["'ls"], _F["-la"]))),
    ("els_dat", "els"): (("-los-els", "'ls-els"), ((_F["-los"], _ELS_NU),   (_F["'ls"], _ELS_NU))),
    ("els_dat", "el"):  (("-los-el", "'ls-el"),   ((_F["-los"], _EL_NU),    (_F["'ls"], _EL_NU))),

    # --- el (sempre elidit "l'", davant hi/en, independent del verb) ---
    ("el", "hi"): ("-l'hi", (_F["'l"], _F["-hi"])),
    ("el", "en"): ("-l'en", (_F["'l"], _EN_NU)),

    # --- els acusatiu (com "el" per a la forma, però varia amb el verb) ---
    ("els_ac", "hi"): (("-los-hi", "'ls-hi"), ((_F["-los"], _F["-hi"]), (_F["'ls"], _F["-hi"]))),
    ("els_ac", "en"): (("-los-en", "'ls-en"), ((_F["-los"], _EN_NU),    (_F["'ls"], _EN_NU))),

    # --- la (mai s'elideix ella mateixa) ---
    ("la", "hi"): ("-la-hi", (_F["-la"], _F["-hi"])),
    ("la", "en"): ("-la'n",  (_F["-la"], _F["'n"])),

    # --- les (mai s'elideix) ---
    ("les", "hi"): ("-les-hi", (_F["-les"], _F["-hi"])),
    ("les", "en"): ("-les-en", (_F["-les"], _EN_NU)),

    # --- en ---
    ("en", "hi"): ("-n'hi", (_F["'n"], _F["-hi"])),
}

# li + el/la/els/les es transforma: el CD passa davant i "li" es converteix
# en "hi" (porta-l'hi, la hi, els hi, les hi -- pla_dos_pronoms.md). La
# parella EFECTIVA per triar ortografia/fonètica és una altra clau de
# PARELLES; el codi de sortida, en canvi, sempre es construeix amb la
# parella ORIGINAL (li, X), no amb l'efectiva (pla_un_pronom.md §4).
TRANSFORMACIO_LI = {"el": "el", "la": "la", "els": "els_ac", "les": "les"}


def parella_efectiva(pronom1, pronom2):
    """
    La clau real a PARELLES d'una parella gramatical.

    Resol les dues indireccions del quadre: la transformació li+CD -> CD+hi
    (li+el -> ("el", "hi"), que és "-l'hi") i la distinció interna
    els_dat/els_ac, que no existeix fora d'aquest mòdul.
    """
    if pronom1 == "li" and pronom2 in TRANSFORMACIO_LI:
        return TRANSFORMACIO_LI[pronom2], "hi"
    return ("els_dat" if pronom1 == "els" else pronom1), pronom2


# Les 69 parelles reals del Quadre 8.9 (71 cel·les, -2 pel solapament de
# els_dat/els_ac en "hi"/"en"), amb "els" unificat (el sufix _dat/_ac és
# només una distinció interna d'aquest mòdul) i les 4 combinacions de "li"
# transformades (el/la/els/les) afegides explícitament, ja que no tenen
# clau pròpia a PARELLES -- es resolen per redirecció (parella_efectiva).
PARELLES_VALIDES = sorted(
    {(p1.replace("els_dat", "els").replace("els_ac", "els"), p2)
     for (p1, p2) in PARELLES}
    | {("li", p2) for p2 in TRANSFORMACIO_LI},
    key=lambda par: (ORDRE_PRONOMS.index(par[0]), ORDRE_PRONOMS.index(par[1])))


def permet_parella(lema, pronom1, pronom2, persona=None):
    """
    La pregunta que fa servir el generador de 2 pronoms.

    Heurística d'unió (decidida amb l'usuari, agost del 2026): la parella es
    permet si el verb admet cada pronom per separat, sense dades noves de
    ditransitivitat -- el mateix criteri de sobregeneració que P2/P3 al pla
    d'1 pronom, aplicat ara a parelles.

    Els pronominals inherents en són l'excepció i tenen regla pròpia: amb 1
    pronom no admeten res més que el reflexiu, i si els apliquéssim la unió
    tal qual no arribarien mai a 2 pronoms.
    """
    if (pronom1, pronom2) not in PARELLES_VALIDES:
        return False

    if classe(lema) == INHERENT:
        return _parella_inherent(lema, pronom1, pronom2, persona)

    if not (permet(lema, pronom1, None) and permet(lema, pronom2, None)):
        return False
    if persona is None:
        return True
    # la concordança de persona només afecta el membre de 1a/2a/reflexiu
    for p in (pronom1, pronom2):
        if p in SLOT_REFLEXIU and not permet(lema, p, persona):
            return False
    return True


def _parella_inherent(lema, pronom1, pronom2, persona):
    """
    Els 392 verbs inherentment pronominals, que és el cas que
    pla_un_pronom.md §2.2 reservava justament per a aquesta fase:
    penedir-ne ❌, però penedir-se'n ✅.

    El reflexiu és part del verb i no es pot ometre, o sigui que sempre és el
    PRIMER pronom -- i a l'imperatiu, el que concorda amb el subjecte
    (permet() ja hi aplica REFLEXIU_EXACTE). El SEGON és el que llicenciï la
    construcció: els datius, 'hi' i 'en' com a qualsevol intransitiu
    (queixar-se-li, abalançar-s'hi, adonar-se'n), i un acusatiu només si el
    verb té alguna construcció 'v. tr. pron.' (endur-se'l, empassar-se-la).
    """
    if not permet(lema, pronom1, persona):
        return False
    if pronom2 not in UNIVERSALS and not (pronom2 in ACUSATIUS and admet_cd(lema)):
        return False
    # el 2n pronom no és el reflexiu inherent sinó un datiu: no hi val
    # REFLEXIU_EXACTE, hi val la matriu general (*penedim-nos-em)
    if persona is not None and not MATRIU_PERSONA[persona].get(pronom2, True):
        return False
    return True


# ------------------------------------------------------------------- informes

def verbs_per_pronom():
    """{pronom: set(lemes que l'admeten)}, sense mirar la persona."""
    out = {}
    for lema in carregar():
        for p in pronoms_permesos(lema):
            out.setdefault(p, set()).add(lema)
    return out


def resum():
    """Recompte de verbs per classe, per comprovar que quadra amb el pla."""
    return Counter(carregar().values())


if __name__ == "__main__":
    import sys
    sys.path.insert(0, BASE_DIR)

    print("VERBS PER CLASSE")
    noms = {SENSE_INFO: "sense informació (P1: es salten)",
            INHERENT: "pronominal inherent",
            TRANSITIU: "transitiu (± pronominal)",
            INTR_PRON: "intransitiu + pronominal",
            INTR_PUR: "intransitiu pur"}
    r = resum()
    for cl in (SENSE_INFO, INHERENT, TRANSITIU, INTR_PRON, INTR_PUR):
        exemple = next((v for v, c in carregar().items() if c == cl), "")
        n_pron = len(pronoms_permesos(exemple)) if exemple else 0
        print(f"  {noms[cl]:34s} {r[cl]:6d} verbs  {n_pron:2d} pronoms")
    print(f"  {'TOTAL':34s} {sum(r.values()):6d}")

    print("\nVERBS PER PRONOM")
    for p, s in sorted(verbs_per_pronom().items(), key=lambda x: -len(x[1])):
        print(f"  {p:5s} {len(s):6d}")
