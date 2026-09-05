"""
Buscar cada infinitiu dels apendixs al diccionari i portar-ne Vicc, Viq i Diec.

    python3 marc_dialectes/apendixs_def/filtrar_lemes.py

    {dialecte}/softcatala.txt  +  diccionaris/diccionari.5.2.3.txt
        ->  {dialecte}/col_6_{dialecte}.txt      Vicc
            {dialecte}/col_7_{dialecte}.txt      Viq (sempre NO)
            {dialecte}/col_8_{dialecte}.txt      Diec
            {dialecte}/esborrades_{dialecte}.txt les files sense lema

Es compara la segona columna de cada fila de l'apendix (l'infinitiu) amb la
segona columna del diccionari (el lema). Si el lema hi es, la fila es queda i
rep les tres marques de diccionari; si no hi es, la fila desapareix de
softcatala.txt i va a parar al fitxer d'esborrades del seu dialecte.

LES TRES MARQUES SON DEL LEMA, NO DE LA FORMA. Al diccionari van fila per fila
i no sempre son iguals dins d'un mateix lema:

    Viq   les formes dialectals no son a la Viquipedia: sempre NO.
    Diec  constant a totes les files d'un verb; es copia i prou.
    Vicc  canvia en 1.141 verbs, perque el Viccionari de vegades nomes te
          l'entrada de l'infinitiu i no la conjugacio (adjuntar hi es, pero
          adjunta/adjuntava no). Com que les formes dialectals son formes
          conjugades, s'agafa el valor de la MAJORIA de files del verb: si el
          Viccionari no el conjuga, la forma dialectal tampoc hi sera.

EN ESBORRAR FILES ES DESQUADREN LES ALTRES COLUMNES. Els col_N_{dialecte}.txt
van lligats linia per linia amb softcatala.txt, i el col_9 (la transcripcio
d'espeak-ng) costa d'obtenir; per aixo, amb SINCRONITZAR, se'ls treuen les
mateixes linies.
"""

import os
import sys

CARPETA = os.path.dirname(os.path.abspath(__file__))
ARREL = os.path.dirname(os.path.dirname(CARPETA))
DICCIONARI = os.path.join(ARREL, "diccionaris", "diccionari.5.2.3.txt")

DIALECTES = ["ca", "nw", "ba", "va"]

# Quina dada va a quin fitxer, seguint la numeracio del diccionari de 10
# columnes (0 forma, 1 lema, 2 codi, 3-4 rimes, 5 silabes, 6 Vicc, 7 Viq,
# 8 Diec, 9 fonetica).
COL_VICC = 6
COL_VIQ = 7
COL_DIEC = 8

# Les formes dialectals no surten a la Viquipedia.
VIQ = "NO"

# Treure tambe de la resta de columnes les linies esborrades, per no desquadrar-les.
SINCRONITZAR = True


def llegir_diccionari():
    """Per a cada lema del diccionari, quin Vicc i quin Diec li toquen.

    El diccionari va per files (forma, lema, codi, silabes, Vicc, Viq, Diec)
    separades per $. Es compten les files de cada lema i guanya la majoria.
    Nomes es miren les files verbals quan n'hi ha, perque hi ha lemes que son
    verb i nom alhora (poder) i les formes dels apendixs son totes verbals.
    """
    verbals = {}
    altres = {}
    with open(DICCIONARI, encoding="utf-8") as fitxer:
        for numero, linia in enumerate(fitxer, 1):
            camps = linia.rstrip("\n").replace("\r", "").split("$")
            if len(camps) != 7:
                sys.exit("diccionari.5.2.3.txt, linia %d: hi ha %d columnes i n'hi "
                         "ha d'haver 7." % (numero, len(camps)))
            lema, codi, vicc, diec = camps[1], camps[2], camps[4], camps[6]
            on = verbals if codi.startswith("V") else altres
            compte = on.setdefault(lema, [0, 0, 0, 0])
            compte[0 if vicc == "Vicc" else 1] += 1
            compte[2 if diec == "Diec" else 3] += 1

    lemes = {}
    discrepants = 0
    for taula in (altres, verbals):          # les verbals manen i trepitgen les altres
        for lema, (vicc_si, vicc_no, diec_si, diec_no) in taula.items():
            if taula is verbals and (vicc_si and vicc_no):
                discrepants += 1
            lemes[lema] = ("Vicc" if vicc_si > vicc_no else "NO",
                           "Diec" if diec_si > diec_no else "NO")
    return lemes, discrepants


def llegir_apendix(cami):
    """Les files d'un softcatala.txt: (forma, lema, codi) i la linia sencera."""
    files = []
    with open(cami, encoding="utf-8") as fitxer:
        for numero, linia in enumerate(fitxer, 1):
            camps = linia.split()
            if not camps:
                continue
            if len(camps) != 3:
                sys.exit("%s, linia %d: hi ha %d camps i n'hi ha d'haver 3 "
                         "(forma, lema, codi)." % (cami, numero, len(camps)))
            files.append(camps)
    return files


def escriure(cami, valors):
    """Una columna, un valor per linia.

    Amb newline LF a posta: som a Windows i, sense dir-ho, el Python escriuria
    CRLF i els fitxers no serien comparables amb els altres.
    """
    with open(cami, "w", encoding="utf-8", newline="\n") as fitxer:
        for valor in valors:
            fitxer.write(valor + "\n")


def sincronitzar(carpeta, dialecte, mascara, files_abans, generats):
    """Treure les mateixes linies de la resta de columnes del dialecte.

    Nomes es toquen els fitxers que anaven quadrats amb l'apendix; si un no te
    el nombre de linies d'abans es que ja no hi anava lligat, i val mes deixar-lo
    estar i dir-ho que no pas esguerrar-lo.
    """
    for nom in sorted(os.listdir(carpeta)):
        if not nom.startswith("col_") or not nom.endswith("_%s.txt" % dialecte):
            continue
        if nom in generats:
            continue
        cami = os.path.join(carpeta, nom)
        with open(cami, encoding="utf-8") as fitxer:
            linies = fitxer.read().replace("\r", "").split("\n")
        if linies and linies[-1] == "":
            linies.pop()
        if len(linies) != files_abans:
            print("    {} te {:,} linies i l'apendix en tenia {:,}: no es toca."
                  .format(nom, len(linies), files_abans))
            continue
        escriure(cami, [l for l, quedar in zip(linies, mascara) if quedar])
        print("    {} sincronitzat".format(nom))


def main():
    print("Llegint el diccionari...")
    lemes, discrepants = llegir_diccionari()
    print("  {:,} lemes ({:,} amb el Vicc repartit entre les seves formes; "
          "hi mana la majoria)".format(len(lemes), discrepants))

    for dialecte in DIALECTES:
        carpeta = os.path.join(CARPETA, dialecte)
        apendix = os.path.join(carpeta, "softcatala.txt")
        if not os.path.exists(apendix):
            sys.exit("no hi ha %s." % apendix)

        print("\n%s" % dialecte)
        files = llegir_apendix(apendix)

        mascara = []
        quedar = []
        fora = []
        vicc = []
        diec = []
        for forma, lema, codi in files:
            marques = lemes.get(lema)
            mascara.append(marques is not None)
            if marques is None:
                fora.append((forma, lema, codi))
            else:
                quedar.append((forma, lema, codi))
                vicc.append(marques[0])
                diec.append(marques[1])

        generats = {}
        for numero, valors in ((COL_VICC, vicc),
                               (COL_VIQ, [VIQ] * len(quedar)),
                               (COL_DIEC, diec)):
            nom = "col_%d_%s.txt" % (numero, dialecte)
            escriure(os.path.join(carpeta, nom), valors)
            generats[nom] = True
        print("  {:,} files amb lema al diccionari  ->  {}".format(
            len(quedar), ", ".join(sorted(generats))))

        if fora:
            nom = "esborrades_%s.txt" % dialecte
            with open(os.path.join(carpeta, nom), "w", encoding="utf-8",
                      newline="\n") as fitxer:
                for fila in fora:
                    fitxer.write(" ".join(fila) + "\n")
            print("  {:,} files sense lema  ->  {} ({:,} infinitius diferents)".format(
                len(fora), nom, len(set(f[1] for f in fora))))

            with open(apendix, "w", encoding="utf-8", newline="\n") as fitxer:
                for fila in quedar:
                    fitxer.write(" ".join(fila) + "\n")
            print("  softcatala.txt: {:,} files -> {:,}".format(len(files), len(quedar)))

            if SINCRONITZAR:
                sincronitzar(carpeta, dialecte, mascara, len(files), generats)
        else:
            # Res a treure: no es reescriu l'apendix ni s'esborra el registre
            # d'una passada anterior.
            print("  cap fila sense lema: softcatala.txt es queda com estava.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
