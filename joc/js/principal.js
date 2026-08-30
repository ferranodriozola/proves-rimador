// Fil conductor del joc: enllaça les pantalles amb el motor i amb les dades.
//
// EL ?v=dev DE LES IMPORTACIONS no és cap error: el deploy.yml el substitueix
// pels set primers caràcters del commit, igual que fa amb els ?v= dels HTML.
// Ha d'anar a cada importació perquè les importacions entre mòduls no hereten
// res de l'etiqueta <script> que carrega aquest fitxer: sense el ?v=, refrescar
// principal.js deixava els altres vuit mòduls a la memòria cau del navegador i
// es barrejaven versions.

import {
    carregarVersions, carregarIndex, indexDe, carregarDialecte,
    grupDeRimes, respostesValides, escoltarProgres,
} from './dades.js?v=dev';
import { clauAleatoria, clauDelDia, triarParaula } from './objectius.js?v=dev';
import { Partida, RESULTAT, formatarTemps } from './motor.js?v=dev';
import * as ui from './ui.js?v=dev';
import * as dialecte from './dialecte.js?v=dev';
import {
    avui, identificadorRecord, llegirRecord, desarRecord,
    resultatDiari, dificultatsJugades, desarResultatDiari,
    llegirTotsElsRecords, llegirSobrenom, desarSobrenom,
} from './magatzem.js?v=dev';
import { textPerCompartir, compartirResultat } from './compartir.js?v=dev';
import {
    validarSobrenom, enviarPuntuacio, estaConfigurat,
    carregarClassificacio,
} from './classificacio.js?v=dev';

const SEGONS_DIARIA = 60;
const NOM_DIFICULTAT = { facil: 'fàcil', dificil: 'difícil' };

// Si el versions.json no es pot llegir, el joc encara ha de poder-se jugar en
// central, que és el que hi havia abans que se'n pogués triar cap.
const DIALECTES_DE_RESERVA = [{ codi: dialecte.DIALECTE_PER_DEFECTE, nom: 'Central' }];

const estat = {
    mode: 'illimitat',
    dificultat: 'facil',
    segons: 90,
    dialecte: dialecte.DIALECTE_PER_DEFECTE,
    partida: null,
    ultimResum: null,
    data: avui(),
};

let dialectes = DIALECTES_DE_RESERVA;
let opcionsDificultat = null;
let opcionsTemps = null;

// ------------------------------------------------------------------ Arrencada

ui.preparar();
opcionsDificultat = ui.grupOpcions(ui.el.opcionsDificultat, 'dificultat', (valor) => {
    estat.dificultat = valor;
    refrescarConfig();
});
opcionsTemps = ui.grupOpcions(ui.el.opcionsTemps, 'segons', (valor) => {
    estat.segons = Number(valor);
    refrescarConfig();
});

for (const boto of document.querySelectorAll('[data-mode]')) {
    boto.addEventListener('click', () => obrirConfig(boto.dataset.mode));
}
for (const boto of document.querySelectorAll('[data-accio="inici"]')) {
    boto.addEventListener('click', tornarAInici);
}
for (const boto of document.querySelectorAll('[data-vista]')) {
    boto.addEventListener('click', () => obrirVista(boto.dataset.vista));
}
for (const boto of document.querySelectorAll('.pestanya')) {
    boto.addEventListener('click', () => canviarPestanya(boto.dataset.taula));
}

ui.el.botoComencar.addEventListener('click', comencarPartida);
ui.el.botoRepetir.addEventListener('click', comencarPartida);
ui.el.botoCompartir.addEventListener('click', compartir);
ui.el.botoEnviarRecord.addEventListener('click', enviarARanquing);
ui.el.formulari.addEventListener('submit', enviarParaula);
// El formulari ja s'envia sol amb la tecla de retorn, pero ho deixem explicit
// com a js/cerca.js: hi ha teclats de mobil que no disparen l'enviament implicit.
ui.el.camp.addEventListener('keydown', (esdeveniment) => {
    if (esdeveniment.key === 'Enter') enviarParaula(esdeveniment);
});

arrencar();

/**
 * Quins dialectes hi ha i quin es juga. Ho diu dades/versions.json, que és
 * petit i el volem a punt abans que ningú premi cap botó; l'índex del dialecte
 * triat, tot seguit, pel mateix motiu.
 */
async function arrencar() {
    try {
        const versions = await carregarVersions();
        if (versions.dialectes && versions.dialectes.length > 0) {
            dialectes = versions.dialectes;
        }
    } catch (error) {
        console.warn('No s\'ha pogut llegir el versions.json: es juga en central', error);
    }

    const codis = dialectes.map((d) => d.codi);
    ui.recordarNomsDeDialecte(dialectes);
    estat.dialecte = dialecte.inicial(codis);
    ui.pintarTiraDialectes(dialectes, estat.dialecte, triarDialecte);

    refrescarInici();
    precarregar(estat.dialecte);
}

/**
 * L'índex i el fitxer del dialecte, demanats sense esperar-los.
 *
 * El fitxer fa 1,9 MB comprimits i és el que abans es baixava per trossos. Es
 * comença ara, mentre l'usuari llegeix el menú i tria mode i rellotge, perquè
 * quan premi "Comença" ja hi sigui. Si encara no hi és, la partida l'esperarà
 * igualment: carregarDialecte guarda la promesa i no en fa dues descàrregues.
 */
function precarregar(codi) {
    carregarIndex().catch(() => {});
    carregarDialecte(codi).catch(() => {});
}

// ------------------------------------------------------------------ Dialecte

function triarDialecte(codi) {
    if (codi === estat.dialecte) return;

    estat.dialecte = codi;
    // Només ho desa la tira: el dialecte que arriba per l'adreça val per a
    // aquella visita i prou (vegeu dialecte.js).
    dialecte.desar(codi);
    dialecte.escriureALAdreca(codi);
    ui.marcarDialecte(codi);

    // Cada dialecte té la seva paraula del dia i els seus rècords, o sigui que
    // tot el que la pantalla diu d'això s'ha de tornar a mirar.
    refrescarInici();
    // I el fitxer del dialecte nou, a punt per quan comenci la partida.
    precarregar(codi);
}

// ------------------------------------------------------------------ Pantalles

function refrescarInici() {
    estat.data = avui();
    const jugades = dificultatsJugades(estat.data, estat.dialecte);
    const etiqueta = ui.el.etiquetaDiaria;

    if (jugades.length === 0) {
        etiqueta.hidden = true;
        return;
    }
    etiqueta.hidden = false;
    etiqueta.textContent = jugades.length === 2
        ? 'Avui ja l\'has jugada en totes dues dificultats'
        : `Avui ja l'has jugada en ${NOM_DIFICULTAT[jugades[0]]}`;
}

function tornarAInici() {
    aturarPartida();
    refrescarInici();
    ui.mostrarPantalla('inici');
}

function obrirVista(vista) {
    if (vista === 'records') obrirRecords();
    else if (vista === 'classificacio') obrirClassificacio();
}

// ------------------------------------------------------------- Els meus rècords

function obrirRecords() {
    ui.pintarRecords(llegirTotsElsRecords());
    ui.mostrarPantalla('records');
}

// ------------------------------------------------------------- Classificació

/**
 * La modalitat de la classificació NO du el dialecte, a diferència de
 * l'identificadorRecord dels rècords personals: la classificació és una de sola
 * per modalitat i el dialecte es diu a cada fila (vegeu subtitolEntrada a ui.js).
 */
function modalitatDe({ mode, dificultat, segons }) {
    return `${mode}|${dificultat}|${segons}`;
}

let modalitatActiva = null;
let diaActiu = null;
let dificultatDiaria = null;
let pestanyaActiva = 'modalitats';
let classificacio = null;

async function obrirClassificacio() {
    ui.mostrarPantalla('classificacio');
    ui.el.classificacioData.textContent = '';
    ui.el.classificacioSelector.replaceChildren();
    ui.estatClassificacio('Carregant la classificació…');

    try {
        classificacio = await carregarClassificacio();
    } catch (error) {
        ui.estatClassificacio('No s\'ha pogut carregar la classificació. Torna-ho a provar més tard.');
        return;
    }

    ui.el.classificacioData.textContent = classificacio.actualitzacio
        ? `Última actualització: ${classificacio.actualitzacio} (s'actualitza 1 cop al dia, de matinada)`
        : '';
    pintarPestanyaActiva();
}

function canviarPestanya(quina) {
    pestanyaActiva = quina;
    if (classificacio) pintarPestanyaActiva();
}

function pintarPestanyaActiva() {
    ui.marcarPestanya(pestanyaActiva);
    ui.subtitolClassificacio(
        'Les millors puntuacions de tota la gent que hi juga, jugui en el '
        + 'dialecte que jugui.');

    if (pestanyaActiva === 'diaria') pintarDiaria();
    else pintarModalitats();
}

/**
 * Les modalitats d'il·limitat, juguin en el dialecte que juguin. La paraula del
 * dia no hi surt: té la seva pestanya, i barrejar-hi partides d'un minut amb un
 * sol intent al dia no comparava res.
 */
function pintarModalitats() {
    ui.amagarSelectorDificultat();

    const modalitats = Object.entries(classificacio.modalitats || {})
        .filter(([clau]) => clau.startsWith('illimitat|'))
        // La pestanya ja diu "Il·limitat": repetir-ho a cada pastilla només
        // faria més estret el que de debò les distingeix.
        .map(([clau, valor]) => ({
            clau,
            titol: (valor.titol || '').replace(/^Il·limitat · /, ''),
            top: valor.top || [],
        }))
        .filter((m) => m.top.length > 0);

    if (modalitats.length === 0) {
        ui.el.classificacioSelector.replaceChildren();
        ui.estatClassificacio(estaConfigurat()
            ? 'Encara no hi ha cap partida il·limitada. Sigues el primer!'
            : 'La classificació encara no està activada en aquest lloc.');
        return;
    }

    // Si venim de jugar, ensenyem la modalitat que acabem de jugar si hi surt.
    if (!modalitats.some((m) => m.clau === modalitatActiva)) {
        const jugada = modalitatDe(estat);
        modalitatActiva = modalitats.some((m) => m.clau === jugada) ? jugada : modalitats[0].clau;
    }

    const perClau = new Map(modalitats.map((m) => [m.clau, m.top]));
    const elMeuSobrenom = llegirSobrenom();

    function mostrar(clau) {
        modalitatActiva = clau;
        ui.estatClassificacio('');
        ui.pintarSelectorModalitats(modalitats, clau, mostrar);
        ui.pintarClassificacio(perClau.get(clau) || [], elMeuSobrenom);
    }

    mostrar(modalitatActiva);
}

/**
 * La pestanya de la paraula del dia: el rànquing del dia que triïs i, a sota, el
 * dels millors de sempre. Els dos en la dificultat que triïs.
 */
function pintarDiaria() {
    const perDia = classificacio.diaria || {};
    const millors = classificacio.diaria_millors || {};
    const dies = Object.keys(perDia).sort().reverse();

    if (dies.length === 0) {
        ui.amagarSelectorDificultat();
        ui.el.classificacioSelector.replaceChildren();
        ui.estatClassificacio(estaConfigurat()
            ? 'Encara no hi ha cap paraula del dia jugada.'
            : 'La classificació encara no està activada en aquest lloc.');
        return;
    }

    if (!dies.includes(diaActiu)) diaActiu = dies[0];
    // Per defecte, la dificultat que jugues: és la que et deus voler mirar.
    if (dificultatDiaria === null) dificultatDiaria = estat.dificultat;
    const elMeuSobrenom = llegirSobrenom();

    function mostrar() {
        ui.estatClassificacio('');
        ui.pintarSelectorDificultat(dificultatDiaria, (dificultat) => {
            dificultatDiaria = dificultat;
            mostrar();
        });
        ui.pintarSelectorDies(dies, diaActiu, (dia) => {
            diaActiu = dia;
            mostrar();
        });
        ui.pintarDiaria({
            delDia: (perDia[diaActiu] || {})[dificultatDiaria],
            millors: millors[dificultatDiaria],
            dia: diaActiu,
            dificultat: dificultatDiaria,
        }, elMeuSobrenom);
    }

    mostrar();
}

// ------------------------------------------------------------ Configuració

function obrirConfig(mode) {
    estat.mode = mode;
    estat.data = avui();

    const esDiaria = mode === 'diaria';
    ui.el.configTitol.textContent = esDiaria ? 'Paraula del dia' : 'Il·limitat';
    ui.el.grupTemps.hidden = esDiaria;
    ui.el.configDialecte.textContent = `En ${ui.nomDialecte(estat.dialecte).toLowerCase()}`;
    estat.segons = esDiaria ? SEGONS_DIARIA : Number(opcionsTemps.valor());

    if (esDiaria) {
        // Un intent per dificultat, dialecte i dia: les jugades es bloquegen.
        for (const dificultat of ['facil', 'dificil']) {
            opcionsDificultat.activar(
                dificultat, !resultatDiari(estat.data, estat.dialecte, dificultat));
        }
        const lliure = ['facil', 'dificil']
            .find((d) => !resultatDiari(estat.data, estat.dialecte, d));
        if (lliure) opcionsDificultat.seleccionar(lliure);
    } else {
        opcionsDificultat.activar('facil', true);
        opcionsDificultat.activar('dificil', true);
    }

    estat.dificultat = opcionsDificultat.valor();
    refrescarConfig();
    ui.mostrarPantalla('config');
}

function refrescarConfig() {
    const esDiaria = estat.mode === 'diaria';
    const jugada = esDiaria
        ? resultatDiari(estat.data, estat.dialecte, estat.dificultat)
        : null;
    const totJugat = esDiaria && dificultatsJugades(estat.data, estat.dialecte).length === 2;

    ui.el.botoComencar.disabled = Boolean(jugada);
    ui.texteBoto(ui.el.botoComencar, jugada ? 'Torna-hi demà' : 'Comença');

    let avis = '';
    if (totJugat) {
        avis = 'Avui ja has jugat la paraula del dia en totes dues dificultats. Demà n\'hi haurà una de nova!';
    } else if (jugada) {
        avis = `Avui ja has jugat en ${NOM_DIFICULTAT[estat.dificultat]}: ${jugada.punts} ${jugada.punts === 1 ? 'rima' : 'rimes'}. Prova l'altra dificultat o torna demà.`;
    } else if (esDiaria) {
        avis = 'La mateixa paraula per a tothom qui juga en aquest dialecte, 1 minut i un sol intent.';
    }
    ui.el.configAvis.textContent = avis;
    ui.el.configAvis.hidden = avis === '';

    const record = llegirRecord(identificadorRecord(estat));
    ui.el.configRecord.textContent = record > 0
        ? `Rècord en aquesta modalitat: ${record}`
        : '';
}

// -------------------------------------------------------------------- Partida

// Quant esperem abans d'ensenyar el loader. Amb el fitxer del dialecte ja
// baixat, preparar una partida són 90 ms: ensenyar-lo de seguida seria una
// fuetada de pantalla que no informa de res. Si passa d'això, és que hi ha
// alguna cosa baixant i llavors sí que s'ha de veure.
const ESPERA_ABANS_DEL_LOADER = 150;

async function comencarPartida() {
    if (estat.mode === 'diaria'
        && resultatDiari(estat.data, estat.dialecte, estat.dificultat)) return;

    // Enganxar-se a la descàrrega que ja hi hagi en marxa. La precàrrega de
    // l'arrencada l'ha començada fa estona, o sigui que aquí normalment només
    // en recollim el final.
    let progres = { rebut: 0, total: 0 };
    let visible = false;
    const deixarEscoltar = escoltarProgres(estat.dialecte, (estatDescarrega) => {
        progres = estatDescarrega;
        if (visible) ui.progresCarregant(progres);
    });

    // El loader no s'ensenya de cop: es demana, i si la partida es prepara
    // abans no arriba a sortir.
    const temporitzador = setTimeout(() => {
        visible = true;
        ui.mostrarCarregant(true, 'Preparant la partida…');
        ui.progresCarregant(progres);
    }, ESPERA_ABANS_DEL_LOADER);

    try {
        const { objectiu, respostes } = await prepararParaula();

        ui.buidarPartida();
        ui.pintarObjectiu(objectiu.mostrar, estat.dificultat);
        ui.actualitzarPunts(0);
        ui.mostrarPantalla('joc');
        clearTimeout(temporitzador);
        ui.mostrarCarregant(false);

        estat.partida = new Partida({
            objectiu,
            respostes,
            segons: estat.segons,
            alTic: (restants) => ui.actualitzarRellotge(restants, estat.segons, formatarTemps(restants)),
            alFinal: acabarPartida,
        });
        estat.partida.comencar();
        ui.el.camp.focus();
    } catch (error) {
        console.error(error);
        clearTimeout(temporitzador);
        ui.mostrarCarregant(false);
        ui.el.configAvis.textContent = 'No s\'han pogut carregar les rimes. Comprova la connexió i torna-ho a provar.';
        ui.el.configAvis.hidden = false;
        ui.mostrarPantalla('config');
    } finally {
        deixarEscoltar();
    }
}

async function prepararParaula() {
    const index = indexDe(await carregarIndex(), estat.dialecte);
    const esDiaria = estat.mode === 'diaria';
    const seleccio = esDiaria
        ? clauDelDia(index, estat.data, estat.dialecte)
        : clauAleatoria(index);

    const grup = await grupDeRimes(estat.dialecte, seleccio.grup);
    const objectiu = triarParaula(grup, seleccio.clau, seleccio.aleatori);
    const respostes = respostesValides(grup, seleccio.clau, estat.dificultat);

    return { objectiu, respostes };
}

function enviarParaula(esdeveniment) {
    esdeveniment.preventDefault();
    const partida = estat.partida;
    if (!partida || partida.acabada) return;

    const { resultat, mostrar } = partida.provar(ui.el.camp.value);
    if (resultat === RESULTAT.BUIT) {
        ui.el.camp.value = '';
        return;
    }

    ui.el.camp.value = '';

    if (resultat === RESULTAT.ENCERT) {
        ui.actualitzarPunts(partida.punts);
        ui.afegirTrobada(mostrar);
        ui.animarEntrada('encert');
        ui.avisar('Molt bé!', 'encert');
        return;
    }

    ui.animarEntrada('error');
    if (resultat === RESULTAT.REPETIDA) {
        ui.avisar('Ja introduïda', 'neutre');
    } else if (resultat === RESULTAT.OBJECTIU) {
        ui.avisar('Aquesta és la paraula que has de rimar', 'neutre');
    } else {
        ui.avisar('No rima', 'error');
    }
}

function aturarPartida() {
    if (estat.partida) estat.partida.cancellar();
    estat.partida = null;
}

function acabarPartida(resum) {
    ui.bloquejarEntrada();
    estat.ultimResum = resum;

    const identificador = identificadorRecord(estat);
    const recordAnterior = llegirRecord(identificador);
    const recordNou = desarRecord(identificador, resum.punts);

    const esDiaria = estat.mode === 'diaria';
    if (esDiaria) {
        desarResultatDiari(estat.data, estat.dialecte, estat.dificultat, {
            punts: resum.punts,
            paraules: resum.paraules,
        });
    }

    ui.pintarFinal({
        ...resum,
        recordNou,
        record: recordAnterior,
        titolLlista: resum.punts === 1 ? 'La teva paraula' : 'Les teves paraules',
    });

    ui.el.botoCompartir.hidden = !esDiaria;
    ui.texteBoto(ui.el.botoCompartir, 'Comparteix el resultat');
    ui.el.botoRepetir.hidden = esDiaria;

    // Preparem el bloc d'enviament a la classificacio (per a totes les partides).
    modalitatActiva = modalitatDe(estat);
    diaActiu = esDiaria ? estat.data : diaActiu;
    ui.reiniciarEnviament();
    ui.el.campSobrenom.value = llegirSobrenom();
    if (resum.punts === 0) {
        ui.estatEnviament('Fes almenys una rima per pujar a la classificació.', null);
        ui.el.campSobrenom.disabled = true;
        ui.el.botoEnviarRecord.disabled = true;
    }

    // Petita pausa perque es vegi que el rellotge ha arribat a zero.
    setTimeout(() => ui.mostrarPantalla('final'), 500);
}

// -------------------------------------------------- Enviar a la classificació

async function enviarARanquing() {
    const resum = estat.ultimResum;
    if (!resum || resum.punts === 0) return;

    const comprovacio = validarSobrenom(ui.el.campSobrenom.value);
    if (!comprovacio.ok) {
        ui.estatEnviament(comprovacio.motiu, 'error');
        return;
    }

    desarSobrenom(comprovacio.sobrenom);
    ui.el.botoEnviarRecord.disabled = true;
    ui.estatEnviament('Enviant…', null);

    const resposta = await enviarPuntuacio({
        sobrenom: comprovacio.sobrenom,
        mode: estat.mode,
        dificultat: estat.dificultat,
        segons: estat.segons,
        dialecte: estat.dialecte,
        punts: resum.punts,
        paraula: resum.objectiu,
        data: estat.mode === 'diaria' ? estat.data : avui(),
    });

    if (resposta.estat === 'enviat') {
        ui.enviamentFet('Enviat! Sortiràs a la classificació quan s\'actualitzi.');
    } else if (resposta.estat === 'sense-backend') {
        ui.enviamentFet('Desat! (La classificació d\'aquest lloc encara no està activada.)');
    } else {
        ui.el.botoEnviarRecord.disabled = false;
        ui.estatEnviament('No s\'ha pogut enviar. Torna-ho a provar.', 'error');
    }
}

// ----------------------------------------------------------------- Compartir

async function compartir() {
    const text = textPerCompartir({
        data: estat.data,
        dificultat: estat.dificultat,
        dialecte: ui.nomDialecte(estat.dialecte),
        punts: estat.ultimResum ? estat.ultimResum.punts : 0,
    });

    const com = await compartirResultat(text);
    if (com === 'cancellat' || com === 'compartit') return;

    ui.texteBoto(ui.el.botoCompartir, com === 'copiat' ? 'Copiat!' : 'No s\'ha pogut copiar');
    setTimeout(() => {
        ui.texteBoto(ui.el.botoCompartir, 'Comparteix el resultat');
    }, 1600);
}
