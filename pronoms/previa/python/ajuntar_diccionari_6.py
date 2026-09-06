"""
El diccionari de producció + totes les formes amb pronom, en un sol fitxer.

    python3 ajuntar_diccionari_6.py

    diccionaris/diccionari.5.2.3.txt        619.783 línies
  + pronoms/txt_fets/1_pronom/*.txt         626.837 línies
  + pronoms/txt_fets/2_pronoms/*.txt      2.779.550 línies
  ------------------------------------------------------
  = diccionaris/diccionari.6.txt         ~4.026.170 línies

L'última passa del workflow pronoms.yml, que abans hi executa els dos
generadors. Aquí no s'hi genera cap forma: només s'ajunta i s'ordena el que
els generadors acaben de deixar a txt_fets/.

NO hi ha cap fitxer intermedi. Les línies dels 82 fitxers de txt_fets/ no
passen mai per un "tot.txt" amb només les rimes de pronom: es llegeixen, es
barregen amb les del diccionari i surten directament al fitxer final. És a
posta -- un fitxer intermedi de 280 MB és mig minut i molt de disc per no
guardar res que ningú no torni a llegir.

    (l'ajuntar_i_comptar_rimes.py, que és l'estudi de què passaria amb les
    rimes, sí que se'l fa i el deixa a txt_fets/tot.txt. Són dos programes
    independents: aquest no el llegeix ni el necessita, i el fitxers_font()
    de sota està fet justament per no ensopegar-hi.)

ORDRE ALFABÈTIC amb à=a=À=A, è=é=e=È=É=E, ç=c, ï=i...: s'ordena per la
paraula (camp 0) sense accents ni majúscules, i les que empaten es desfan amb
la paraula tal com s'escriu. Vegeu clau_ordenacio().
"""

import os
import sys
import unicodedata

# .parent perquè aquest fitxer viu a pronoms/python/ i txt_fets/ és a pronoms/.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRONOMS_DIR = os.path.dirname(BASE_DIR)
DIR_TXT = os.path.join(PRONOMS_DIR, "txt_fets")

# Quin diccionari és el base i quin es publica ho diu config.py, que és l'únic
# lloc del repositori que ho diu.
sys.path.insert(0, os.path.join(PRONOMS_DIR, "..", "diccionaris", "python"))
import config

FITXER_BASE = config.CAMI_BASE
FITXER_SORTIDA = config.CAMI_PUBLICAT

CAMPS = 10


def mil(n):
    """4025866 -> '4.025.866', com els números de la documentació."""
    return f"{n:,}".replace(",", ".")


# ------------------------------------------------------- d'on surten les línies

def fitxers_font():
    """
    Els .txt de les SUBCARPETES de txt_fets/ (1_pronom/ i 2_pronoms/).

    Només mira dins de subcarpetes, i això no és cap detall: a txt_fets/
    mateix hi ha el tot.txt de l'ajuntar_i_comptar_rimes.py, que ja és la
    suma de tots aquests fitxers. Si s'hi colés, cada forma amb pronom
    sortiria DUES vegades al diccionari.6.txt, i el col_3_prova_v.6.txt que hi
    ha al costat (que només té una columna) faria petar la comprovació de
    camps de llegir_linies().
    """
    trobats = []
    for nom in sorted(os.listdir(DIR_TXT)):
        carpeta = os.path.join(DIR_TXT, nom)
        if not os.path.isdir(carpeta):
            continue
        for arrel, _, noms in os.walk(carpeta):
            trobats += [os.path.join(arrel, n) for n in noms if n.endswith(".txt")]
    if not trobats:
        raise SystemExit(
            f"No hi ha cap .txt a les subcarpetes de {DIR_TXT}.\n"
            "Executa abans generar_tot_1_pronom.py i generar_tot_2_pronoms.py."
        )
    return sorted(trobats)


def llegir_linies(cami):
    """
    Les línies d'un fitxer, sense les buides i amb els camps comptats.

    La comprovació dels 10 camps és barata i atura de seguida un fitxer que
    no tingui el format del diccionari. Sense ella, una línia dolenta no es
    veuria fins que el web no sabés llegir el diccionari.
    """
    try:
        with open(cami, "r", encoding="utf-8") as f:
            linies = [linia for linia in f.read().splitlines() if linia]
    except FileNotFoundError:
        raise SystemExit(f"No s'ha trobat el fitxer: {cami}")

    dolentes = [linia for linia in linies if linia.count("$") != CAMPS - 1]
    if dolentes:
        raise SystemExit(
            f"{cami}: {len(dolentes)} línies no tenen {CAMPS} camps separats "
            f"per '$', per exemple: {dolentes[0]!r}"
        )
    return linies


# ------------------------------------------------------------ l'ordre alfabètic

def clau_ordenacio(linia):
    """
    Ordena per la paraula (camp 0) amb à=a=À=A, è=é=e=È=É=E, ç=c, ï=i...

    Com s'hi arriba: NFD parteix cada lletra accentuada en lletra + accent
    (à -> a + ¨`), i llavors es llencen totes les marques (categoria Mn) i
    queda la lletra pelada. El .lower() de davant iguala majúscules i
    minúscules, que és l'altra meitat de la regla.

    Desempat amb la paraula original: les que només es diferencien per
    l'accent o la caixa han de sortir sempre en el mateix ordre i no pas en
    l'ordre en què s'han llegit els fitxers. Deixa 'Índia' abans que 'índia',
    com ja ho fa el diccionari d'ara.

    Les paraules IDÈNTIQUES (homògrafes de lemes diferents) es queden en
    l'ordre d'entrada, perquè el sort de Python és estable: primer la del
    diccionari base i després les formes amb pronom, per ordre de fitxer.
    """
    paraula = linia.split("$", 1)[0]
    sense_accents = "".join(
        c for c in unicodedata.normalize("NFD", paraula.lower())
        if unicodedata.category(c) != "Mn"
    )
    return (sense_accents, paraula)


# ---------------------------------------------------------------------- la feina

def ajuntar(base=FITXER_BASE, sortida=FITXER_SORTIDA, fitxers=None):
    if os.path.abspath(base) == os.path.abspath(sortida):
        raise SystemExit("La sortida no pot ser el mateix fitxer que la base.")
    if fitxers is None:
        fitxers = fitxers_font()

    linies = llegir_linies(base)
    print(f"  {os.path.basename(base):32s} {mil(len(linies)):>12s} línies")
    velles = len(linies)

    for cami in fitxers:
        noves = llegir_linies(cami)
        linies += noves
    print(f"  {f'{len(fitxers)} fitxers de txt_fets/':32s}"
          f" {mil(len(linies) - velles):>12s} línies")

    linies.sort(key=clau_ordenacio)

    # Línia per línia i no pas amb un "\n".join(linies): el join faria una
    # sola cadena de 300 MB al costat de la llista que ja tenim a la memòria.
    with open(sortida, "w", encoding="utf-8") as f:
        for linia in linies:
            f.write(linia)
            f.write("\n")

    return len(linies), velles


def main():
    # Si l'interruptor publica el diccionari base, aquest script no té cap
    # feina: no hi ha cap v.6 a fer, i escriure'l voldria dir sobreescriure el
    # diccionari que s'edita a mà amb ell mateix més les formes amb pronom.
    if not config.CAL_V6:
        raise SystemExit(
            f"config.py publica {config.DICCIONARI_PUBLICAT}, que és el "
            "diccionari base:\nno hi ha cap diccionari amb pronoms per fer."
        )

    print(f"Ajuntant a {os.path.basename(FITXER_SORTIDA)}:\n")
    total, velles = ajuntar()
    mida = os.path.getsize(FITXER_SORTIDA) / 1e6
    print(f"\nFet! {mil(total)} línies ({mil(velles)} del diccionari + "
          f"{mil(total - velles)} amb pronom)")
    print(f"     {os.path.relpath(FITXER_SORTIDA, BASE_DIR)}, {mida:,.0f} MB,"
          " ordenat alfabèticament")


if __name__ == "__main__":
    main()
