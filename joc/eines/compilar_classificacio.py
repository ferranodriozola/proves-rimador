# Compilador de la classificacio (leaderboard) del joc.
#
# Funciona igual que stats/stats.py: llegeix el full de calcul de Google publicat
# en CSV (on el Google Apps Script va apuntant les puntuacions que envia la gent)
# i n'escriu un ranquing net a joc/dades/classificacio.json, que es el que mostra
# la pantalla de classificacio del joc.
#
# Aqui es on es decideix de veritat que s'accepta: es validen els sobrenoms, es
# treuen els repetits i, de cada persona i modalitat, es guarda nomes la millor
# puntuacio.
#
# QUE EN SURT:
#   modalitats  ranquing de cada mode|dificultat|segons
#   diaria      ranquing de cada dia i dificultat, amb la paraula que tocava. El
#               joc el fa servir a la pestanya "Paraula del dia" de la pantalla
#               de classificacio (vegeu pintarDiaria a joc/js/ui.js).
#
# EL DIALECTE NO PARTEIX EL RANQUING. Es guarda al full i viatja amb cada
# entrada, i el joc el posa entre parentesis a cada fila, pero no fa taules a
# part: quatre classificacions de quatre persones cadascuna no son cap
# classificacio. Aixi tothom surt a la mateixa taula i es veu en que jugava.
#
# LES DUES DATES: el full en guarda dues (vegeu apps_script_classificacio.gs).
# La "Data" es quan va arribar l'enviament i la "DataPartida" de quin dia era la
# partida. El ranquing per dia agrupa per DataPartida, que es la que ho diu be:
# qui juga a les 23.55 i ho envia a les 00.05 ha jugat la paraula d'ahir.
#
# Execucio (a ma, quan es vulgui refrescar el ranquing):
#   python joc/eines/compilar_classificacio.py

import json
import os
import re
import ssl
import unicodedata
from datetime import datetime

# pandas nomes fa falta quan hi ha backend configurat. Si no hi es (per exemple
# en local, abans de muntar el full), l'script encara ha de poder escriure una
# classificacio buida, o sigui que no petem si falta.
try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

ssl._create_default_https_context = ssl._create_unverified_context

# --- Configuracio -----------------------------------------------------------

# El full publicat en CSV (Fitxer > Comparteix > Publica a la web > CSV). Mentre
# no hi sigui, l'script escriu una classificacio buida perque la pagina no peti.
URL_FULL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRwuOIIAtFLHbvQpMS_gHPTBOyge4TCoXb--viKHL3tTux1qkDgv9evA_wy2aYVzGKXTDfEefqtXC4l/pub?output=csv"

# Quantes posicions guardem per modalitat.
TOP_N = 20

# Quants dies enrere de paraula del dia es publiquen. Amb 30 la pantalla te un
# mes per mirar i el JSON no creix sense aturador.
DIES_DIARIA = 30

# Mateixes regles que joc/js/classificacio.js: el navegador ja filtra, pero aqui
# ho tornem a comprovar perque es l'ultima porta abans de publicar.
LLARG_MIN, LLARG_MAX = 3, 16
CARACTERS_OK = re.compile(r"^[^\W_]+[\w .\-]*$", re.UNICODE)
PARAULES_VETADES = [
    "merda", "puta", "puto", "collo", "cabro", "fill de",
    "nazi", "hitler", "admin", "moderador",
]

ARREL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_JSON = os.path.join(ARREL, "joc", "dades", "classificacio.json")

NOM_MODE = {"illimitat": "Il·limitat", "diaria": "Paraula del dia"}
NOM_DIFICULTAT = {"facil": "Fàcil", "dificil": "Difícil"}
NOM_TEMPS = {"45": "Llampec", "60": "1 minut", "90": "Estàndard", "180": "Lent"}
# Els noms dels dialectes no son aqui: al JSON hi va el codi i el joc el
# tradueix amb el que digui joc/dades/versions.json (vegeu nomDialecte a
# joc/js/ui.js). Aixi els noms es diuen en un sol lloc.

# El dialecte de les files d'abans que se'n pogues triar cap. Es el mateix
# DIALECTE_ANTIC de joc/js/magatzem.js.
DIALECTE_ANTIC = "ca"

# Les columnes que ha de dur el full. Les dues ultimes son les que es van afegir
# quan el joc va passar a tenir dialectes: les files velles no les duen i se'ls
# posa un valor per defecte en comptes de descartar-les.
COLUMNES = ["Data", "Sobrenom", "Mode", "Dificultat", "Segons", "Punts",
            "Paraula", "Usuari"]
COLUMNES_NOVES = {"DataPartida": "", "Dialecte": DIALECTE_ANTIC}


# --- Utilitats --------------------------------------------------------------


def sense_accents(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    ).lower()


def sobrenom_valid(text):
    net = re.sub(r"\s+", " ", str(text).strip())
    if not (LLARG_MIN <= len(net) <= LLARG_MAX):
        return None
    if not CARACTERS_OK.match(net):
        return None
    pla = sense_accents(net)
    if any(mot in pla for mot in PARAULES_VETADES):
        return None
    return net


def titol_modalitat(mode, dificultat, segons):
    parts = [NOM_MODE.get(mode, mode), NOM_DIFICULTAT.get(dificultat, dificultat)]
    if mode != "diaria":
        parts.append(NOM_TEMPS.get(str(segons), f"{segons}s"))
    return " · ".join(parts)


def top_entrades(df):
    """De cada sobrenom, la millor puntuacio; despres, les TOP_N millors."""
    millor = (
        df.sort_values("Punts", ascending=False)
        .drop_duplicates(subset=["clau_persona"], keep="first")
        .head(TOP_N)
    )
    return [
        {
            "sobrenom": fila["Sobrenom"],
            "punts": int(fila["Punts"]),
            "paraula": fila["Paraula"],
            # Viatja amb l'entrada, no amb la taula: el joc el posa entre
            # parentesis a cada fila (vegeu subtitolEntrada a joc/js/ui.js).
            "dialecte": fila["Dialecte"],
            "data": fila["Data"].strftime("%d/%m/%Y") if pd.notna(fila["Data"]) else "",
        }
        for _, fila in millor.iterrows()
    ]


# --- Proces -----------------------------------------------------------------


def classificacio_buida():
    return {
        "actualitzacio": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "modalitats": {},
        "diaria": {},
    }


def main():
    if not URL_FULL_CSV:
        print("URL_FULL_CSV no configurada: escric una classificacio buida.")
        desar(classificacio_buida())
        return
    if pd is None:
        raise SystemExit("Cal instal·lar pandas per compilar el full: pip install pandas")

    df = pd.read_csv(URL_FULL_CSV)

    # Els noms de columna els posa el Google Apps Script. Les que hi ha d'haver
    # sempre, si falten, son un full mal muntat i val mes dir-ho que no pas
    # publicar un ranquing a mitges.
    falten = [c for c in COLUMNES if c not in df.columns]
    if falten:
        raise SystemExit(f"Al full li falten columnes: {', '.join(falten)}. "
                         "Mira les capceleres que demana apps_script_classificacio.gs.")
    # Les noves, en canvi, poden faltar: son files d'abans que el joc tingues
    # dialectes i no s'han de perdre.
    for columna, per_defecte in COLUMNES_NOVES.items():
        if columna not in df.columns:
            print(f"  (el full no té la columna {columna}: hi poso "
                  f"{per_defecte!r} a tot arreu)")
            df[columna] = per_defecte

    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df["Punts"] = pd.to_numeric(df["Punts"], errors="coerce")
    df = df.dropna(subset=["Punts"])
    df["Punts"] = df["Punts"].astype(int)

    for columna in ["Sobrenom", "Mode", "Dificultat", "Segons", "Paraula",
                    "Usuari", "Dialecte", "DataPartida"]:
        df[columna] = df[columna].fillna("").astype(str)

    # Les files velles no duien dialecte: eren totes en central.
    df["Dialecte"] = df["Dialecte"].str.strip().replace({"": DIALECTE_ANTIC, "nan": DIALECTE_ANTIC})

    # El dia de la partida: el que diu el navegador i, si no el diu (files
    # velles), el dia que va arribar l'enviament.
    dia_arribada = df["Data"].dt.strftime("%Y-%m-%d")
    dia_partida = df["DataPartida"].str.strip()
    df["dia"] = dia_partida.where(dia_partida.str.match(r"^\d{4}-\d{2}-\d{2}$"), dia_arribada)

    # Nomes puntuacions amb sobrenom acceptable.
    df["Sobrenom"] = df["Sobrenom"].map(sobrenom_valid)
    df = df.dropna(subset=["Sobrenom"])

    # La "persona" per desduplicar: el sobrenom (en minuscula i sense accents) o,
    # si el tenim, l'identificador d'usuari. Aixi una mateixa persona no ocupa
    # mitja taula amb el mateix nom.
    df["clau_persona"] = df["Usuari"].where(
        df["Usuari"].str.startswith("usr_"), df["Sobrenom"].map(sense_accents)
    )

    resultat = classificacio_buida()

    # Ranquings per modalitat (mode | dificultat | segons). El dialecte no hi
    # entra: tothom qui juga la mateixa modalitat surt a la mateixa taula.
    for (mode, dificultat, segons), grup in df.groupby(
            ["Mode", "Dificultat", "Segons"]):
        clau = f"{mode}|{dificultat}|{segons}"
        resultat["modalitats"][clau] = {
            "titol": titol_modalitat(mode, dificultat, segons),
            "top": top_entrades(grup),
        }

    # Ranquing especial de la paraula del dia, per dia i dificultat. Nomes els
    # DIES_DIARIA ultims dies: es una pantalla per mirar com va anar aquesta
    # setmana, no un arxiu historic.
    #
    # Aqui no hi ha cap "paraula del dia" sola: cada dialecte te la seva (vegeu
    # clauDelDia a joc/js/objectius.js), o sigui que la paraula va a cada
    # entrada, al costat del dialecte, i no pas a la capcalera del dia.
    diaria = df[(df["Mode"] == "diaria") & df["dia"].notna()].copy()
    if not diaria.empty:
        dies = sorted(diaria["dia"].unique(), reverse=True)[:DIES_DIARIA]
        diaria = diaria[diaria["dia"].isin(dies)]
        for dia, grup_dia in diaria.groupby("dia"):
            entrada = resultat["diaria"].setdefault(dia, {})
            for dificultat, grup in grup_dia.groupby("Dificultat"):
                entrada[dificultat] = top_entrades(grup)

    desar(resultat)
    n = sum(len(m["top"]) for m in resultat["modalitats"].values())
    print(f"Fet: {len(resultat['modalitats'])} modalitats, {n} puntuacions publicades, "
          f"{len(resultat['diaria'])} dies de paraula del dia "
          f"(hora: {datetime.now().strftime('%H:%M:%S')}).")


def desar(dades):
    os.makedirs(os.path.dirname(RUTA_JSON), exist_ok=True)
    with open(RUTA_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dades, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
