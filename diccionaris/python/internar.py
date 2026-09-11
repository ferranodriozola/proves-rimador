"""
Internar les columnes: en lloc de repetir el mateix text milers de vegades,
una taula amb els valors diferents i, per a cada fila, el número que hi apunta.

    python3 diccionaris/python/internar.py

    separat/col_1,2,5,6,7,8              ->  separat/internat/
    <codi>/trans_dicc/col_3,4            ->  <codi>/trans_dicc/internat/
    <codi>/apendix/col_1,2,3,4,5,6,7,8   ->  <codi>/apendix/internat/

El perquè: la col_8 (si la paraula surt al DIEC) té 619.783 files i exactament
DOS valors diferents. Al navegador, cada fila era un objecte de text separat, i
això vol dir 14 MB de memòria per dir dues coses. Set de les columnes tenen
aquesta mateixa forma i entre totes se n'enduien 111 MB. Internades en són 11,6.

Es fa aquí i no al navegador perquè així no s'ha de fer a cada visita, però
sobretot perquè el navegador ja no ha de crear mai els 619.783 objectes de
text: els números van directes a un array de mida fixa.

El format és text i no binari a posta. Per la xarxa pesen igual (1,42 MB contra
1,29 un cop comprimits), però un .txt és text/plain i GitHub Pages el comprimeix
segur, mentre que un .bin se serviria com a application/octet-stream, que els
CDN normalment no comprimeixen: seria passar de 1,4 MB a 7,8. I de retruc els
fitxers continuen sortint al git diff.

La col_0 (paraula) no s'interna: 529.206 valors diferents de 619.783 files, el
85 % són únics i no hi ha res a estalviar. La col_9 (transcripcions) tampoc, pel
mateix motiu i perquè el navegador no la demana mai. Als apendixs es fa igual,
i per la mateixa raó: són columnes de la mateixa forma, més curtes.

CADA COLUMNA ES COMPARA AMB LES DE LA SEVA BANDA. Les del diccionari i les del
trans_dicc de cada dialecte han de tenir totes les files del diccionari; les
d'un apendix, les d'aquell apendix, que és un nombre diferent a cada dialecte.
Prendre'n una per l'altra és l'error que desquadraria una columna sencera en
silenci, i per això aquí el nombre de files sempre arriba com a paràmetre i mai
d'una variable global.
"""

import os
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import avisos
import camins

# Columnes que són nombres i que no s'internen "a cegues".
#
# A la resta, el número de cada valor és l'ordre en què ha aparegut, que no vol
# dir res. A la col_5, en canvi, els valors SÓN el nombre de síl·labes, i seria
# absurd que la síl·laba 5 s'amagués darrere d'un número qualsevol. Aquí la
# taula va del 0 al 14 i cada valor cau al seu lloc: idx[i] és directament el
# nombre de síl·labes, i condicions com "6 o més" es poden escriure idx[i] >= 6
# sense haver de mirar la taula ni convertir cap text.
#
# No costa memòria: un Uint8Array ocupa un byte per fila tant si la taula té 13
# entrades com si en té 15.
NUMERIQUES = {5: 14}  # columna -> valor màxim admès


def internar(valors):
    taula, numero, indexs = [], {}, []
    for valor in valors:
        n = numero.get(valor)
        if n is None:
            n = len(taula)
            numero[valor] = n
            taula.append(valor)
        indexs.append(n)
    return taula, indexs


def internar_numerica(valors, maxim, nom):
    """La taula és 0, 1, 2... fins al màxim, i l'índex de cada fila és el seu
    propi valor. Els valors arriben en bytes, com a l'altre internador."""
    taula = [str(n).encode() for n in range(maxim + 1)]
    indexs = []
    for fila, valor in enumerate(valors, 1):
        try:
            n = int(valor)
        except ValueError:
            avisos.plegar(f"{nom}, fila {fila}: {valor!r} no és cap nombre.")
        if not 0 <= n <= maxim:
            avisos.plegar(f"{nom}, fila {fila}: {n} surt del marge 0-{maxim}. "
                          f"Puja el màxim a NUMERIQUES i torna-ho a passar.")
        # Descarta "01", " 3" i companyia: si el text no torna a sortir igual,
        # la columna no es reconstruiria byte a byte.
        if taula[n] != valor:
            avisos.plegar(f"{nom}, fila {fila}: {valor!r} no s'escriu com {taula[n]!r}.")
        indexs.append(n)
    return taula, indexs


def tipus_darray(quants):
    """Informatiu: el navegador ho torna a deduir de la mida de la taula, i per
    això no ho escrivim en cap fitxer. Deduir-ho és més segur que declarar-ho,
    perquè no es pot desincronitzar quan el diccionari creixi."""
    if quants <= 256:
        return "Uint8Array", 1
    if quants <= 65536:
        return "Uint16Array", 2
    return "Uint32Array", 4


def desar(nom, cami_origen, cami_taula, cami_idx, files_esperades, maxim=None,
          companyes="les columnes del diccionari"):
    valors = camins.llegir_columna(cami_origen)

    # Són una sola llista de paraules partida en columnes: si no van a l'una, la
    # fila 500 d'una columna no és la mateixa paraula que la fila 500 d'una
    # altra, i internar-ho només consagraria el desori.
    if len(valors) != files_esperades:
        avisos.plegar(f"{nom} té {camins.mil(len(valors))} files i {companyes} "
                      f"en tenen {camins.mil(files_esperades)}.")

    valors = [valor.encode() for valor in valors]
    if maxim is not None:
        taula, indexs = internar_numerica(valors, maxim, nom)
    else:
        taula, indexs = internar(valors)

    # Que el que escrivim reconstrueixi exactament el que hem llegit. Si això
    # falla, val més no deixar cap fitxer que deixar-ne un de dolent.
    if [taula[n] for n in indexs] != valors:
        avisos.plegar(f"la {nom} internada no reconstrueix l'original.")
    if max(indexs) >= len(taula):
        avisos.plegar(f"la {nom} té un índex fora de la seva taula.")

    # Sense salt de línia al final, com les columnes d'origen: el navegador
    # munta l'array comptant salts de línia i es trobaria una fila de més.
    os.makedirs(os.path.dirname(cami_taula), exist_ok=True)
    with open(cami_taula, "wb") as fitxer:
        fitxer.write(b"\n".join(taula))
    with open(cami_idx, "wb") as fitxer:
        fitxer.write(b"\n".join(str(n).encode() for n in indexs))

    nom_tipus, bytes_per_fila = tipus_darray(len(taula))
    abans = os.path.getsize(cami_origen)
    despres = os.path.getsize(cami_taula) + os.path.getsize(cami_idx)
    memoria = len(taula) * 24 + files_esperades * bytes_per_fila
    avisos.nota(f"  {nom:<24} {len(taula):>6} valors -> {nom_tipus:<12}"
                f" disc {abans/1048576:5.1f} MB -> {despres/1048576:4.1f} MB"
                f" | memòria ~{memoria/1048576:4.1f} MB"
                f"{' (numèrica)' if maxim is not None else ''}")


def main():
    files = camins.files_del_diccionari()
    avisos.nota(f"Internant les columnes del diccionari ({camins.mil(files)} files):\n")

    for i in camins.INTERNADES_DEL_DICCIONARI:
        desar(f"col_{i}.txt", camins.cami_columna(i),
              camins.cami_internat(i, "taula"), camins.cami_internat(i, "idx"),
              files, NUMERIQUES.get(i))

    for codi in camins.dialectes():
        avisos.nota(f"\nDialecte '{codi}', trans_dicc ({camins.mil(files)} files):\n")
        for i in camins.COLUMNES_DE_DIALECTE:
            cami = camins.cami_dialecte(codi, i)
            desar(os.path.basename(cami), cami,
                  camins.cami_internat_dialecte(codi, i, "taula"),
                  camins.cami_internat_dialecte(codi, i, "idx"), files)

        if not camins.te_apendix(codi):
            continue

        # Les files d'un apendix són les seves i no pas les del diccionari.
        files_apendix = camins.files_de_lapendix(codi)
        avisos.nota(f"\nDialecte '{codi}', apendix ({camins.mil(files_apendix)} files):\n")
        for i in camins.INTERNADES_APENDIX:
            cami = camins.cami_apendix(codi, i)
            if not os.path.exists(cami):
                avisos.plegar(f"falta {camins.relatiu(cami)}. Passa el columnes.py "
                              f"(la col_3 i la col_4) o el sincronitzar.py (la resta).")
            desar(os.path.basename(cami), cami,
                  camins.cami_internat_apendix(codi, i, "taula"),
                  camins.cami_internat_apendix(codi, i, "idx"),
                  files_apendix, NUMERIQUES.get(i),
                  f"les altres columnes de l'apendix del '{codi}'")

    avisos.nota("\nFet. Ara toca el versions.py: els fitxers nous han d'entrar al\n"
                "versions.json perquè el navegador els pugui desar a la memòria cau.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
