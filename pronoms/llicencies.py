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
FITXER_VERBS = os.path.join(BASE_DIR, "verbs_anotats_num.json")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
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
    global _verbs
    if _verbs is not None and ruta is None:
        return _verbs
    with open(ruta or FITXER_VERBS, "r", encoding="utf-8") as f:
        dades = json.load(f)
    _verbs = {verb: classificar(info.get("categories", []))
              for verb, info in dades.items()}
    return _verbs


def classe(lema):
    """Classe d'un lema. Un lema desconegut es tracta com si no en sabéssim res."""
    return carregar().get(lema, SENSE_INFO)


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
