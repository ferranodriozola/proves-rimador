"""
EINA LOCAL. Passa tots els moviments de la taula i comprova què fa cadascun.

    python3 diccionaris/python/provar.py

Munta un arbre de joguina a /tmp (un diccionari de deu paraules, dos dialectes)
i hi fa córrer el sincronitzar.py de debò, un moviment a cada còpia nova. Sobre
els fitxers de veritat, provar un sol moviment vol dir escriure 100 MB dues
vegades; així són vint-i-quatre proves en un segon.

Qui fa possible això és la variable RIMADOR_ARREL: els scripts la miren per
saber on és l'arrel del repositori (vegeu camins.py) i, si no hi és, la
dedueixen d'on són ells.

Les proves són la taula de moviments: què ha de passar quan s'edita el
diccionari, quan s'edita la col_10, quan s'editen tots dos, quan es reordena,
quan s'afegeix un dialecte i quan el format no és el que ha de ser.
"""
import os, shutil, subprocess, sys, tempfile

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(SCRIPTS))

PARAULES = [
    ("gos", "gos", "NCMS000", "1", "ɡˈos", "ɡˈos"),
    ("gossos", "gos", "NCMP000", "2", "ɡˈosus", "ɡˈosos"),
    ("gat", "gat", "NCMS000", "1", "ɡˈat", "ɡˈat"),
    ("gats", "gat", "NCMP000", "1", "ɡˈats", "ɡˈats"),
    ("casa", "casa", "NCFS000", "2", "kˈazə", "kˈaza"),
    ("cases", "casa", "NCFP000", "2", "kˈazəs", "kˈazes"),
    ("be", "be", "NCMS000", "1", "bˈɛ", "bˈe"),
    ("be", "be", "NCMS000", "1", "bˈe", "bˈe"),
    ("pare", "pare", "NCMS000", "2", "pˈaɾə", "pˈaɾe"),
    ("mare", "mare", "NCFS000", "2", "mˈaɾə", "mˈaɾe"),
]
CODIS = ["ca", "va"]


def muntar(carpeta):
    dicc = os.path.join(carpeta, "diccionaris")
    os.makedirs(os.path.join(dicc, "separat"), exist_ok=True)
    files = [[p, l, c, s, "NO", "NO", "NO"] for p, l, c, s, _, _ in PARAULES]
    with open(os.path.join(dicc, "diccionari.5.2.3.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join("$".join(fila) for fila in files) + "\n")
    for n, camp in ((0, 0), (1, 1), (2, 2)):
        with open(os.path.join(dicc, "separat", f"col_{n}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(fila[camp] for fila in files))
    linies = []
    for p, l, c, s, ca, va in PARAULES:
        linies.append(f"{p} € {l} € {c} €$ca$ {ca} €$va$ {va}")
    with open(os.path.join(dicc, "col_10.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linies))
    for i, codi in enumerate(CODIS):
        d = os.path.join(carpeta, "dialectes_col", codi)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"col_9_transcripcio_{codi}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(p[4 + i] for p in PARAULES))


def llegir(carpeta, relatiu):
    with open(os.path.join(carpeta, relatiu), encoding="utf-8") as f:
        t = f.read()
    return t[:-1].split("\n") if t.endswith("\n") else t.split("\n")


def escriure(carpeta, relatiu, linies, salt=False):
    with open(os.path.join(carpeta, relatiu), "w", encoding="utf-8") as f:
        f.write("\n".join(linies) + ("\n" if salt else ""))


def correr(carpeta, script="sincronitzar.py"):
    entorn = dict(os.environ, RIMADOR_ARREL=carpeta)
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)],
                       capture_output=True, text=True, env=entorn, cwd=REPO)
    return r.returncode, r.stdout + r.stderr


DICC = "diccionaris/diccionari.5.2.3.txt"
C10 = "diccionaris/col_10.txt"
resultats = []


def prova(nom, canvi, codi_esperat, text=None, comprova=None):
    carpeta = tempfile.mkdtemp()
    try:
        muntar(carpeta)
        canvi(carpeta)
        codi, sortida = correr(carpeta)
        ok = codi == codi_esperat
        if ok and text:
            ok = text.lower() in sortida.lower()
        if ok and comprova:
            ok = comprova(carpeta)
        resultats.append(ok)
        print(f"  {'OK   ' if ok else 'FALLA'} {nom}")
        if not ok:
            print(f"         codi {codi} (esperat {codi_esperat})")
            for l in sortida.strip().splitlines()[-6:]:
                print(f"         {l}")
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def edita_dicc(fila, camp, valor):
    def fes(c):
        linies = llegir(c, DICC)
        camps = linies[fila].split("$"); camps[camp] = valor
        linies[fila] = "$".join(camps)
        escriure(c, DICC, linies, salt=True)
    return fes


def edita_c10(fila, camp, valor):
    def fes(c):
        linies = llegir(c, C10)
        cap, resta = linies[fila].split(" €$", 1)
        camps = cap.split(" € "); camps[camp] = valor
        linies[fila] = " € ".join(camps) + " €$" + resta
        escriure(c, C10, linies)
    return fes


def edita_transcripcio(fila, codi, valor):
    def fes(c):
        linies = llegir(c, C10)
        trossos = linies[fila].split(f" €${codi}$ ")
        cua = trossos[1].split(" €$", 1)
        cua[0] = valor
        linies[fila] = trossos[0] + f" €${codi}$ " + " €$".join(cua)
        escriure(c, C10, linies)
    return fes


def esborra(fitxer, fila):
    def fes(c):
        linies = llegir(c, fitxer)
        del linies[fila]
        escriure(c, fitxer, linies, salt=(fitxer == DICC))
    return fes


def afegeix_dicc(fila, camps):
    def fes(c):
        linies = llegir(c, DICC)
        linies.insert(fila, "$".join(camps))
        escriure(c, DICC, linies, salt=True)
    return fes


def afegeix_c10(fila, linia):
    def fes(c):
        linies = llegir(c, C10)
        linies.insert(fila, linia)
        escriure(c, C10, linies)
    return fes


def junta(*fes):
    def tot(c):
        for f in fes:
            f(c)
    return tot


def diu(fitxer, fila, text):
    return lambda c: text in llegir(c, fitxer)[fila]


def files(fitxer, quantes):
    return lambda c: len(llegir(c, fitxer)) == quantes


print("1. Canviar una fila que ja hi és")
prova("1.1 diccionari: síl·labes", edita_dicc(4, 3, "9"), 0, comprova=diu(DICC, 4, "$9$"))
prova("1.2 col_10: una transcripció", edita_transcripcio(4, "va", "kˈaza!"), 0,
      comprova=lambda c: llegir(c, "dialectes_col/va/col_9_transcripcio_va.txt")[4] == "kˈaza!")
prova("1.4 diccionari: el codi", edita_dicc(4, 2, "NCFP000"), 0,
      comprova=lambda c: "NCFP000" in llegir(c, C10)[4])
prova("1.5 col_10: el codi", edita_c10(4, 2, "NCFP000"), 0,
      comprova=diu(DICC, 4, "NCFP000"))
prova("1.6 diccionari: la paraula", edita_dicc(4, 0, "kasa"), 0,
      comprova=lambda c: llegir(c, C10)[4].startswith("kasa € "))
prova("1.7 col_10: la paraula", edita_c10(4, 0, "kasa"), 0, comprova=diu(DICC, 4, "kasa$"))
prova("1.8 tots dos igual", junta(edita_dicc(4, 2, "NCFP000"), edita_c10(4, 2, "NCFP000")), 0)
prova("1.9 tots dos diferent", junta(edita_dicc(4, 2, "NCFP000"), edita_c10(4, 2, "NCMS000")),
      1, "conflicte")
prova("1.10 identitat i transcripció alhora",
      junta(edita_dicc(4, 2, "NCFP000"), edita_transcripcio(4, "va", "kˈaza!")), 0)

print("\n2. Esborrar")
prova("2.1 diccionari: esborrar", esborra(DICC, 4), 0,
      comprova=lambda c: (files(C10, 9)(c)
                          and files("dialectes_col/ca/col_9_transcripcio_ca.txt", 9)(c)
                          and not any(l.startswith("casa € ") for l in llegir(c, C10))))
prova("2.2 col_10: esborrar", esborra(C10, 4), 1, "esborrat")
prova("2.3 tots dos esborren", junta(esborra(DICC, 4), esborra(C10, 4)), 0, comprova=files(DICC, 9))
prova("2.4 el diccionari esborra i la col_10 hi toca",
      junta(esborra(DICC, 4), edita_transcripcio(4, "va", "kˈaza!")), 0, comprova=files(DICC, 9))

print("\n3. Afegir")
NOVA_D = ["gossa", "gos", "NCFS000", "2", "NO", "NO", "NO"]
NOVA_C = "gossa € gos € NCFS000 €$ca$ ɡˈosə €$va$ ɡˈosa"
prova("3.1 als dos alhora", junta(afegeix_dicc(1, NOVA_D), afegeix_c10(1, NOVA_C)), 0,
      comprova=lambda c: (files(DICC, 11)(c)
                          and llegir(c, "dialectes_col/va/col_9_transcripcio_va.txt")[1] == "ɡˈosa"))
prova("3.2 només al diccionari", afegeix_dicc(1, NOVA_D), 1, "no és a la col_10")
prova("3.3 només a la col_10", afegeix_c10(1, NOVA_C), 1, "no al diccionari")
prova("3.4 als dos, diferents",
      junta(afegeix_dicc(1, NOVA_D), afegeix_c10(1, "gossot € gos € NCMS000 €$ca$ ɡ €$va$ ɡ")),
      1, "no és a la col_10")

print("\n4. Reordenar")
def reordena(c):
    linies = llegir(c, DICC)
    linies[2], linies[3] = linies[3], linies[2]
    escriure(c, DICC, linies, salt=True)
prova("4.1 reordenar el diccionari", reordena, 1, "un altre ordre")

print("\n5. Dialectes")
def dialecte_nou(c):
    d = os.path.join(c, "dialectes_col", "nw")
    os.makedirs(d)
    with open(os.path.join(d, "col_9_transcripcio_nw.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(p[4] for p in PARAULES))
prova("5.1 dialecte nou", dialecte_nou, 0, "dialecte nou",
      comprova=lambda c: "€$nw$" in llegir(c, C10)[0])
def treure_dialecte(c):
    shutil.rmtree(os.path.join(c, "dialectes_col", "va"))
prova("5.2 treure un dialecte", treure_dialecte, 0,
      comprova=lambda c: "€$va$" not in llegir(c, C10)[0])
def dialecte_curt(c):
    d = os.path.join(c, "dialectes_col", "nw")
    os.makedirs(d)
    with open(os.path.join(d, "col_9_transcripcio_nw.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(p[4] for p in PARAULES[:5]))
prova("5.3 dialecte nou desquadrat", dialecte_curt, 1, "files")

print("\n6. Format")
def camps_de_menys(c):
    linies = llegir(c, DICC)
    linies[3] = "gats$gat$NCMP000"
    escriure(c, DICC, linies, salt=True)
prova("6.1 una fila del diccionari amb 3 camps", camps_de_menys, 1, "camps")
def dialecte_de_menys(c):
    linies = llegir(c, C10)
    linies[3] = linies[3].split(" €$va$")[0]
    escriure(c, C10, linies)
prova("6.2 una línia de la col_10 sense un dialecte", dialecte_de_menys, 1, "dialectes")
def transcripcio_buida(c):
    escriure(c, C10, [l.replace("€$va$ ɡˈats", "€$va$ ") if "gats" in l else l
                      for l in llegir(c, C10)])
prova("6.3 una transcripció buida", transcripcio_buida, 1, "buida")

print(f"\n{sum(resultats)}/{len(resultats)} proves correctes")
sys.exit(0 if all(resultats) else 1)
