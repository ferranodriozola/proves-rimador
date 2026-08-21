//DEBUG
const debugLevel = 0; // 0 = Off, 1 = Goatcounter, 2 = Errors, 3 = Logs, 4 = Temps

const Debug = {
    log: debugLevel >= 3 ? (label) => console.log(`[DEBUG] ${label}`) : () => {},
    logError: debugLevel >= 2 ? (...args) => console.error('[ERROR]', ...args) : () => {},
    logTime: debugLevel >= 4 ? (label) => console.time(`[TIMER] ${label}`) : () => {},
    logTimeEnd: debugLevel >= 4 ? (label) => console.timeEnd(`[TIMER] ${label}`) : () => {},
    contador: debugLevel >= 1 ? (label) => console.log(`[COUNTER] ${label}`) : () => {},
};

if (debugLevel >= 3) {
  window.addEventListener('DOMContentLoaded', () => {
    const boto = document.getElementById("botoNetejarCache");
    if (boto) boto.style.display = "block";
  });
}

// ============================================================= //
// LOADER
//
// Ensenyar el loader no és tan senzill com posar-li display i prou. El
// navegador té un sol fil per a la nostra feina i per a pintar: si li
// diem que ensenyi el loader i tot seguit ens passem tres segons
// escrivint HTML, no arriba a pintar res fins que hem acabat, i el
// loader s'ensenya i s'amaga dins el mateix fotograma. O sigui, com si
// no hi fos. Per això Loader.mentre() espera dos fotogrames abans de
// posar-se a treballar: el primer es programa abans del pròxim pintat i
// el segon no arriba fins que aquell pintat ja s'ha entregat a pantalla.
//
// La pila serveix per als encavallaments: una cerca demana el loader i,
// a mitges, la càrrega de les transcripcions el torna a demanar. Si el
// de dins l'apagués en acabar, la cerca es quedaria fent la feina grossa
// amb la pantalla destapada i tornaríem a on érem.
const Loader = {
  _pila: [],

  _pintar() {
    const caixa = document.getElementById('loader');
    if (!caixa) return;
    const text = document.getElementById('loader-text2');

    if (this._pila.length) {
      if (text) text.textContent = this._pila[this._pila.length - 1];
      caixa.style.display = '';
    } else {
      caixa.style.display = 'none';
      if (text) text.textContent = '';
    }
  },

  // Espera que el navegador hagi dibuixat de debò. El primer
  // requestAnimationFrame es programa abans del pròxim pintat i el segon
  // no arriba fins que aquell pintat ja s'ha entregat a la pantalla.
  //
  // Ara bé: si la pestanya no es veu (l'usuari ha canviat de pestanya o
  // ha abaixat la finestra), el navegador no dibuixa i aquests avisos no
  // arriben mai. Sense les dues sortides d'emergència d'aquí sota, la
  // cerca es quedaria esperant un fotograma que no ha de venir i no
  // arrencaria fins que algú tornés a mirar la pàgina.
  _dosFotogrames() {
    if (document.hidden) return Promise.resolve();

    return new Promise(resolve => {
      let fet = false;
      const acabar = () => { if (!fet) { fet = true; resolve(); } };

      requestAnimationFrame(() => requestAnimationFrame(acabar));
      setTimeout(acabar, 200); // per si els fotogrames no arriben igualment
    });
  },

  // Ensenya el loader, fa la feina i el treu passi el que passi.
  async mentre(missatge, feina) {
    this._pila.push(missatge);
    this._pintar();
    await this._dosFotogrames();

    try {
      return await feina();
    } finally {
      this._pila.pop();
      this._pintar();
    }
  },

  // Per a les estones en què la pàgina espera que l'usuari decideixi (el
  // diàleg d'homògrafs): el loader hi fa nosa, i deixar-lo donant voltes
  // al darrere fa pensar que la pàgina encara està carregant. El treu
  // mentre duri l'espera i el torna a deixar com estava.
  async apartat(feina) {
    const desada = this._pila;
    this._pila = [];
    this._pintar();

    try {
      return await feina();
    } finally {
      this._pila = desada;
      this._pintar();
      if (this._pila.length) await this._dosFotogrames();
    }
  }
};

// ============================================================= //

// PARAULES NÀUFRAGUES
//
// Una paraula és nàufraga quan no rima consonantment amb cap altra: el seu grup
// de rima només la conté a ella, encara que hi surti diverses vegades amb codis
// diferents.
//
// Abans això es mirava en un paraules_naufragues.json de 3,9 MB que es baixava
// a CADA visita (anava amb ?t=Date.now(), o sigui que no es cachejava mai).
// Amb la memòria cau calenta era gairebé l'única cosa que quedava per baixar.
//
// Però la resposta ja la tenim: l'índex de rimes diu quines files comparteixen
// rima amb la paraula cercada, i mirar-ne les poques que són (47 de mitjana) és
// instantani. La llista només la necessita la pàgina que les ensenya totes.
let paraulaEsNaufraga = false;

function calcularSiEsNaufraga(fila) {
  if (fila < 0 || !indexConsonant) return false;

  const rima = col3.idx[fila];
  const paraula = array0[fila].toLowerCase();
  const { inici, files } = indexConsonant;

  for (let k = inici[rima]; k < inici[rima + 1]; k++) {
    if (array0[files[k]].toLowerCase() !== paraula) return false;
  }
  return true;
}


//gestió de versions
let VERSIONS_FITXERS = {};

async function carregarVersions() {
  try {
    const resposta = await fetch(`${ARREL}diccionaris/versions.json?t=${Date.now()}`);
    const dades = await resposta.json();

    // La versió de cada columna és un resum del seu contingut, calculat
    // pels workflows amb diccionaris/generar_versions.py. Cada columna es
    // refresca exactament quan el seu fitxer ha canviat: ni abans (com
    // passava quan una columna reescrita mantenia el número vell i es
    // barrejaven generacions del diccionari) ni de més.
    if (!dades.columnes) throw new Error("versions.json no porta la llista de columnes");

    VERSIONS_FITXERS = dades.columnes;
    console.log("Versions carregades correctament:", VERSIONS_FITXERS);
  } catch (err) {
    // Sense versions de confiança no podem saber si el que tenim guardat
    // encara val. Es deixa la llista buida: llavors cada columna es baixa
    // del servidor i no se'n desa cap còpia (vegeu llegirFitxerAmbIndexedDB).
    console.error("Error carregant versions.json: es baixarà tot el diccionari sense memòria cau", err);
    VERSIONS_FITXERS = {};
  }
}


//INICI

// array0 (les paraules) és una llista de text de tota la vida. La resta de
// columnes van internades: en lloc de repetir el mateix text milers de
// vegades, cadascuna és { taula, idx }, amb els valors diferents a la taula i
// un número per fila que hi apunta. Guardades així ocupen 11,6 MB en comptes
// de 111 (vegeu generar_columnes_internades.py).
let array0;

let col1, col2, col3, col4, col5, col6, col7, col8;

// Les tres últimes columnes són sí/no (surt al Viccionari, a la Viquipèdia, al
// DIEC). Tres arrays d'un byte per fila per guardar tres bits és malbaratar-ne
// vint-i-un: aquí van totes tres al mateix byte. Val null si algun dia alguna
// d'aquestes columnes deixa de tenir només dos valors, i llavors es llegeixen
// com les altres.
let banderes = null;

// Per a cada rima, quines files la tenen (vegeu indexarPerRima).
let indexConsonant = null;
let indexAssonant = null;

// Lectors de les columnes internades: tornen el text de sempre a partir del
// número que hi ha guardat a cada fila.
const t1 = i => col1.taula[col1.idx[i]];
const t2 = i => col2.taula[col2.idx[i]];
const t3 = i => col3.taula[col3.idx[i]];
const t4 = i => col4.taula[col4.idx[i]];
const t5 = i => col5.taula[col5.idx[i]];
const t6 = i => (banderes ? col6.taula[banderes[i] & 1] : col6.taula[col6.idx[i]]);
const t7 = i => (banderes ? col7.taula[(banderes[i] >> 1) & 1] : col7.taula[col7.idx[i]]);
const t8 = i => (banderes ? col8.taula[(banderes[i] >> 2) & 1] : col8.taula[col8.idx[i]]);

let fitxersLlegits = 0;

// col_9 (les transcripcions senceres) no hi és, i no s'hi baixa mai: fa 73 MB
// i quatre milions de línies. L'única cosa que en necessitava el web era el
// diàleg d'homògrafs, i per a saber-ho ja n'hi ha prou amb els números de rima
// de col_3 i col_4, que es carreguen igualment per cercar (vegeu buscarParaula).
const CAMI_PARAULES = `${ARREL}diccionaris/separat/col_0.txt`;

// La paraula, el lema, el codi, les síl·labes i els tres enllaços són les
// mateixes es parli com es parli, i continuen a separat/.
const COLUMNES_DEL_DICCIONARI = [1, 2, 5, 6, 7, 8];

// La rima, en canvi, ja no és al diccionari: depèn de com es parli i cada
// dialecte té la seva a dialectes_col/<codi>/.
const COLUMNES_DE_RIMA = [3, 4];

// Quins dialectes hi ha. Surten de la llista DIALECTES de js/components.js,
// que és la mateixa que pinta les pastilles de la tira: així el que es baixa i
// el que es pot triar no poden dir coses diferents mai. Afegir-hi el
// rossellonès és tocar aquella llista i res més.
//
// El fallback és per a les pàgines que carreguen aquest fitxer sense passar
// pel components.js: allà no hi ha cap tira per triar res i el central és
// l'únic que fa falta.
const CODIS_DE_DIALECTE = (typeof DIALECTES !== 'undefined') ? DIALECTES.map(d => d.codi) : ['ca'];

// El de sempre: l'únic amb la transcripció repassada a mà (els altres surten
// de l'espeak-ng) i el que es dona a qui no ha triat mai res. És el CENTRAL de
// diccionaris/python/camins.py.
const DIALECTE_PER_DEFECTE = 'ca';

// La tria es recorda entre visites, igual que el tema (vegeu THEME_STORAGE_KEY).
const CLAU_DIALECTE = 'rimadorDialecte';

function dialecteDesat() {
  try {
    const desat = localStorage.getItem(CLAU_DIALECTE);
    if (CODIS_DE_DIALECTE.includes(desat)) return desat;
  } catch (err) {
    // Mode privat o cookies barrades: no és cap problema, s'agafa el de sempre.
  }
  return DIALECTE_PER_DEFECTE;
}

// Quin se serveix ara mateix. Canvia amb la tira de dialectes (vegeu
// lligarTriaDeDialecte, més avall).
let dialecteActiu = dialecteDesat();

// La rima de tots els dialectes, ja llegida i interpretada:
// { ca: { 3: {taula, idx}, 4: {taula, idx} }, nw: {...}, ... }
//
// S'hi baixen TOTS a l'inici, no pas només el triat. Són uns 3,5 MB per
// dialecte (i molt menys per la xarxa, que són fitxers de xifres i el
// servidor els comprimeix), i a canvi canviar de dialecte no espera cap
// descàrrega: ja són a la memòria i només s'han de tornar a indexar.
let rimaPerDialecte = {};

// La col_0 i, de cada columna internada, la taula i els índexs. Es compta i no
// s'escriu a mà: el dia que hi hagi sis dialectes, el comptador del loader
// continuarà dient la veritat sense que ningú se n'hagi de recordar.
let nombresDeFitxers = 1 +
    COLUMNES_DEL_DICCIONARI.length * 2 +
    CODIS_DE_DIALECTE.length * COLUMNES_DE_RIMA.length * 2;

// Com es diu la columna de rima de cada dialecte. El codi va DINS del nom del
// fitxer i no només a la carpeta, a posta: la memòria cau i el versions.json
// s'indexen pel nom del fitxer sol (vegeu llegirFitxerAmbIndexedDB, que fa
// rutaFitxer.split("/").pop()), i el col_3.idx.txt del valencià i el del
// balear serien la mateixa entrada.
const NOMS_DE_RIMA = { 3: 'rimacons', 4: 'rimaass' };

function arrelDeLaColumna(numero, codi) {
  if (NOMS_DE_RIMA[numero]) {
    return `${ARREL}dialectes_col/${codi}/internat/col_${numero}_${NOMS_DE_RIMA[numero]}_${codi}`;
  }
  return `${ARREL}diccionaris/separat/internat/col_${numero}`;
}

// El tipus surt de la mida de la taula i no es declara enlloc: així el dia que
// el diccionari creixi i una columna passi dels 65.536 valors diferents, això
// puja de tipus tot sol.
function menaDArray(quantsValors) {
  if (quantsValors <= 256) return Uint8Array;
  if (quantsValors <= 65536) return Uint16Array;
  return Uint32Array;
}

// Els índexs es llegeixen xifra a xifra cap a un array de mida fixa. No es fa
// servir split('\n') a posta: partiria el text en 619.783 objectes de text, que
// és exactament el que estem mirant de no tenir.
function textAIndexs(contingut, Tipus) {
  let files = 1;
  for (let i = 0; i < contingut.length; i++) {
    if (contingut.charCodeAt(i) === 10) files++;
  }

  const indexs = new Tipus(files);
  let valor = 0;
  let fila = 0;

  for (let i = 0; i < contingut.length; i++) {
    const codi = contingut.charCodeAt(i);
    if (codi === 10) {
      indexs[fila++] = valor;
      valor = 0;
    } else {
      valor = valor * 10 + (codi - 48);
    }
  }
  indexs[fila] = valor;

  return indexs;
}

// La taula va primer perquè és qui diu de quina mena ha de ser l'array dels
// índexs. Totes dues passen pel mateix llegirFitxerAmbIndexedDB que la resta,
// o sigui que hereten la memòria cau i el control de versions sense res especial.
async function carregarColumnaInternada(numero, codi) {
  const arrel = arrelDeLaColumna(numero, codi);
  const taula = await llegirFitxerAmbIndexedDB(`${arrel}.taula.txt`);
  const Tipus = menaDArray(taula.length);
  const idx = await llegirFitxerAmbIndexedDB(`${arrel}.idx.txt`, contingut => textAIndexs(contingut, Tipus));
  return { taula, idx };
}

// Per a cada rima, les files que la tenen, amb dos arrays plans en lloc d'un
// array d'arrays: `inici` diu on comença cada grup dins de `files`, i `files`
// són els números de fila seguits, agrupats per rima. Deu mil arrays petits
// serien deu mil objectes i molta memòria de capçaleres.
//
// Dins de cada grup les files queden en ordre creixent, perquè s'omple
// recorrent el diccionari de dalt a baix. Això importa: és el que fa que les
// rimes surtin en el mateix ordre que quan es mirava el diccionari sencer.
function indexarPerRima(columna) {
  const quantesRimes = columna.taula.length;
  const inici = new Uint32Array(quantesRimes + 1);

  for (let i = 0; i < columna.idx.length; i++) inici[columna.idx[i] + 1]++;
  for (let r = 0; r < quantesRimes; r++) inici[r + 1] += inici[r];

  const files = new Uint32Array(columna.idx.length);
  const posicio = inici.slice(0, quantesRimes);
  for (let i = 0; i < columna.idx.length; i++) files[posicio[columna.idx[i]]++] = i;

  return { inici, files };
}

// El que es prepara un cop, en carregar, i estalvia feina a cada cerca.
function prepararColumnes() {
  // Les tres banderes al mateix byte. El bit que ocupa cadascuna és el mateix
  // número que ja tenia a la seva taula, o sigui que llegir-lo torna el text bo.
  // El col6.idx i companyia s'alliberen aquí sota, o sigui que això només es
  // pot fer un cop: si algun dia es torna a cridar, que no hi torni a entrar.
  if (col6.idx && col7.idx && col8.idx &&
      col6.taula.length <= 2 && col7.taula.length <= 2 && col8.taula.length <= 2) {
    const empaquetades = new Uint8Array(col6.idx.length);
    for (let i = 0; i < empaquetades.length; i++) {
      empaquetades[i] = col6.idx[i] | (col7.idx[i] << 1) | (col8.idx[i] << 2);
    }
    banderes = empaquetades;
    col6.idx = col7.idx = col8.idx = null; // ja no calen
  }
}

// Passar a un altre dialecte. La rima ja és tota a la memòria (vegeu
// rimaPerDialecte), o sigui que això no baixa res: només torna a apuntar el
// col3 i el col4 cap a l'altra columna i en refà els índexs, que són un parell
// de passades pel diccionari i prou.
//
// Torna false si la rima demanada encara no hi és (el diccionari s'està
// carregant, o el codi no existeix). Qui el crida no ha de tocar res en aquest
// cas: val més quedar-se com estàvem que marcar una pastilla i ensenyar les
// rimes de l'altre dialecte.
function aplicarDialecte(codi) {
  const rima = rimaPerDialecte[codi];
  if (!rima || !rima[3] || !rima[4]) return false;

  dialecteActiu = codi;
  col3 = rima[3];
  col4 = rima[4];
  indexConsonant = indexarPerRima(col3);
  indexAssonant = indexarPerRima(col4);
  return true;
}

document.addEventListener('DOMContentLoaded', async () => {
    if (idPagina !== 'principal') return;
    Debug.logTime('Temps de càrrega');
    const loaderText2 = document.getElementById('loader-text2');
    if (loaderText2) {
        loaderText2.textContent = `Carregant fitxers (${fitxersLlegits}/${nombresDeFitxers+1})`; //+1 per si de cas es queda penjat, que no quedi 10/10
    }

    try {
        await carregarVersions();

        // Tot d'una tirada i en paral·lel: les paraules, les columnes del
        // diccionari i la rima de TOTS els dialectes. Un sol Promise.all i no
        // pas un per grup, perquè així el navegador fa la cua ell sol i no hi
        // ha cap fase que s'esperi l'anterior sense necessitat.
        //
        // Baixar-los tots d'entrada és el que fa que triar un altre dialecte
        // sigui immediat: si es baixessin quan es demanen, cada clic a la tira
        // voldria dir esperar-se uns quants MB.
        const feinesDeRima = CODIS_DE_DIALECTE.flatMap(codi =>
            COLUMNES_DE_RIMA.map(numero =>
                carregarColumnaInternada(numero, codi).then(columna => ({ codi, numero, columna }))));

        const carregat = await Promise.all([
            llegirFitxerAmbIndexedDB(CAMI_PARAULES),
            ...COLUMNES_DEL_DICCIONARI.map(numero => carregarColumnaInternada(numero)),
            ...feinesDeRima
        ]);

        // El Promise.all torna les coses en el mateix ordre que se li han
        // demanat: primer les paraules, després tantes columnes com en té el
        // COLUMNES_DEL_DICCIONARI, i la resta són les de rima.
        const finalDelDiccionari = 1 + COLUMNES_DEL_DICCIONARI.length;
        array0 = carregat[0];
        [col1, col2, col5, col6, col7, col8] = carregat.slice(1, finalDelDiccionari);

        for (const { codi, numero, columna } of carregat.slice(finalDelDiccionari)) {
            if (!rimaPerDialecte[codi]) rimaPerDialecte[codi] = {};
            rimaPerDialecte[codi][numero] = columna;
        }

        prepararColumnes();

        // Si el dialecte desat s'hagués quedat sense carregar, tornaríem al
        // central abans de deixar cercar: sense col3 ni col4 no hi ha cerca
        // possible.
        if (!aplicarDialecte(dialecteActiu)) aplicarDialecte(DIALECTE_PER_DEFECTE);
        marcarDialecteTriat();

        console.log('Tots els fitxers carregats correctament');

        document.getElementById("loader").style.display = "none";

        // Va aquí i no pas al principi del DOMContentLoaded: la cerca
        // necessita el diccionari llegit i indexat, que és justament el que
        // s'acaba de fer. Dins el try, perquè si la càrrega ha petat no hi ha
        // res per on cercar.
        cercarDesDeLaURL();
    } catch (error) {
        Debug.logError('Error en carregar els fitxers:', error);
        document.getElementById("loader").style.display = "none";
    } finally {
        Debug.logTimeEnd('Temps de càrrega');
    }
});


// --- FUNCIONS INDEXEDDB ---
// Versió 2: abans aquí s'hi desava el text tal com baixava del servidor i es
// tornava a interpretar a cada visita. Ara s'hi desa ja interpretat (la llista
// de paraules feta, els índexs com a array de nombres), que és el que estalvia
// la feina. Com que el que hi ha a dins canvia de forma però les claus i les
// versions es diuen igual, el codi nou llegiria text on ara espera estructures:
// per això puja el número i es buida la caixa. Els visitants de sempre es
// tornen a baixar el diccionari una vegada i s'acaba.
function obrirIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('rimadorDB', 2);
        request.onerror = () => reject(null);
        request.onsuccess = () => resolve(request.result);
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (db.objectStoreNames.contains('fitxers')) {
                db.deleteObjectStore('fitxers');
            }
            db.createObjectStore('fitxers', { keyPath: 'nom' });
        };
    });
}

function recuperarFitxer(db, nom) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('fitxers', 'readonly');
        const store = tx.objectStore('fitxers');
        const req = store.get(nom);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(null);
    });
}

function guardarFitxer(db, nom, contingut, versio) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('fitxers', 'readwrite');
        const store = tx.objectStore('fitxers');
        store.put({ nom, contingut, versio });
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject();
    });
}

// LECTURA AMB INDEXEDDB + VERSIÓ + BACKUP
// `processar` diu què s'ha de fer amb el text un cop el tenim. Per defecte,
// partir-lo per línies com sempre; els fitxers d'índexs passen el seu, que els
// converteix en un array de nombres sense crear cap objecte de text pel camí.
async function llegirFitxerAmbIndexedDB(rutaFitxer, processar = processarFitxerDeText) {
  const nomFitxer = rutaFitxer.split("/").pop();
  const versioActual = VERSIONS_FITXERS[nomFitxer];

  const comptarFitxer = () => {
    fitxersLlegits++;
    const loaderText2 = document.getElementById("loader-text2");
    if (loaderText2) {
      loaderText2.textContent = `Carregant fitxers (${fitxersLlegits}/${nombresDeFitxers+1})`; //+1 per si de cas es queda penjat, que no quedi 10/10
    }
  };

  try {
    // Sense una versió de confiança no sabem si la còpia guardada encara
    // val: la baixem del servidor i no en desem cap (ho fa el catch).
    if (!versioActual) throw new Error(`Sense versió per a ${nomFitxer}`);

    const db = await obrirIndexedDB();
    if (!db) throw new Error("IndexedDB no disponible");

    const fitxerDesat = await recuperarFitxer(db, nomFitxer); 
    const versioGuardada = fitxerDesat ? fitxerDesat.versio : "cap";

    // El que hi ha desat ja està interpretat: es torna tal com surt, sense
    // tornar a partir cap text ni tornar a llegir cap xifra.
    if (fitxerDesat && fitxerDesat.versio === versioActual) {
      console.log(`[${nomFitxer}] Carregat d'IndexedDB (${versioGuardada} = ${versioActual})`);
      comptarFitxer();
      return fitxerDesat.contingut;
    }

    console.log(`[${nomFitxer}] obsolet o no guardat, fent fetch i guardant arxiu a IndexedDB (${versioGuardada} =/= ${versioActual})`);
    const contingut = await fetchFitxer(rutaFitxer);
    const interpretat = processar(contingut);
    await guardarFitxer(db, nomFitxer, interpretat, versioActual);

    comptarFitxer();
    return interpretat;

  } catch (err) {
    Debug.logError(`IndexedDB fallida per ${nomFitxer}, intentant fetch directe`);
    const errorMsg = document.getElementById("error-msg"); 
    if (errorMsg) errorMsg.textContent = `Problema amb cache. Carregant ${nomFitxer} manualment.`;

    const contingut = await fetchFitxer(rutaFitxer);
    comptarFitxer();
    return processar(contingut);
  }
}

// FETCH NORMAL
async function fetchFitxer(url) {
    const nomFitxer = url.split("/").pop();
    // Si no sabem la versió (versions.json ha fallat), posem un valor
    // sempre diferent perquè el navegador tampoc no ens doni una còpia
    // seva que podria ser vella.
    const versio = VERSIONS_FITXERS[nomFitxer] || `sense-versio-${Date.now()}`;
    const response = await fetch(`${url}?v=${versio}`);
    if (!response.ok) throw new Error(`Error en llegir ${url}`);
    return await response.text();
}

// PROCESSAR TXT
function processarFitxerDeText(contingut) {
    return contingut.split('\n');
}

// NETEJAR INDEXEDDB
function netejarIndexedDB() {
    const request = indexedDB.deleteDatabase('rimadorDB');
    request.onsuccess = () => console.log('IndexedDB esborrat correctament');
    request.onerror = () => console.error('Error en esborrar IndexedDB');
    request.onblocked = () => console.warn("L'esborrat d'IndexedDB està bloquejat");
}
  

// event listener per la tecla enter
const inputParaula = document.getElementById('paraulaCercada');
if (inputParaula) {
  inputParaula.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      realitzarCerca();
    }
  });
}


//Botó:
const cercaButton = document.getElementById('cercaButton');
if (cercaButton) {
  cercaButton.addEventListener('click', realitzarCerca);
}


// --- LA TIRA PER TRIAR EL DIALECTE ---
// La pinta el js/components.js a partir de la seva llista DIALECTES; el que
// fa és cosa d'aquí, que és qui té les columnes.

function botonsDeDialecte() {
  return document.querySelectorAll('#dialectes .dialecte');
}

// Quina pastilla surt marcada. El components.js sempre pinta el central, o
// sigui que si de l'altre cop en va quedar un altre de desat, es corregeix
// aquí. Passa abans del primer pintat (tots dos fitxers són defer i aquest va
// just darrere), i per tant no es veu cap salt.
function marcarDialecteTriat() {
  botonsDeDialecte().forEach(boto => {
    const es = boto.dataset.dialecte === dialecteActiu;
    boto.classList.toggle('triat', es);
    boto.setAttribute('aria-checked', es ? 'true' : 'false');
  });
}

function lligarTriaDeDialecte() {
  const botons = botonsDeDialecte();
  if (!botons.length) return; // pàgines sense tira: llistes, dades, error...

  marcarDialecteTriat();

  botons.forEach(boto => {
    boto.addEventListener('click', () => {
      const codi = boto.dataset.dialecte;
      if (codi === dialecteActiu) return;

      // Mentre el diccionari es carrega, el loader tapa la pantalla sencera
      // (z-index 99999 a css/loader.scss) i aquí no hi arriba cap clic. Tot i
      // així ho comprovem: si la rima encara no hi fos, val més no fer res
      // que deixar la pastilla canviada i les rimes de l'altre dialecte.
      if (!aplicarDialecte(codi)) return;

      marcarDialecteTriat();
      try {
        localStorage.setItem(CLAU_DIALECTE, codi);
      } catch (err) {
        // Mode privat: la tria val per a aquesta visita i prou.
      }

      // Els resultats que hi ha a la pantalla són de l'altre dialecte i ja no
      // valen. Es torna a cercar el mateix, tal com si es tornés a pitjar el
      // botó. Si no s'ha cercat mai, o si el camp s'ha buidat mentrestant, no
      // hi ha res per refer: cercar el buit no tornaria res i esborraria de la
      // pantalla l'única cosa que hi havia.
      const resultats = document.getElementById('rima_enllac');
      const camp = document.getElementById('paraulaCercada');
      if (resultats && resultats.innerHTML.trim() && camp && camp.value.trim()) {
        realitzarCerca();
      }
    });
  });
}

lligarTriaDeDialecte();

// El botó de compartir la cerca a X (Twitter).
//
// Només surt quan la cerca ha trobat la paraula al diccionari: si no s'ha
// trobat no hi ha res per anar a consultar i el piulet convidaria a obrir una
// pàgina buida. Es refà a cada cerca, que és quan pot canviar res del que hi
// diu: el número que dona no depèn de les caselles (vegeu-ho més avall).
//
// L'adreça és la d'intenció de X. El twitter.com/intent/tweet de sempre encara
// hi redirigeix, però fem servir la d'ara per no dependre del salt; si mai
// canvia, es canvia aquí i a l'href de l'index.html i prou.
function actualitzarBotoCompartir() {
  const boto = document.getElementById('compartirButton');
  if (!boto) return;

  const paraula = paraulacerca[0];
  if (paraula === 0) {
    boto.hidden = true;
    return;
  }

  let piulet;

  // Les nàufragues només ho són en rima consonant: en assonant rimen com
  // qualsevol altra paraula, i aleshores el piulet ha de ser el de sempre. És
  // la mateixa condició que decideix què s'ensenya a la pantalla (vegeu
  // l'actualitzarRimes), i per força ha de dir el mateix que ella.
  const tipusRima = document.getElementById('rimaSelector').value;

  if (paraulaEsNaufraga && tipusRima === 'r.consonant') {
    piulet = "He trobat una paraula nàufraga! '" + paraula + "' no rima " +
             "consonantment amb cap altra paraula del diccionari. Descobreix " +
             "totes les altres: rimador.cat/llistes/llista_naufragues.html";

  } else {
    // matches i no pas matches_provisionals, que és el que es veu a la
    // pantalla: el piulet ha de dir quantes rimes té la paraula amb totes les
    // caselles marcades. Si comptés les que es veuen, qui obrís l'enllaç en
    // trobaria unes altres, perquè hi arriba amb els filtres per estrenar.
    const quantes = matches.length;
    const compte = quantes === 1 ? "1 rima" : quantes + " rimes";

    const esAssonant = tipusRima === 'r.assonant';

    // La paraula hi va dues vegades i de dues maneres: dins el text, tal com
    // s'escriu, i dins l'enllaç, codificada. L'encodeURIComponent no toca res
    // si la paraula és tota ASCII, o sigui que l'adreça només s'embruta quan
    // no hi ha manera de fer-ho altrament ('cançó' -> 'can%C3%A7%C3%B3').
    //
    // El &rima= només hi surt quan és assonant: la consonant ja és la que surt
    // si no s'hi posa res (vegeu cercarDesDeLaURL), i posar-l'hi només faria
    // l'enllaç més llarg per no dir res de nou.
    const adreca = "rimador.cat/?q=" + encodeURIComponent(paraula) +
                   (esAssonant ? "&rima=assonant" : "");

    piulet = "He cercat " + (esAssonant ? "assonantment" : "consonantment") +
             " '" + paraula + "' al rimador.cat i té " + compte + "! " +
             "Consulta-les totes a " + adreca;
  }

  boto.href = 'https://x.com/intent/post?text=' + encodeURIComponent(piulet);
  boto.hidden = false;
}

// Cerca demanada des de l'adreça: rimador.cat/?q=paraula
//
// Serveix per a dues coses. La primera, poder enllaçar una cerca concreta
// (compartir-la, desar-la, posar-la de cercador al navegador). La segona, que
// el SearchAction del JSON-LD de l'index.html digui la veritat: allà hi ha
// declarat exactament aquest patró d'URL, i sense això seria una mentida —
// l'adreça obriria la pàgina d'inici buida i no cercaria res.
//
// Només omple el camp i pitja el botó: tota la feina la fa el realitzarCerca
// de sempre, amb els filtres tal com els deixa el components.js. No toca la
// barra d'adreces quan es cerca des del formulari; el ?q= és una porta
// d'entrada, no un estat que la pàgina vagi mantenint.
function cercarDesDeLaURL() {
  const parametres = new URLSearchParams(window.location.search);

  const paraula = parametres.get('q');
  if (!paraula || !paraula.trim()) return;

  const camp = document.getElementById('paraulaCercada');
  if (!camp) return;

  // El tipus de rima és opcional i l'única cosa que s'hi entén és 'assonant':
  // qualsevol altra cosa (o no posar-hi res) deixa el desplegable tal com ve,
  // que és amb la consonant triada (vegeu opcionsRima a js/components.js).
  // Així una adreça mal escrita no es queda sense cercar, només cerca com de
  // costum.
  const selector = document.getElementById('rimaSelector');
  if (selector && (parametres.get('rima') || '').trim().toLowerCase() === 'assonant') {
    selector.value = 'r.assonant';
  }

  camp.value = paraula.trim();
  realitzarCerca();
}

const CriterisNoms = {
  ...crearCriteris('Noms', 'N'),
  ...crearCriteris('Propis', 'NP'),
  ...crearCriteris('Comuns', 'NC'),
};

const CriterisVerbs = {
  ...crearCriteris('Verbs', 'V'),
  ...crearCriterisTriples('Indicatiu', 'VAI', 'VSI', 'VMI' ),
  ...crearCriterisTriples('Subjuntiu', 'VAS', 'VSS', 'VMS'),
  ...crearCriterisTriples('Imperatiu', 'VAM', 'VSM', 'VMM'),
  ...crearCriterisTriples('Gerundis', 'VAG', 'VSG', 'VMG'),
  ...crearCriterisTriples('Participis', 'VAP', 'VSP', 'VMP'),
  ...crearCriterisTriples('Infinitius', 'VAN', 'VSN', 'VMN'),
  ...crearCriterisTriples('Condicional', 'VAC', 'VSC', 'VMC' ),
};

const CriterisAdjectius = {
  ...crearCriteris('Adjectius', 'A'),
  ...crearCriteris('Qualificatius', 'AQ0'),
  ...crearCriteris('Superlatius', 'AQA'),
  ...crearCriteris('Ordinals', 'AO'),
};

const CriterisPronoms = {
  ...crearCriteris('Pronoms', 'P'),
  ...crearCriteris('Demostratius', 'PD'),
  ...crearCriteris('Indefinits', 'PI'),
  ...crearCriteris('Interrogatius / Exclamatius', 'PT'),
  ...crearCriterisDobles('Personals (forts i febles)', 'PP', 'P0'),
  ...crearCriteris('Possessius', 'PX'),
  ...crearCriteris('Relatius', 'PR'),
};

const CriterisDeterminants = {
  ...crearCriteris('Determinants', 'D'),
  ...crearCriteris('Números', 'DN'),
  ...crearCriteris('Articles', 'DA'),  
  ...crearCriteris('Relatius', 'DR'),
  ...crearCriteris('Interrogatius', 'DT'),
  ...crearCriteris('Demostratius', 'DD'),
  ...crearCriteris('Exclamatius', 'DE'),
  ...crearCriteris('Indefinits', 'DI'),
  ...crearCriteris('Possessius', 'DP'),
};

const CriterisAltres = {
  ...crearCriteris('Altres categories', 'Z'),
  ...crearCriteris('Adverbis', 'ZR'),
  ...crearCriteris('Conjuncions', 'ZC'),
  ...crearCriteris('Interjeccions', 'ZI'),
  ...crearCriteris('Preposicions', 'ZSPS'),
  ...crearCriteris('Contraccions', 'ZSP+'),
  ...crearCriteris('"etcètera"', 'ZF'),
};

function crearCriteris(nom, prefix) {  
  return {
      [`${nom}`]: {
          filterFunction: item => item[2].startsWith(`${prefix}`),},};
}

function crearCriterisDobles(nom, prefix1, prefix2) {
  return {
      [`${nom}`]: {
          filterFunction: item => item[2].startsWith(prefix1) || item[2].startsWith(prefix2),},};
}

function crearCriterisTriples(nom, prefix1, prefix2, prefix3) {
  return {
      [`${nom}`]: {
          filterFunction: item => item[2].startsWith(prefix1) || item[2].startsWith(prefix2) || item[2].startsWith(prefix3),},};
}



//excel per guardar cerques
const URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbw5uSetN-OKIEQjmEo9PFFJp0r7UclUnHEYhbkghbqQ4q7JnIM7i0Ljfa3W_Q7Z-s5f/exec";

// Les cerques només es registren des del web de debò: rimador.cat (el domini
// del CNAME) i rimador.github.io (l'adreça que GitHub Pages dona al
// repositori oficial). Al repositori de proves i en local, l'amfitrió no és
// cap d'aquests dos i no s'envia res, que és el que evita que les proves
// embrutin el full de càlcul.
//
// Va aquí fora i no dins de registrarCerca perquè l'amfitrió no canvia mentre
// la pàgina és oberta: no cal tornar-ho a mirar a cada cerca.
const ES_WEB_OFICIAL = window.location.hostname === 'rimador.cat'
                    || window.location.hostname === 'rimador.github.io';

function getUsuariID() {
  let usuariID = localStorage.getItem('rimador_usuari_id');
  if (!usuariID) {
    const temps = Date.now().toString(36);    
    const aleatori = Math.random().toString(36).substring(2, 7);
    usuariID = 'usr_' + temps + '_' + aleatori;
    localStorage.setItem('rimador_usuari_id', usuariID);
  }
  return usuariID;
}

function registrarCerca(paraulaBuscada, rimaTrobada, tipusRima, codiParaula, numeroSeleccionat, comenca, inclourePropis, inclourePlurals) {
  // Aquesta comprovació va la primera de totes. Abans era al final, just
  // abans del fetch, i per tant el web de proves i el navegador en local
  // arribaven a passar pel getUsuariID(), que fabrica un identificador
  // d'usuari i el desa al localStorage. Es creaven identificadors de
  // seguiment en llocs on no s'envia res i que no serviran mai per a res.
  if (!ES_WEB_OFICIAL) return;
  if (!paraulaBuscada || paraulaBuscada.trim().length < 2) return;

  const dades = new URLSearchParams();
  dades.append('paraula', paraulaBuscada.trim().toLowerCase());
  dades.append('rima', rimaTrobada || "***");
  dades.append('codi', codiParaula || "***");
  dades.append('numeroSilabes', numeroSeleccionat);
  dades.append('comencaPer', comenca);
  dades.append('inclourePropis', inclourePropis);
  dades.append('inclourePlurals', inclourePlurals);
  dades.append('tipusRima', tipusRima);
  dades.append('usuari', getUsuariID());

  fetch(URL_GOOGLE_SCRIPT, {
    method: 'POST',
    mode: 'no-cors',
    body: dades
  }).catch(error => console.log('Error silenciós', error));
}




//FUNCIONS PRINCIPALS

// Els resultats que hi ha ara mateix a la pantalla. Fins ara naixien
// sols, sense declarar enlloc, de la primera assignació que se'ls feia;
// això vol dir que amb el mode estricte el programa peta, i que una
// errada de tecleig en comptes de queixar-se crea una variable nova.
//
// - matches: tot el que ha trobat l'última cerca.
// - matches_provisionals: el subconjunt que passa el filtre de categories
//   de les caselles, que és el que s'imprimeix.
// - paraulacerca: la fila del diccionari de la paraula cercada.
// - codiParaula: la seva categoria gramatical.
//
// Van amb var i no amb let a posta: script_llistes.js les escriu com a
// window.matches, window.matches_provisionals i window.paraulacerca, i
// només var deixa la variable penjada del window. Amb let serien una
// variable del guió i les pàgines de llistes escriurien a un lloc que
// aquest fitxer no llegeix mai.
var matches = [];
var matches_provisionals = [];
var paraulacerca = [0, 0, 0, 0, 0, 0, 0];
var codiParaula = "";

// Mentre el diàleg d'homògrafs és obert, la cerca està a mitges. Si
// se'n comencés una altra, tindríem dues cerques en marxa i dos diàlegs
// oberts alhora. Amb el prompt() d'abans això no podia passar, perquè
// aturava tota la pàgina.
let cercaEnCurs = false;

async function realitzarCerca() {
  Debug.log("Botó clicat!");
  Debug.logTime('realitzarCerca');

  if (cercaEnCurs) {
    Debug.log("Ja hi ha una cerca en marxa; ignorem la nova.");
    return;
  }
  cercaEnCurs = true;

  document.getElementById("espai_inicial").style.display = "none";

  try {
    // Abans aquí hi havia `matches = []`. Ara que la cerca es pot aturar
    // esperant el diàleg d'homògrafs, buidar-ho d'entrada deixava la
    // pàgina en un estat incoherent mentre el diàleg era obert: a la
    // pantalla encara s'hi veien els resultats de la cerca anterior,
    // però la llista que els sosté era buida. Les substituïm de cop
    // quan les noves ja estan fetes (línia de sota del buscarParaula).
    var paraulaCercada = document.getElementById('paraulaCercada').value.trim().toLowerCase();
    var numeroSeleccionat = document.getElementById('numeroSelector').value;
    var tipusRima = document.getElementById('rimaSelector').value;
    var comença = document.getElementById('categoriaSelector').value;
    var inclourePropis = document.getElementById('nomsPropis').value;
    var inclourePlurals = document.getElementById('plurals').value;
    
    // Tota la feina va sota el loader. Aquí sí, i al clic de casella no,
    // perquè la cerca és l'única part que encara triga: pintar les rimes
    // per primera vegada són segons quan la rima és ampla. Amagar-ne unes
    // quantes després, en canvi, són mil·lisegons.
    //
    // El diàleg d'homògrafs, si surt, s'obre amb el loader apartat
    // (vegeu buscarParaula).
    await Loader.mentre("Cercant les rimes...", async () => {
      const buscaparaula = await buscarParaula(paraulaCercada, numeroSeleccionat, comença, tipusRima, inclourePropis, inclourePlurals);

      // null = s'ha tancat el diàleg d'homògrafs sense triar cap paraula.
      // No toquem res: ni els resultats de la pantalla ni el registre de
      // cerques.
      if (buscaparaula === null) {
        Debug.log("Cerca cancel·lada des del diàleg d'homògrafs.");
        return;
      }

      matches = buscaparaula[0];
      paraulacerca = buscaparaula[1];

      // lògica per a registrar les cerques
      let rimaTrobada = "***";

      if (paraulacerca[0] !== 0) {
          if (tipusRima === 'r.consonant') {
              rimaTrobada = paraulacerca[3];}
          else if (tipusRima === 'r.assonant') {
              rimaTrobada = paraulacerca[4];}
      }
      codiParaula = paraulacerca[2];

      registrarCerca(
            paraulaCercada,
            rimaTrobada,
            tipusRima,
            codiParaula,
            numeroSeleccionat,
            comença,
            inclourePropis,
            inclourePlurals
          );

      matches_provisionals = matches.slice();

      actualitzarRimes();
      var checkboxes = document.querySelectorAll('.clickable-checkbox');

      checkboxes.forEach(function(checkbox) {
        checkbox.checked = true;
      });

      mostrarTotesLesLlistes();
      document.querySelector('.impressio').style.display = 'flex';

      // Una cerca acabada compta com un dia d'ús per a l'avís periòdic
      // de donatius (avis/avis.js). És ell qui decideix si toca ensenyar
      // res o no; aquí només l'informem. Va aquí baix, i no al principi
      // de la funció, perquè només compti quan la cerca ha anat bé.
      if (window.AvisRimador) window.AvisRimador.registraUs();
    });

    Debug.logTimeEnd('realitzarCerca');
  } catch (error) {
    Debug.logError('Error en realitzar la cerca:', error);
  } finally {
    cercaEnCurs = false;
  }
}

function descriureCategoria(codi) {
  if (codi.startsWith("Y")) return "abreviació";
  if (codi.startsWith("CC")) return "conjunció";
  if (codi.startsWith("SP")) return "preposició";
  if (codi.startsWith("I")) return "interjecció";
  if (codi.startsWith("RG")) return "adverbi";
  if (codi.startsWith("V")) return "verb";
  if (codi.startsWith("N")) return "nom";
  if (codi.startsWith("A")) return "adjectiu";
  if (codi.startsWith("P")) return "pronom";
  if (codi.startsWith("D")) return "determinant";
  if (codi.startsWith("Z")) return "altre";
  return "altra categoria";
}

function obtenirPesJerarquia(codi) {
  if (!codi) return 10;
  if (codi.startsWith('NC')) return 1;
  if (codi.startsWith('A')) return 2;
  if (codi.startsWith('D')) return 3;
  if (codi.startsWith('P')) return 4;
  if (codi.startsWith('V')) return 5;
  if (codi.startsWith('R')) return 6;
  if (codi.startsWith('I')) return 7;
  if (codi.startsWith('CC')) return 8;
  if (codi.startsWith('NP')) return 9;
  return 10;
}

// Diàleg per triar entre paraules homògrafes ('dona', 'soc', 'coure'...).
// Abans això era un prompt() del navegador: una finestra que no es pot
// estilar de cap manera, o sigui que les transcripcions hi sortien amb
// la tipografia del sistema i cada aparell hi feia el que volia amb els
// caràcters de l'AFI. Fet a casa, hereta les fonts del web.
// Retorna una promesa amb l'opció triada, o amb null si es tanca sense
// triar res. Mai no tria per compte de l'usuari: si la cerca continués
// amb una opció posada per nosaltres, sortirien les rimes de l'altra
// paraula sense que ningú ho hagués demanat.
function triarHomograf(paraulaCercada, opcions) {
  return new Promise(resolve => {
    // Xarxa de seguretat per a navegadors sense <dialog> (iOS anterior
    // al 15.4): tornem al prompt() de tota la vida.
    if (typeof HTMLDialogElement === 'undefined' || !HTMLDialogElement.prototype.showModal) {
      const text = opcions.map(o => `${o.numero}: ${o.paraula} (${o.categoria}, ${o.arrel}) ${o.transcripcio}`).join("\n");
      const eleccio = parseInt(prompt(`Hi ha ${opcions.length} coincidències per "${paraulaCercada}".\nEscull una opció:\n\n${text}`));
      resolve(isNaN(eleccio) || eleccio <= 0 || eleccio > opcions.length ? null : opcions[eleccio - 1]);
      return;
    }

    const dialeg = document.createElement('dialog');
    dialeg.className = 'dialeg-homografs focus-inicial';

    const titol = document.createElement('h2');
    titol.textContent = `Quina "${paraulaCercada}" cerques?`;
    dialeg.appendChild(titol);

    const explicacio = document.createElement('p');
    explicacio.className = 'dialeg-explicacio';
    explicacio.textContent = `S'escriuen igual però es pronuncien de manera diferent, i per tant no rimen amb les mateixes paraules.`;
    dialeg.appendChild(explicacio);

    const llista = document.createElement('div');
    llista.className = 'dialeg-opcions';

    // Tanquem, netegem i responem sempre des d'aquí. No ens refiem de
    // l'esdeveniment 'close' del <dialog> (hi ha navegadors que no
    // l'envien, i llavors el diàleg es quedaria enganxat al document i
    // la cerca no acabaria mai).
    let tancat = false;

    const tancar = opcio => {
      if (tancat) return;
      tancat = true;
      dialeg.close();
      dialeg.remove();
      resolve(opcio);
    };

    opcions.forEach(opcio => {
      const boto = document.createElement('button');
      boto.type = 'button';
      boto.className = 'dialeg-opcio';

      const transcripcio = document.createElement('span');
      transcripcio.className = 'transcripcio dialeg-transcripcio';
      transcripcio.textContent = opcio.transcripcio;

      const detall = document.createElement('span');
      detall.className = 'dialeg-detall';
      detall.textContent = `${opcio.categoria}, ${opcio.arrel}`;

      boto.appendChild(transcripcio);
      boto.appendChild(detall);
      boto.addEventListener('click', () => tancar(opcio));

      llista.appendChild(boto);
    });

    dialeg.appendChild(llista);

    // Esc: es cancel·la la cerca sencera. No triem nosaltres cap opció.
    dialeg.addEventListener('cancel', event => {
      event.preventDefault();
      tancar(null);
    });
    dialeg.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        event.preventDefault();
        tancar(null);
      }
      // El primer keydown de debò (normalment Tab) vol dir que l'usuari
      // navega amb teclat: a partir d'aquí el contorn de focus ha de
      // funcionar amb normalitat. Vegeu la classe .focus-inicial a
      // css/dialeg.scss.
      dialeg.classList.remove('focus-inicial');
    });

    // Clic al fons fosc: també cancel·la. Compte, que event.target és el
    // <dialog> tant si es clica el fons com si es clica el farciment del
    // quadre o l'espai entre dues opcions; si no ho distingíssim, un toc
    // una mica desviat tancaria el diàleg com si fos un clic a fora.
    // Comparem les coordenades amb el rectangle del quadre.
    dialeg.addEventListener('click', event => {
      if (event.target !== dialeg) return;

      const caixa = dialeg.getBoundingClientRect();
      const aDins = event.clientX >= caixa.left && event.clientX <= caixa.right &&
                    event.clientY >= caixa.top && event.clientY <= caixa.bottom;

      if (!aDins) tancar(null);
    });

    document.body.appendChild(dialeg);
    dialeg.showModal();
    llista.querySelector('button').focus();
  });
}

// Les columnes no són paràmetres: es llegeixen d'on són. Ho eren, però passar-
// ho tot per la porta (les banderes empaquetades, els índexs de rima...) era
// una llista d'arguments que no deia res que no se sabés.
async function buscarParaula(paraulaCercada, numeroSeleccionat, comença, tipusRima, inclourePropis, inclourePlurals) {
  Debug.logTime('buscarParaula');

  // Aquesta era una variable global. Ara que la funció és asíncrona (s'atura
  // a esperar el diàleg d'homògrafs), dues cerques poden estar en marxa
  // alhora, i si totes dues hi escrivien els resultats es barrejaven: sortien
  // rimes d'una altra paraula. Cada cerca es guarda les seves i les retorna
  // al final.
  let llistaParaulaCerca;
  const matches = [];

  // Quina fila del diccionari és la paraula que s'ha cercat, o -1 si no hi és.
  // Ens la guardem perquè és d'on surt el número de la rima que hem de buscar.
  let filaTrobada = -1;

  // Abans això era un .map() que fabricava 619.783 objectes { paraula, index }
  // a cada cerca, només per trobar-ne un grapat. Un bucle normal fa la mateixa
  // feina sense deixar res per escombrar.
  const buscada = paraulaCercada.toLowerCase();
  const coincidencies = [];
  for (let i = 0; i < array0.length; i++) {
    if (array0[i].toLowerCase() === buscada) coincidencies.push(i);
  }

  // L'ordenació és estable, o sigui que les del mateix pes es queden en
  // l'ordre del diccionari, com abans.
  coincidencies.sort((a, b) => obtenirPesJerarquia(t2(a)) - obtenirPesJerarquia(t2(b)));

  if (coincidencies.length === 0) {
    llistaParaulaCerca = [0, 0, 0, 0, 0, 0, 0, 0, 0];

  } else if (coincidencies.length === 1) {
    var indexparaula = coincidencies[0];
    filaTrobada = indexparaula;
    llistaParaulaCerca = [
      array0[indexparaula], t1(indexparaula), t2(indexparaula),
      t3(indexparaula), t4(indexparaula), t5(indexparaula),
      t6(indexparaula), t7(indexparaula), t8(indexparaula)
    ];
  } else {
    // No fa falta la transcripció sencera de la col_9 per saber si aquestes
    // entrades "sonen igual": ens val que rimin igual, i això ja ho diu el
    // número de rima que porten col_3 (consonant) o col_4 (assonant), que
    // igualment es carreguen per cercar. És el mateix criteri que la cerca
    // fa servir més avall per triar les files candidates (vegeu la "rima").
    const columna = tipusRima === 'r.consonant' ? col3 : col4;
    const rimes = new Set(coincidencies.map(fila => columna.idx[fila]));

    // Si totes les entrades tenen el mateix número de rima, tant se val
    // quina agafem: no cal preguntar res. És el cas de gairebé totes les
    // paraules repetides.
    if (rimes.size === 1) {
      var indexparaula = coincidencies[0];
      filaTrobada = indexparaula;
      llistaParaulaCerca = [
        array0[indexparaula], t1(indexparaula), t2(indexparaula),
        t3(indexparaula), t4(indexparaula), t5(indexparaula),
        t6(indexparaula), t7(indexparaula), t8(indexparaula)
      ];
    } else {
      // Només oferim una opció per número de rima: si dues entrades rimen
      // igual (per exemple dues formes verbals de 'donar'), donarien
      // exactament les mateixes rimes i al diàleg hi sortirien dues opcions
      // idèntiques.
      const vistes = new Set();
      const opcions = [];

      coincidencies.forEach(index => {
        const seva = columna.idx[index];
        if (vistes.has(seva)) return;
        vistes.add(seva);

        const terminacio = tipusRima === 'r.consonant' ? t3(index) : t4(index);
        opcions.push({
          index,
          numero: opcions.length + 1,
          paraula: array0[index],
          arrel: t1(index),
          categoria: descriureCategoria(t2(index)),
          transcripcio: "/-" + terminacio + "/"
        });
      });

      // Amb el loader tapant la pantalla, el diàleg sortiria amb la roda
      // donant voltes al darrere i semblaria que encara carrega alguna
      // cosa. Mentre esperem que l'usuari triï, fora.
      const triada = await Loader.apartat(() => triarHomograf(paraulaCercada, opcions));

      // S'ha tancat el diàleg sense triar: la cerca s'atura aquí i la
      // pantalla es queda tal com estava. Abans agafàvem la primera
      // opció, i això volia dir ensenyar les rimes d'una altra paraula
      // (les de 'dona' nom quan potser volies el verb) sense avisar.
      if (!triada) return null;

      const indexparaula = triada.index;
      filaTrobada = indexparaula;
      llistaParaulaCerca = [
        array0[indexparaula], t1(indexparaula), t2(indexparaula),
        t3(indexparaula), t4(indexparaula), t5(indexparaula),
        t6(indexparaula), t7(indexparaula), t8(indexparaula)
      ];
    }
  }

  paraulaEsNaufraga = calcularSiEsNaufraga(filaTrobada);

  // Els filtres de síl·labes i de categoria no depenen de la paraula sinó del
  // seu valor de columna, i valors diferents només n'hi ha 15 i 337. En lloc
  // de fer la mateixa pregunta 619.783 vegades, es respon un cop per valor i
  // el bucle només mira la resposta a la taula.
  const silabesOK = new Uint8Array(col5.taula.length);
  for (let v = 0; v < col5.taula.length; v++) {
    const silabes = col5.taula[v];
    let passa = true;
    if (silabes !== numeroSeleccionat && numeroSeleccionat !== "0" && numeroSeleccionat !== "6") passa = false;
    if (numeroSeleccionat === "6" && parseInt(silabes) < 6) passa = false;
    silabesOK[v] = passa ? 1 : 0;
  }

  const codiOK = new Uint8Array(col2.taula.length);
  for (let v = 0; v < col2.taula.length; v++) {
    const codi = col2.taula[v];
    let passa = true;
    if (inclourePropis === 'no' && codi[0] === "N" && codi[1] === "P") passa = false;
    if (inclourePlurals === 'no') {
      if (codi[0] === "D" && codi[4] === "P") passa = false; //Determinants
      if (codi[0] === "A" && codi[4] === "P") passa = false; //Adjectius
      if (codi[0] === "N" && codi[3] === "P") passa = false; //Noms
      if (codi[0] === "P" && codi[4] === "P") passa = false; //Pronoms
    }
    codiOK[v] = passa ? 1 : 0;
  }

  // Quines files s'han de mirar. Amb l'índex de rimes no cal recórrer el
  // diccionari sencer: n'hi ha prou amb les files de la rima que busquem, que
  // en consonant són dues de mediana. I la rima es compara com a número, que
  // és el que hi ha guardat: no cal anar a buscar-ne el text.
  let candidates = null; // null = mirar-les totes, de la primera a l'última
  let desDe = 0;
  let finsA = array0.length;

  if (tipusRima === 'r.consonant' || tipusRima === 'r.assonant') {
    if (filaTrobada < 0) {
      finsA = 0; // la paraula no és al diccionari: no rima amb res
    } else {
      const columna = tipusRima === 'r.consonant' ? col3 : col4;
      const index = tipusRima === 'r.consonant' ? indexConsonant : indexAssonant;
      const rima = columna.idx[filaTrobada];
      candidates = index.files;
      desDe = index.inici[rima];
      finsA = index.inici[rima + 1];
    }
  }

  const vocalsValides = 'haeiouàèéíïòóúü';

  for (let k = desDe; k < finsA; k++) {
    const i = candidates ? candidates[k] : k;

    if (!silabesOK[col5.idx[i]]) continue;
    if (!codiOK[col2.idx[i]]) continue;

    const inicial = array0[i][0];
    if (comença === "vocal+h" && !vocalsValides.includes(inicial)) continue;
    if (comença === "consonant" && vocalsValides.includes(inicial)) continue;

    matches.push([array0[i], t1(i), t2(i), t5(i), t6(i), t7(i), t8(i)]); //no cal guardar les rimes (col3 i col4)
  }

  Debug.logTimeEnd('buscarParaula');
  return [matches, llistaParaulaCerca];
}

//gestió logos per a imprimir
//
// Els logos són el fons de l'enllaç (.logo-vicc, .logo-viq i .logo-diec a
// css/impressio.scss), no pas una imatge a dins. Una cerca ampla ensenya
// desenes de milers de rimes amb fins a tres enllaços cadascuna, i cada <img>
// era un element més del DOM i una feina més per al navegador abans de pintar
// res. Com que el dibuix no diu res que l'enllaç no digui, l'aria-label fa la
// feina que abans feia l'alt.
//
// Les ADRECES tampoc no s'imprimeixen: cada enllaç surt amb un href="#" i la
// bona s'hi posa el primer cop que el ratolí hi passa per sobre o que hi
// arriba el focus del teclat, coses que sempre passen abans del clic. Escrites
// a l'HTML eren una tercera part de tot el que el navegador havia de llegir, i
// de cent mil rimes la gent no en clica cap o en clica una.
const ADRECES = {
  'logo-vicc': 'https://ca.wiktionary.org/wiki/',
  'logo-viq': 'https://ca.wikipedia.org/wiki/',
  'logo-diec': 'https://dlc.iec.cat/Results?DecEntradaText='
};

function completarEnllac(event) {
  const enllac = event.target.closest ? event.target.closest('a.logo') : null;
  if (!enllac || enllac.dataset.fet) return;

  const fila = enllac.closest('li');
  const paraula = fila && fila.dataset.e;
  if (!paraula) return;

  for (const classe in ADRECES) {
    if (enllac.classList.contains(classe)) {
      enllac.href = ADRECES[classe] + paraula;
      enllac.target = '_blank';
      enllac.dataset.fet = '1';
      return;
    }
  }
}

let enllacosEscoltats = false;

function escoltarElsEnllacos() {
  if (enllacosEscoltats) return;
  const contenidor = document.getElementById('rima_enllac');
  if (!contenidor) return;
  // Un sol escoltador per a tot el contenidor: cent mil enllaços amb el seu
  // escoltador cadascun tornaria a ser el problema que estem evitant.
  contenidor.addEventListener('pointerover', completarEnllac);
  contenidor.addEventListener('focusin', completarEnllac);
  enllacosEscoltats = true;
}

function crearEnllacViccionari() {
  return '<a href="#" class="logo logo-vicc" aria-label="Viccionari"></a>';
}

function crearEnllacViquipedia() {
  return '<a href="#" class="logo logo-viq" aria-label="Viquipèdia"></a>';
}

function crearEnllacDiec() {
  return '<a href="#" class="logo logo-diec" aria-label="DIEC"></a>';
}


// El que s'ha imprès a la pantalla i que aplicarFiltres necessita per saber
// què amagar: quin número de classe té cada codi gramatical, i quins codis hi
// ha a cada grup de síl·labes. Val null quan el que hi ha imprès no és una
// llista de rimes (la paraula nàufraga, o el missatge de no trobada).
let impressio = null;

// El full d'estil que amaga les categories desmarcades. És sempre el mateix i
// se'n reescriu el contingut sencer a cada clic: una sola assignació.
let fullDeFiltres = null;

// Amb poques rimes, redueix el nombre de columnes (l'amplada es manté)
function aplicarNombreDeColumnes(contenidor, nombreResultats) {
  contenidor.classList.remove("cols-1", "cols-2", "cols-3");

  if (nombreResultats < 6) {
    contenidor.classList.add("cols-1");
  } else if (nombreResultats < 14) {
    contenidor.classList.add("cols-2");
  } else if (nombreResultats < 20) {
    contenidor.classList.add("cols-3");
  }
}

function textDelNombre() {
  // A la pàgina principal el rètol diu amb quina paraula es rima, que és la
  // pregunta que s'ha fet l'usuari. Surt la forma del diccionari
  // (paraulacerca[0]) i no pas la que s'ha escrit al camp: si algú cerca
  // "AMOR" o tria una homògrafa al diàleg, el rètol ensenya la paraula tal
  // com és al diccionari.
  //
  // Va amb innerHTML per la negreta, i no cal escapar res: paraulacerca[0]
  // surt del diccionari, no del que escriu l'usuari. Quan no s'ha trobat la
  // paraula val 0, i aleshores es queda el rètol de sempre, que acompanya el
  // missatge de "no s'ha trobat".
  if (idPagina === 'principal') {
    if (paraulacerca[0] === 0) {
      return "Nombre de rimes: " + matches_provisionals.length;
    }
    return "Paraules que rimen amb <strong>" + paraulacerca[0] + "</strong>: " + matches_provisionals.length;
  }

  let text = '';
  if (idPagina === 'llista') {
    if (dataLlista === 'naufragues') {
      text = 'de paraules nàufragues';
    } else if (dataLlista === 'mots_de7_real') {
      text = 'de paraules de set síl·labes';
    } else if (dataLlista === 'mots_de7_glosa') {
      text = "d'heptasíl·labs";
    }
  }
  return "Nombre " + text + ": " + matches_provisionals.length;
}

function actualitzarRimes() {
  Debug.logTime('actualitzarRimes');

  var numerorimes = textDelNombre();
  document.getElementById("nombre").innerHTML = numerorimes;

  actualitzarBotoCompartir();

  var rimesPerSilabes = {};
  var rima_enllac = "";

  var contenidorRimes = document.getElementById("rima_enllac");
  var checkboxContainer = document.getElementById("checkboxContainer");
  var resultatsContainer = document.querySelector(".resultats");

  var textNombre = document.getElementById("nombre");

  if (matches.length > 0) {
    var esNaufraga = paraulaEsNaufraga;
    var tipusRima = document.getElementById('rimaSelector').value;
    if (esNaufraga && tipusRima === 'r.consonant') {
      impressio = null;
      textNombre.innerHTML = ""; 

      contenidorRimes.classList.remove("column-container", "cols-1", "cols-2", "cols-3");

      if (checkboxContainer) checkboxContainer.style.display = "none";
      if (resultatsContainer) resultatsContainer.style.width = "100%";

      var isSober = document.documentElement.getAttribute("data-theme") === "sober";

      if (isSober) {       
        rima_enllac = /*html*/`
          <div class="alerta-naufraga" style="text-align: center; width: 100%; margin-top: 20px;">
            <p><strong>Has trobat una paraula nàufraga.</strong></p>
            <p>La paraula <strong>${paraulacerca[0]}</strong> no rima consonantment amb cap altra paraula del diccionari...</p>
            <p>Consulta la llista de <a id="enllaç" href="${ARREL}llistes/llista_naufragues.html" target="_blank">Paraules nàufragues</a></p>
          </div>
        `;  
      } else {
        rima_enllac = /*html*/`
          <div class="alerta-naufraga" style="
              background-color: #ffff00;
              border: 6px dashed #ff00ff;
              box-shadow: 10px 10px 0px #00ffff;
              padding: 25px;
              text-align: center;
              width: 80%;
              max-width: 600px;
              margin: 40px auto;
              font-family: var(--font-divertida);
              color: #0000cc;
              border-radius: 15px;
              transform: rotate(-1deg);
          ">
            <h2 style="color: #ff0000; text-shadow: 3px 3px 0px #00ff00; font-size: 28px; text-transform: uppercase; margin-top: 0;">Paraula nàufraga!!!</h2>
            <p style="font-size: 18px;">La paraula <strong style="font-size: 24px; color: #ff00ff; text-decoration: underline;">${paraulacerca[0]}</strong> no rima consonantment amb cap altra paraula del diccionari...</p>

            <div style="margin-top: 25px; background: #817f7f; padding: 10px; border-radius: 8px; border: 2px solid #00ffff;">
              <p style="font-weight: bold; font-size: 18px; color: white; margin: 0;">
                Consulta la llista de <a id="enllaçbrillant" href="${ARREL}llistes/llista_naufragues.html" target="_blank">Paraules nàufragues</a>
              </p>
            </div>
          </div>
        `;
      }
      
    } else {
        if (checkboxContainer) checkboxContainer.style.display = "";
        if (resultatsContainer) resultatsContainer.style.width = "";
        contenidorRimes.classList.add("column-container");

        // Es pinten TOTES les rimes trobades, no només les que passen el filtre
        // de categories d'ara mateix. Amagar-ne unes quantes passa a ser una
        // sola regla de CSS (vegeu aplicarFiltres). Abans, cada clic de casella
        // refeia l'HTML sencer: muntar-lo són mig segon i que el navegador se'l
        // torni a llegir, dos segons més.
        //
        // El que fa possible que una regla de CSS n'hi hagi prou: tots els
        // criteris de les caselles miren el codi gramatical i res més, o sigui
        // que dues rimes amb el mateix codi sempre hi entren i en surten
        // juntes. Amb una classe per codi n'hi ha prou per a totes.
        //
        // Els trossos de text s'apilen directament al seu grup de síl·labes. La
        // versió d'abans fabricava un objecte per rima només per reagrupar-les
        // i tot seguit els tornava a recórrer.
        const codis = new Map();
        const perSilabes = new Map();

        for (let i = 0; i < matches.length; i++) {
          const parts = matches[i];
          const codi = parts[2];

          let numCodi = codis.get(codi);
          if (numCodi === undefined) { numCodi = codis.size; codis.set(codi, numCodi); }

          let grup = perSilabes.get(parts[3]);
          if (!grup) { grup = { trossos: [], codis: new Set() }; perSilabes.set(parts[3], grup); }
          grup.codis.add(numCodi);

          // El data-e és la paraula amb què es munten les adreces dels enllaços
          // (vegeu completarEnllac). No sempre és la que es veu: de cada cent
          // rimes, noranta-tres vénen d'una altra forma.
          let tros = "<li class='k" + numCodi + "' data-e=\"" + parts[1] + "\">" + parts[0];

          // Abans hi havia un <span class='classeParaula'> al voltant de la
          // paraula. No el gastava ningú: no hi ha cap regla de CSS que el miri.
          if (codi[0] === "V") tros += "<span class='classeParaulaMare'> (" + parts[1] + ") </span>";

          if (parts[4] === "Vicc") tros += " " + crearEnllacViccionari();
          if (parts[5] === "Viq") tros += " " + crearEnllacViquipedia();
          if (parts[6] === "Diec") tros += " " + crearEnllacDiec();

          grup.trossos.push(tros + "</li>");
        }

        const grups = [];
        const ordenades = [...perSilabes.keys()].sort((a, b) => a - b);

        for (const sil of ordenades) {
          const grup = perSilabes.get(sil);
          const classe = "g" + grups.length;
          grups.push({ classe, codis: grup.codis });

          let titol = "";
          if (dataLlista === 'mots_de7_glosa') {
            if (sil == 7) titol = "7 síl·labes (mots aguts):";
            else if (sil == 8) titol = "8 síl·labes (mots plans):";
            else if (sil == 9) titol = "9 síl·labes (mots esdrúixols):";
          } else {
            titol = sil + (sil > 1 ? " síl·labes" : " síl·laba") + ":";
          }

          // El <br> el treu el CSS al primer títol que es veu, que no sempre és
          // el mateix: depèn de quins grups hagin quedat buits pel filtre.
          if (titol) rima_enllac += "<h3 class='" + classe + "'><br class='salt'>" + titol + "</h3>";
          rima_enllac += "<ul class='" + classe + "'>" + grup.trossos.join("") + "</ul>";
        }

        // Surt quan les caselles ho amaguen tot. Va imprès des del principi
        // perquè ensenyar-lo també sigui cosa de la regla de CSS.
        rima_enllac += "<ul class='capRima'><li>Ets massa exigent! Aquesta paraula existeix i té més resultats, però per trobar-los hauràs de canviar els filtres</li></ul>";

        impressio = { codis, grups };
    }

  } else {
    impressio = null;
    textNombre.innerHTML = numerorimes;
    contenidorRimes.classList.remove("column-container", "cols-1", "cols-2", "cols-3");
    var rimes;
    if (paraulacerca[0] === 0) {
      if (checkboxContainer) checkboxContainer.style.display = "none";
      if (resultatsContainer) resultatsContainer.style.width = "100%";
      rimes = "<span class='missatgeNoTrobat'><br>No s'ha trobat la paraula al diccionari. Revisa l'ortografia i recorda cercar la paraula sencera, no la terminació.</span>";
    } else {
      if (checkboxContainer) checkboxContainer.style.display = "";
      if (resultatsContainer) resultatsContainer.style.width = "";
      rimes = "Ets massa exigent! Aquesta paraula existeix i té més resultats, però per trobar-los hauràs de canviar els filtres";
    }
    
    rima_enllac = "<ul><li>" + rimes + "</li></ul>";
  }

  document.getElementById("rima_enllac").innerHTML = rima_enllac;
  escoltarElsEnllacos();
  aplicarFiltres();

  Debug.logTimeEnd('actualitzarRimes');
}


// Amaga i ensenya les rimes segons les caselles marcades, sense tocar l'HTML:
// escriu una sola regla de CSS. Abans, cada clic refeia la llista sencera.
function aplicarFiltres() {
  const contenidorRimes = document.getElementById("rima_enllac");
  const textNombre = document.getElementById("nombre");
  if (textNombre && impressio) textNombre.innerHTML = textDelNombre();
  if (!impressio) return;

  Debug.logTime('aplicarFiltres');

  // Quins codis han quedat. Com que els criteris de les caselles només miren
  // el codi, saber quins codis hi ha és saber quines rimes s'han de veure.
  const visibles = new Set();
  for (let i = 0; i < matches_provisionals.length; i++) {
    const numero = impressio.codis.get(matches_provisionals[i][2]);
    if (numero !== undefined) visibles.add(numero);
  }

  const amagats = [];
  for (const numero of impressio.codis.values()) {
    if (!visibles.has(numero)) amagats.push(".k" + numero);
  }

  // Un grup de síl·labes que es queda sense cap rima visible perd el títol.
  let primerGrup = null;
  for (const grup of impressio.grups) {
    let enTeAlguna = false;
    for (const numero of grup.codis) {
      if (visibles.has(numero)) { enTeAlguna = true; break; }
    }
    if (!enTeAlguna) amagats.push("." + grup.classe);
    else if (!primerGrup) primerGrup = grup.classe;
  }

  // Les rimes s'amaguen amb content-visibility i no amb display:none. Totes
  // dues les treuen de la pantalla igual i el resultat es veu idèntic, però
  // display:none llença la feina que el navegador ja tenia feta per dibuixar-
  // les, i tornar-les a ensenyar vol dir tornar-la a fer de zero.
  // content-visibility:hidden se la guarda: el navegador se salta el
  // contingut però recorda com el tenia col·locat.
  //
  // Mesurat amb una llista d'aquestes mides, amagar-la i tornar-la a
  // ensenyar: amb display:none, 10.278 ms. Amb content-visibility, 2.000 ms
  // la primera vegada i 624 la segona, que és quan ja se'n recorda.
  //
  // L'alçada, els marges i el farciment es posen a zero perquè la rima amagada
  // no deixi el seu forat: a diferència de display:none, la caixa hi continua
  // sent encara que no s'hi vegi res.
  const AMAGAR = "{content-visibility:hidden;contain-intrinsic-size:0;height:0;margin:0;padding:0}";

  const capRima = matches_provisionals.length === 0;
  let css = amagats.length ? "#rima_enllac " + amagats.join(",#rima_enllac ") + AMAGAR : "";
  if (capRima) css += "#rima_enllac .capRima{display:block}";

  if (!fullDeFiltres) {
    fullDeFiltres = document.createElement("style");
    document.head.appendChild(fullDeFiltres);
  }
  fullDeFiltres.textContent = css;

  // El primer títol que es veu no porta el salt de línia de davant, i quin és
  // depèn de quins grups hagin quedat buits.
  const anterior = contenidorRimes.querySelector("h3.primer");
  if (anterior) anterior.classList.remove("primer");
  if (primerGrup) {
    const titol = contenidorRimes.querySelector("h3." + primerGrup);
    if (titol) titol.classList.add("primer");
  }

  contenidorRimes.classList.toggle("column-container", !capRima);
  aplicarNombreDeColumnes(contenidorRimes, matches_provisionals.length);

  Debug.logTimeEnd('aplicarFiltres');
}



function mostrarTotesLesLlistes() {
  Debug.logTime('mostrarTotesLesLlistes');

  var resultats = obtenirValorsSegonsPrimerCaracter(matches)

  mostrarLlista('noms', resultats.resultatsN, 'checkbox1');
  mostrarLlista('adjectius', resultats.resultatsA, 'checkbox2');
  mostrarLlista('verbs', resultats.resultatsV, 'checkbox3');
  mostrarLlista('determinants', resultats.resultatsD, 'checkbox4');
  mostrarLlista('pronoms', resultats.resultatsP, 'checkbox5');
  mostrarLlista('altres', resultats.resultatsAlt, 'checkbox6');

  Debug.logTimeEnd('mostrarTotesLesLlistes');
}

function mostrarLlista(tipusLlista, elementsAMostrar, checkboxId) {
  Debug.logTime('mostrarLlista');

  var titleSelector = '#' + checkboxId;
  var listSelector = '#' + tipusLlista + 'List';

  var listTitle = document.querySelector(titleSelector);
  var list = document.querySelector(listSelector);

  if (listTitle && list) {
      listTitle.parentElement.style.display = elementsAMostrar.length > 0 ? 'block' : 'none';
      list.style.display = elementsAMostrar.length > 0 ? 'block' : 'none';

      var elementsDeLlista = list.querySelectorAll('li');

      elementsDeLlista.forEach(function (element, index) {
          element.style.display = 'none';
      });

      elementsAMostrar.forEach(function (indexToShow) {
          if (indexToShow < elementsDeLlista.length) {
              elementsDeLlista[indexToShow].style.display = 'list-item';
          }
      });

  } else {
      Debug.log('No es compleixen les condicions per entrar a la lògica principal');
  }
  Debug.logTimeEnd('mostrarLlista');
}


function toggleList(listID, checkboxID) {
  Debug.logTime('toggleList');

  var list = document.getElementById(listID);
  var checkboxTitle = document.getElementById(checkboxID);

  var checkboxes = list.querySelectorAll('input[type="checkbox"]');

  if (checkboxTitle.checked) {
    checkboxes.forEach(function (checkbox) {
      checkbox.checked = true;
    });
  } else {
    checkboxes.forEach(function (checkbox) {
      checkbox.checked = false;
    });
  }
  Debug.logTimeEnd('toggleList');
}


async function handleCheckboxClick(event, checkboxCriteria) {
  Debug.logTime('handleCheckboxClick');

  if (event.target.type === 'checkbox') {
      // textContent, no pas innerText. Tots dos donen la mateixa paraula
      // ("Verbs", "Propis"...), però innerText promet el text tal com es
      // veu, i per poder-ho prometre el navegador ha de tenir la pàgina
      // ben col·locada: en demanar-lo, atura tot i recalcula la
      // disposició sencera. Amb cent mil rimes repartides en columnes
      // això eren vint segons per llegir una etiqueta que ja tenim
      // escrita a l'HTML. El textContent el llegeix de l'arbre i prou.
      const checkboxLabel = event.target.parentNode.textContent.trim();

      const elementLi = event.target.closest('li');
      if (elementLi) {
          const elementUl = elementLi.closest('ul');
          if (elementUl) {
              const casellesMarcadesVisibles = Array.from(elementUl.querySelectorAll('li')).filter(li => {
                  if (li.style.display === 'none') return false;
                  const input = li.querySelector('input[type="checkbox"]');
                  return input && input.checked;
              });
              
              const checkboxPrincipal = document.querySelector(`input[onchange*="${elementUl.id}"]`);
              
              if (checkboxPrincipal) {
                  checkboxPrincipal.checked = casellesMarcadesVisibles.length > 0;
              }
          }
      }


      if (checkboxLabel in checkboxCriteria) {
          const { filterFunction } = checkboxCriteria[checkboxLabel];

          // Sense loader. En tenia un, amb un llindar de deu mil rimes, de
          // quan clicar una casella volia dir refer la llista sencera i podia
          // trigar segons. Ara que amagar-les és una regla de CSS, la feina
          // més llarga que s'ha mesurat són 46 mil·lisegons: el loader només
          // hi feia una pampalluga negra.
          if (event.target.checked) {
              // Unió del que ja hi havia amb el que acaba d'entrar, d'una
              // sola passada i ordenat com el diccionari.
              //
              // Abans això es feia amb un includes() per cada resultat nou
              // i un sort() que a dins hi tenia un indexOf(): totes dues
              // coses recorren la llista sencera cada vegada. Amb una rima
              // ampla (n'hi ha que passen de les cent mil paraules) volia
              // dir milers de milions de comparacions per un sol clic, i
              // el navegador es quedava penjat.
              const inclosos = new Set(matches_provisionals);
              for (let i = 0; i < matches.length; i++) {
                  if (filterFunction(matches[i])) inclosos.add(matches[i]);
              }
              matches_provisionals = matches.filter(item => inclosos.has(item));

              Debug.log(`Checkbox "${checkboxLabel}" marcada`);

          } else {
              Debug.log(`Checkbox "${checkboxLabel}" desclicat`);
              matches_provisionals = matches_provisionals.filter(item => !filterFunction(item));
          }

          aplicarFiltres();
  }   }
  Debug.logTimeEnd('handleCheckboxClick');
}


function obtenirValorsSegonsPrimerCaracter(matches) {
  Debug.logTime('obtenirValorsSegonsPrimerCaracter');

  var resultatsN = [];
  var resultatsA = [];
  var resultatsV = [];
  var resultatsD = [];
  var resultatsP = [];
  var resultatsAlt = [];

  for (var i = 0; i < matches.length; i++) {
      var terceraColumna = matches[i][2];
      var primerCaracter = terceraColumna.charAt(0);
      var segonCaracter = terceraColumna.charAt(1);
      var tercerCaracter = terceraColumna.charAt(2);
      // Les preposicions (ZSPS) i les contraccions (ZSP+) es distingeixen per
      // la QUARTA lletra del codi, no per la tercera: totes dues tenen una P
      // a la tercera. Mirant-hi el tercerCaracter no s'hi acomplia mai cap
      // dels dos casos i les dues subcaselles no s'ensenyaven mai, tot i que
      // les paraules (a, amb, de, per, sense, al, del, pel...) sí que
      // s'imprimien a les rimes.
      var quartCaracter = terceraColumna.charAt(3);

      switch (primerCaracter) {   
          
          case "N": // Noms
              switch (segonCaracter) {
                  case "P": resultatsN.push(0); break; // Propis
                  case "C": resultatsN.push(1); break; // Comuns
              }
              break;

          case "A": // Adjectius
              switch (segonCaracter) {
                  case "Q": // Adjectius
                    switch (tercerCaracter) {
                        case "0": resultatsA.push(0); break; // Qualificatius
                        case "A": resultatsA.push(1); break; // Superlatius
                    }
                    break;
                  case "O": resultatsA.push(2); break; // Ordinals
              }
              break;
          
          case "V": // Verbs
              switch (tercerCaracter) {
                  case "I": resultatsV.push(0); break; // Indicatiu
                  case "S": resultatsV.push(1); break; // Subjuntiu
                  case "M": resultatsV.push(2); break; // Imperatiu
                  case "G": resultatsV.push(3); break; // Gerundi
                  case "P": resultatsV.push(4); break; // Participi
                  case "N": resultatsV.push(5); break; // Infinitiu
                  case "C": resultatsV.push(6); break; // Condicional

              }
              break; 
          
          case "D": // Determinants
              switch (segonCaracter) {
                  case "N": resultatsD.push(0); break; // Números
                  case "A": resultatsD.push(1); break; // Articles
                  case "R": resultatsD.push(2); break; // Relatius
                  case "T": resultatsD.push(3); break; // Interrogatius
                  case "D": resultatsD.push(4); break; // Demostratius
                  case "E": resultatsD.push(5); break; // Exclamatius
                  case "I": resultatsD.push(6); break; // Indefinits
                  case "P": resultatsD.push(7); break; // Possessius
              }
              break;

          case "P": // Pronoms
              switch (segonCaracter) {
                  case "D": resultatsP.push(0); break; // Demostratius
                  case "I": resultatsP.push(1); break; // Indefinits
                  case "T": resultatsP.push(2); break; // Interrogatius / Exclamatius
                  case "P": case "0": resultatsP.push(3); break; // Personals
                  case "X": resultatsP.push(4); break; // Possessius
                  case "R": resultatsP.push(5); break; // Relatius
              }
              break;

          case "Z": // Altres
              switch (segonCaracter) {
                  case "R": resultatsAlt.push(0); break; // Adverbis
                  case "C": resultatsAlt.push(1); break; // Conjuncions
                  case "I": resultatsAlt.push(2); break; // Interjeccions
                  case "F": resultatsAlt.push(5); break; // "etcètera"
              }
              if (segonCaracter === "S") {
                  switch (quartCaracter) {
                      case "S": resultatsAlt.push(3); break; // Preposicions
                      case "+": resultatsAlt.push(4); break; // Contraccions
                  }
              }
              break;
      }
  }

  Debug.logTimeEnd('obtenirValorsSegonsPrimerCaracter');
  return {
      resultatsN: resultatsN,
      resultatsA: resultatsA,
      resultatsV: resultatsV,
      resultatsD: resultatsD,
      resultatsP: resultatsP,
      resultatsAlt: resultatsAlt,
  };
}

// ============================================================= //
// ============================================================= //

//CSS
function ajustarPosicionsSticky() {
  var container = document.getElementById('container');
  var checkboxContainer = document.getElementById('checkboxContainer');
  var separador_rosa2 = document.getElementById('separador_rosa2');
  
  if (!container || !checkboxContainer || !separador_rosa2) return;
  
  var calculTop = 40 + container.offsetHeight;
  
  separador_rosa2.style.top = calculTop + 'px';
  checkboxContainer.style.top = (calculTop + 40) + 'px'; 
}

document.addEventListener('DOMContentLoaded', ajustarPosicionsSticky);

var observer = new ResizeObserver(function() {
    ajustarPosicionsSticky();
});

var containerEl = document.getElementById('container');
if (containerEl) {
    observer.observe(containerEl);
}

// ============================================================= //
// ============================================================= //

// boring style
const THEME_STORAGE_KEY = "rimadorTheme";

let colorFestiuOriginal = null;

function aplicarTema(tema) {
  var peixetImg = document.getElementById("peixetImg");
  var rimadorImg = document.getElementById("rimadorImg");
  var themeColorMeta = document.getElementById("themeColor");

  if (themeColorMeta && !colorFestiuOriginal) {
    colorFestiuOriginal = themeColorMeta.getAttribute("content");
  }

  // La ruta dels assets surt de components.js, només s'ha de tocar allà
  const ruta = ruta1;

  if (tema === "sober") {
    document.documentElement.setAttribute("data-theme", "sober");
    if (peixetImg) {
      peixetImg.src = ruta + "boringlogo.webp?v=2";
      peixetImg.alt = "Logo (mode sobri)";
    }
    if (rimadorImg) {
      rimadorImg.src = ruta + "Rimador-1-sober.webp?v=1";
      rimadorImg.alt = "El Rimador.cat (mode sobri)";
    }
    if (themeColorMeta) {
      themeColorMeta.setAttribute("content", "#e6e4e5");
    }
  } else {
    document.documentElement.removeAttribute("data-theme");
    if (peixetImg) {
      peixetImg.src = ruta + "peixet.webp?v=1";
      peixetImg.alt = "Peixet decoratiu";
    }
    if (rimadorImg) {
      rimadorImg.src = ruta + "Rimador-1.webp?v=1";
      rimadorImg.alt = "Logo del Rimador.cat";
    }
    if (themeColorMeta && colorFestiuOriginal) {
      themeColorMeta.setAttribute("content", colorFestiuOriginal);
    }
  }
}

function toggleTheme() {
  var temaActual = localStorage.getItem(THEME_STORAGE_KEY) === "sober" ? "sober" : "festiu";
  var temaNou = temaActual === "sober" ? "festiu" : "sober";

  try {
    localStorage.setItem(THEME_STORAGE_KEY, temaNou);
  } catch (e) {
    console.error("No s'ha pogut desar el tema a localStorage", e);
  }

  aplicarTema(temaNou);
  if (document.querySelector('.alerta-naufraga')) {
      actualitzarRimes();
    }
  if (typeof actualitzarColorsGrafics === 'function') {
      actualitzarColorsGrafics();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  var temaDesat = null;
  try {
    temaDesat = localStorage.getItem(THEME_STORAGE_KEY);
  } catch (e) {}
  aplicarTema(temaDesat === "sober" ? "sober" : "festiu");
});

// ============================================================= //
// ============================================================= //

