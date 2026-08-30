// Carrega de les dades de rimes, i la gestio de versions que la governa.
//
// Les dades les genera joc/eines/generar_dades.py a partir del diccionari i de
// la rima de cada dialecte. El diccionari sencer fa 46 MB i la web principal
// se'l carrega tot; el joc no s'ho pot permetre, o sigui que descarrega nomes el
// que fa falta, i nomes del dialecte que es juga:
//
//   dades/versions.json          -> quins dialectes hi ha i el resum de cada
//                                   fitxer (uns 8 KB)
//   dades/<codi>/index.json      -> les claus de rima jugables d'aquell dialecte
//   dades/<codi>/rimes/N.txt     -> el grup de rimes de la partida (63 KB de mediana)
//
// Com que la clau consonant sempre implica la mateixa clau assonant, un sol
// fitxer serveix les dues dificultats: en facil valen totes les paraules del
// fitxer i en dificil nomes les de la seccio de la paraula objectiu.
//
// LA GESTIO DE VERSIONS es la mateixa que la del diccionari (vegeu
// carregarVersions a js/script.js i diccionaris/python/versions.py): la versio
// de cada fitxer es un resum del seu contingut, i per tant canvia exactament
// quan el fitxer ha canviat. El versions.json no es cacheja mai; tota la resta
// es demana amb ?v=<resum> i per tant es pot cachejar per sempre.

const BASE = 'dades/';

// Els resums de l'ultima vegada que el versions.json es va llegir be. Fa un
// parell de quilobytes: hi cap de sobres al localStorage.
const CLAU_VERSIONS = 'rimador.joc.versions.v1';

// cami relatiu a dades/ -> resum del contingut
let VERSIONS = {};

let versionsPromesa = null;
const indexosEnMemoria = new Map();
const fitxersEnMemoria = new Map();

/**
 * L'adreca d'un fitxer de dades, amb la seva versio.
 *
 * Sense resum de confianca hi posem un valor sempre diferent, exactament pel
 * mateix motiu que el fetchFitxer de js/script.js: val mes baixar-lo altre cop
 * que servir una copia del navegador que podria ser d'una generacio anterior i
 * no quadrar amb la resta.
 */
function adreca(cami) {
    const versio = VERSIONS[cami];
    return `${BASE}${cami}?v=${versio || 't' + Date.now()}`;
}

async function baixarJSON(cami) {
    const resposta = await fetch(adreca(cami));
    if (!resposta.ok) throw new Error(`${cami}: ${resposta.status}`);
    return resposta.json();
}

/**
 * El versions.json: { generat, dialectes: [{codi, nom}], fitxers: {cami: resum} }.
 *
 * Es el fitxer que diu que hi ha, o sigui que es l'unic que no es pot cachejar
 * mai: va amb ?t= i prou.
 */
export function carregarVersions() {
    if (versionsPromesa) return versionsPromesa;

    versionsPromesa = fetch(`${BASE}versions.json?t=${Date.now()}`)
        .then((resposta) => {
            if (!resposta.ok) throw new Error(`versions.json: ${resposta.status}`);
            return resposta.json();
        })
        .then((dades) => {
            if (!dades.fitxers || !dades.dialectes) {
                throw new Error('versions.json no porta ni fitxers ni dialectes');
            }
            VERSIONS = dades.fitxers;
            try {
                localStorage.setItem(CLAU_VERSIONS, JSON.stringify(dades));
            } catch (error) {
                // Mode privat o disc ple: nomes vol dir que la propera visita
                // sense xarxa no tindra de que estirar.
            }
            return dades;
        })
        .catch((error) => {
            // Sense xarxa, o el servidor respon malament, o el fitxer ve
            // romput. Els resums de l'ultima vegada valen mes que no res: el
            // que el navegador tingui a la seva memoria cau es va demanar amb
            // AQUESTS resums, o sigui que donant-los per bons se serveix una
            // generacio sencera i coherent de les dades. Es el mateix
            // rescat que fa el carregarVersions de js/script.js.
            try {
                const desat = localStorage.getItem(CLAU_VERSIONS);
                if (desat) {
                    const dades = JSON.parse(desat);
                    VERSIONS = dades.fitxers || {};
                    console.warn('No s\'ha pogut llegir el versions.json: es fan servir els resums de l\'ultima vegada', error);
                    return dades;
                }
            } catch (error2) {
                // El localStorage no s'hi pot llegir o el que hi havia no es
                // JSON: es continua avall, com si no hi hagues hagut cap visita.
            }
            versionsPromesa = null;   // que es pugui tornar a provar
            throw error;
        });

    return versionsPromesa;
}

/**
 * L'index de claus jugables d'un dialecte.
 * Cada clau: [clauConsonant, numeroDeFitxer, nombreObjectius]
 */
export function carregarIndex(dialecte) {
    if (indexosEnMemoria.has(dialecte)) return indexosEnMemoria.get(dialecte);

    const promesa = carregarVersions()
        .then(() => baixarJSON(`${dialecte}/index.json`))
        .catch((error) => {
            indexosEnMemoria.delete(dialecte);
            throw error;
        });

    indexosEnMemoria.set(dialecte, promesa);
    return promesa;
}

/**
 * Un fitxer de rimes, ja repartit per seccions.
 * Torna { seccions: Map<clauConsonant, {paraules, objectius}> }.
 */
export function carregarFitxerDeRimes(dialecte, numero) {
    const clau = `${dialecte}/${numero}`;
    if (fitxersEnMemoria.has(clau)) return fitxersEnMemoria.get(clau);

    const cami = `${dialecte}/rimes/${numero}.txt`;
    const promesa = fetch(adreca(cami))
        .then((resposta) => {
            if (!resposta.ok) throw new Error(`${cami}: ${resposta.status}`);
            return resposta.text();
        })
        .then(analitzar)
        .catch((error) => {
            fitxersEnMemoria.delete(clau);
            throw error;
        });

    fitxersEnMemoria.set(clau, promesa);
    return promesa;
}

// El format es una linia per paraula, amb capcaleres "#clau" que obren seccio.
// Un "*" al davant marca les paraules que poden ser OBJECTIU (no son verbs); la
// resta nomes valen com a rima. Si la forma real porta accents va despres d'un
// ">" ("cami>camí"); si no, la linia ja es la forma normalitzada. Aixi no hem de
// normalitzar res aqui.
//
// Cada seccio guarda:
//   paraules  -> Map<normalitzada, formaPerMostrar>  (totes: valen com a rima)
//   objectius -> [normalitzada, ...]                  (nomes les que poden sortir)
function analitzar(text) {
    const seccions = new Map();
    let actual = null;

    for (let linia of text.split('\n')) {
        if (!linia) continue;
        if (linia.charCodeAt(0) === 35 /* # */) {
            actual = { paraules: new Map(), objectius: [] };
            seccions.set(linia.slice(1), actual);
            continue;
        }
        if (!actual) continue;

        const esObjectiu = linia.charCodeAt(0) === 42; /* * */
        if (esObjectiu) linia = linia.slice(1);

        const tall = linia.indexOf('>');
        const normalitzada = tall === -1 ? linia : linia.slice(0, tall);
        const mostrar = tall === -1 ? linia : linia.slice(tall + 1);

        actual.paraules.set(normalitzada, mostrar);
        if (esObjectiu) actual.objectius.push(normalitzada);
    }

    return { seccions };
}

/**
 * Les respostes valides d'una partida: Map<normalitzada, formaPerMostrar>.
 * En facil, tot el grup assonant (o sigui, totes les seccions del fitxer).
 * En dificil, nomes la seccio de la clau consonant de la paraula objectiu.
 * Els verbs hi son inclosos: valen sempre com a rima.
 */
export function respostesValides(fitxer, clauConsonant, dificultat) {
    if (dificultat === 'dificil') {
        const seccio = fitxer.seccions.get(clauConsonant);
        if (!seccio) throw new Error(`No hi ha la seccio "${clauConsonant}"`);
        return new Map(seccio.paraules);
    }

    const totes = new Map();
    for (const seccio of fitxer.seccions.values()) {
        for (const [normalitzada, mostrar] of seccio.paraules) {
            totes.set(normalitzada, mostrar);
        }
    }
    return totes;
}
