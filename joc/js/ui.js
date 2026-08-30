// Tot el que toca el DOM. La resta de moduls no en saben res.

export const el = {};

const NOMS = [
    'pantalla-inici', 'pantalla-config', 'pantalla-joc', 'pantalla-final',
    'pantalla-records', 'pantalla-classificacio',
    'etiqueta-diaria', 'config-titol', 'config-avis', 'config-record', 'config-dialecte',
    'tira-dialectes',
    'opcions-dificultat', 'opcions-temps', 'grup-temps', 'boto-comencar',
    'rellotge', 'punts', 'barra-temps', 'objectiu', 'objectiu-etiqueta',
    'formulari', 'camp', 'toast', 'trobades',
    'resultat-punts', 'resultat-text', 'etiqueta-record', 'resum',
    'boto-compartir', 'boto-repetir', 'trobades-final', 'titol-llista',
    'bloc-classificacio', 'camp-sobrenom', 'boto-enviar-record', 'estat-enviament',
    'records-buit', 'llista-records',
    'classificacio-selector', 'classificacio-estat', 'classificacio-llista', 'classificacio-data',
    'classificacio-subtitol', 'classificacio-dificultat',
    'carregant', 'carregant-text', 'carregant-barra', 'carregant-progres', 'carregant-nota',
];

export function preparar() {
    for (const nom of NOMS) {
        el[aCamell(nom)] = document.getElementById(nom);
    }
}

function aCamell(text) {
    return text.replace(/-([a-z])/g, (_, lletra) => lletra.toUpperCase());
}

// ------------------------------------------------------------- Pantalles

const PANTALLES = ['inici', 'config', 'joc', 'final', 'records', 'classificacio'];

export function mostrarPantalla(nom) {
    for (const pantalla of PANTALLES) {
        el[aCamell(`pantalla-${pantalla}`)].hidden = pantalla !== nom;
    }
    window.scrollTo({ top: 0, behavior: 'instant' });
}

export function mostrarCarregant(visible, text) {
    if (text) el.carregantText.textContent = text;
    el.carregant.hidden = !visible;
    if (!visible) {
        el.carregantBarra.hidden = true;
        el.carregantNota.hidden = true;
        el.carregantProgres.style.width = '0%';
    }
}

/**
 * Com va la descàrrega de les rimes.
 *
 * Només surt quan hi ha alguna cosa a baixar: si el fitxer del dialecte ja és a
 * la memòria (perquè la precàrrega de l'arrencada ha tingut temps), la partida
 * s'obre en 90 ms i això no s'arriba a veure.
 */
export function progresCarregant({ rebut, total }) {
    if (!total || rebut >= total) {
        el.carregantText.textContent = 'Preparant la partida…';
        el.carregantBarra.hidden = true;
        el.carregantNota.hidden = true;
        return;
    }

    const percentatge = Math.max(0, Math.min(100, Math.round((rebut / total) * 100)));
    el.carregantText.textContent = `Baixant les rimes… ${percentatge} %`;
    el.carregantBarra.hidden = false;
    el.carregantNota.hidden = false;
    el.carregantProgres.style.width = `${percentatge}%`;
}

// Alguns botons (els de l'arc de Sant Martí) porten el text dins d'un <span>.
// Escriure directament a textContent l'esborraria, o sigui que si hi ha span,
// hi escrivim a dins.
export function texteBoto(boto, text) {
    const span = boto.querySelector('span');
    (span || boto).textContent = text;
}

// ---------------------------------------------------------------- Opcions

/**
 * Un grup de botons que fa de radiogroup. Torna una funcio per llegir el valor
 * escollit i una per canviar-lo.
 */
export function grupOpcions(contenidor, atribut, alCanviar) {
    const botons = [...contenidor.querySelectorAll('.opcio')];

    function seleccionar(valor) {
        for (const boto of botons) {
            boto.setAttribute('aria-checked', String(boto.dataset[atribut] === valor));
        }
        if (alCanviar) alCanviar(valor);
    }

    contenidor.addEventListener('click', (esdeveniment) => {
        const boto = esdeveniment.target.closest('.opcio');
        if (boto && !boto.disabled) seleccionar(boto.dataset[atribut]);
    });

    return {
        valor: () => {
            const triat = botons.find((boto) => boto.getAttribute('aria-checked') === 'true');
            return triat ? triat.dataset[atribut] : botons[0].dataset[atribut];
        },
        seleccionar,
        activar: (valor, actiu) => {
            const boto = botons.find((b) => b.dataset[atribut] === valor);
            if (boto) boto.disabled = !actiu;
        },
    };
}

// ------------------------------------------------------ Tira de dialectes

/**
 * La tira per triar el dialecte, com la del cercador (vegeu el DIALECTES de
 * js/components.js). La llista ve de dades/versions.json i ja arriba ordenada:
 * aqui nomes es pinta tal com ve, sense saber quins dialectes hi ha ni com es
 * diuen.
 */
export function pintarTiraDialectes(dialectes, actiu, alTriar) {
    el.tiraDialectes.replaceChildren(
        ...dialectes.map(({ codi, nom }) => {
            const boto = document.createElement('button');
            boto.type = 'button';
            boto.className = 'dialecte';
            boto.dataset.dialecte = codi;
            boto.setAttribute('role', 'radio');
            boto.setAttribute('aria-checked', String(codi === actiu));
            boto.textContent = nom;
            boto.addEventListener('click', () => alTriar(codi));
            return boto;
        })
    );
}

export function marcarDialecte(codi) {
    for (const boto of el.tiraDialectes.querySelectorAll('.dialecte')) {
        boto.setAttribute('aria-checked', String(boto.dataset.dialecte === codi));
    }
}

// ----------------------------------------------------------------- Partida

export function pintarObjectiu(paraula, dificultat) {
    el.objectiu.textContent = paraula;
    el.objectiuEtiqueta.textContent = dificultat === 'dificil'
        ? 'Rimes consonants amb'
        : 'Rimes assonants amb';
}

export function actualitzarPunts(punts) {
    el.punts.textContent = String(punts);
}

export function actualitzarRellotge(segonsRestants, segonsTotals, textFormatat) {
    el.rellotge.textContent = textFormatat;
    const percentatge = Math.max(0, Math.min(100, (segonsRestants / segonsTotals) * 100));
    el.barraTemps.style.width = `${percentatge}%`;

    const alerta = segonsRestants <= 10;
    el.rellotge.classList.toggle('marcador__valor--alerta', alerta);
    el.barraTemps.classList.toggle('barra-temps__interior--alerta', alerta);
}

let temporitzadorToast = null;

export function avisar(text, tipus) {
    el.toast.textContent = text;
    el.toast.className = `toast toast--visible toast--${tipus}`;
    clearTimeout(temporitzadorToast);
    temporitzadorToast = setTimeout(() => {
        el.toast.className = 'toast';
    }, 1200);
}

let temporitzadorAnimacio = null;

export function animarEntrada(tipus) {
    const forma = el.formulari;
    forma.classList.remove('entrada--encert', 'entrada--error');
    // Forcem un reflow perque l'animacio es torni a disparar si es repeteix.
    void forma.offsetWidth;
    forma.classList.add(`entrada--${tipus}`);
    clearTimeout(temporitzadorAnimacio);
    temporitzadorAnimacio = setTimeout(() => {
        forma.classList.remove('entrada--encert', 'entrada--error');
    }, 400);
}

export function afegirTrobada(paraula) {
    const item = document.createElement('li');
    item.textContent = paraula;
    el.trobades.prepend(item);
}

export function buidarPartida() {
    el.trobades.replaceChildren();
    el.toast.className = 'toast';
    el.toast.textContent = '';
    el.camp.value = '';
    el.camp.disabled = false;
    el.formulari.querySelector('button').disabled = false;
}

export function bloquejarEntrada() {
    el.camp.disabled = true;
    el.formulari.querySelector('button').disabled = true;
    el.camp.blur();
}

// ------------------------------------------------------------------- Final

export function pintarFinal({ punts, paraules, objectiu, rimesPossibles, recordNou, record, titolLlista }) {
    el.resultatPunts.textContent = String(punts);
    el.resultatText.textContent = punts === 1 ? 'rima trobada' : 'rimes trobades';
    el.etiquetaRecord.hidden = !recordNou;

    const trobables = `«${objectiu}» tenia ${rimesPossibles.toLocaleString('ca-ES')} rimes possibles.`;
    el.resum.textContent = recordNou || !record
        ? trobables
        : `${trobables} El teu rècord en aquesta modalitat és ${record}.`;

    el.titolLlista.textContent = titolLlista;
    el.titolLlista.hidden = paraules.length === 0;
    el.trobadesFinal.replaceChildren(
        ...paraules.map((paraula) => {
            const item = document.createElement('li');
            item.textContent = paraula;
            return item;
        })
    );
}

// -------------------------------------------------- Noms de les modalitats

const NOM_MODE = { illimitat: 'Il·limitat', diaria: 'Paraula del dia' };
const NOM_DIFICULTAT = { facil: 'Fàcil', dificil: 'Difícil' };
const NOM_TEMPS = { 45: 'Llampec', 60: '1 minut', 90: 'Estàndard', 180: 'Lent' };

// Els noms dels dialectes els diu el versions.json (els escriu el generador a
// partir del NOMS_DE_DIALECTE de generar_dades.py). Aqui nomes se'n guarda una
// copia per poder titular els records sense haver d'anar a buscar-la cada cop.
let nomsDeDialecte = {};

export function recordarNomsDeDialecte(dialectes) {
    nomsDeDialecte = Object.fromEntries(dialectes.map((d) => [d.codi, d.nom]));
}

export function nomDialecte(codi) {
    return nomsDeDialecte[codi] || codi;
}

export function titolModalitat({ mode, dificultat, segons, dialecte }) {
    const parts = [NOM_MODE[mode] || mode, NOM_DIFICULTAT[dificultat] || dificultat];
    if (mode !== 'diaria') parts.push(NOM_TEMPS[segons] || `${segons}s`);
    if (dialecte) parts.push(nomDialecte(dialecte));
    return parts.join(' · ');
}

function filaRecord({ posicio, etiqueta, subtitol, punts, destacada }) {
    const fila = document.createElement('div');
    fila.className = 'fila-record';
    if (posicio && posicio <= 3) fila.classList.add(`fila-record--${posicio}`);
    if (destacada) fila.classList.add('fila-record--jo');

    const nom = document.createElement('div');
    nom.className = 'fila-record__nom';
    if (posicio) {
        const pos = document.createElement('span');
        pos.className = 'fila-record__pos';
        pos.textContent = posicio;
        nom.appendChild(pos);
    }
    const text = document.createElement('div');
    text.className = 'fila-record__etiqueta';
    text.textContent = etiqueta;
    if (subtitol) {
        const sub = document.createElement('span');
        sub.className = 'fila-record__sub';
        sub.textContent = subtitol;
        text.appendChild(sub);
    }
    nom.appendChild(text);

    const valor = document.createElement('span');
    valor.className = 'fila-record__punts';
    valor.textContent = punts;

    fila.append(nom, valor);
    return fila;
}

// ------------------------------------------------------- Els meus rècords

// L'ordre de les bombolles dels records: el mateix que trobes jugant, primer la
// paraula del dia i despres l'il·limitat, i dins de cada mode el fàcil abans que
// el difícil i el rellotge de mes rapid a mes lent.
const ORDRE_MODE = ['diaria', 'illimitat'];
const ORDRE_DIFICULTAT = ['facil', 'dificil'];

function posicio(llista, valor) {
    const on = llista.indexOf(valor);
    return on < 0 ? llista.length : on;
}

/**
 * Els teus rècords: una bombolla per modalitat.
 *
 * Abans eren una sola llista ordenada de mes punts a menys, i aixo no comparava
 * res: en tres minuts en fas mes que en quaranta-cinc segons sempre, o sigui que
 * el "Lent" es quedava dalt de tot i el "Llampec" al fons, diguessin el que
 * diguessin. El teu millor llampec no es pitjor que el teu millor lent; son
 * partides diferents. Partides per modalitat, cada numero nomes es compara amb
 * els que li toca.
 *
 * Dins de cada bombolla hi ha una fila per dialecte, perque els records es
 * guarden per dialecte (paraules diferents i grups de rima diferents), amb quina
 * paraula el vas fer. Si sempre jugues igual, es una fila i prou.
 */
export function pintarRecords(records) {
    el.recordsBuit.hidden = records.length > 0;
    el.llistaRecords.hidden = records.length === 0;

    const grups = new Map();
    for (const r of records) {
        const clau = `${r.mode}|${r.dificultat}|${r.segons}`;
        if (!grups.has(clau)) grups.set(clau, []);
        grups.get(clau).push(r);
    }

    const ordenats = [...grups.values()].sort((a, b) => {
        const [x, y] = [a[0], b[0]];
        return posicio(ORDRE_MODE, x.mode) - posicio(ORDRE_MODE, y.mode)
            || posicio(ORDRE_DIFICULTAT, x.dificultat) - posicio(ORDRE_DIFICULTAT, y.dificultat)
            || x.segons - y.segons;
    });

    el.llistaRecords.replaceChildren(...ordenats.map(bombollaRecord));
}

function bombollaRecord(entrades) {
    const { mode, dificultat, segons } = entrades[0];

    // El dialecte no va al titol: la bombolla es de la modalitat i el dialecte
    // es el que distingeix les files de dins.
    const titol = [titolModalitat({ mode, dificultat, segons })];
    if (mode !== 'diaria') titol.push(marcaTemps(segons));

    return bombolla(titol, entrades.map((r) => filaRecord({
        etiqueta: nomDialecte(r.dialecte),
        subtitol: r.paraula ? `amb «${r.paraula}»` : '',
        punts: r.punts,
    })));
}

// ------------------------------------------------------------ Classificació

/**
 * Els segons de la modalitat, en una pastilleta de color.
 *
 * El nom del rellotge («Llampec», «Estàndard», «Lent») no diu quant dura, i tres
 * taules que només es distingeixen per aquesta paraula s'acaben confonent: el
 * número ho diu, i el color deixa veure d'un cop d'ull en quina de les tres ets.
 * El color és de més a més i mai l'única pista: qui no el vegi té igualment el
 * nom i els segons escrits.
 */
function marcaTemps(segons) {
    const marca = document.createElement('span');
    marca.className = `marca-temps marca-temps--${segons}`;
    marca.textContent = `${segons}s`;
    return marca;
}

/**
 * Una bombolla: la capçalera que diu què s'hi mira i les files de sota. La fan
 * servir les dues pantalles de llistes —la classificació i els rècords—, i cada
 * llista va a la seva amb rosa entremig, perquè es vegi de seguida que són
 * coses diferents i no pas una llista llarga.
 *
 * El títol pot ser un text o una llista de trossos, que és com s'hi encasta la
 * marca de temps de la modalitat.
 */
function bombolla(titol, files, buit) {
    const caixa = document.createElement('section');
    caixa.className = 'bombolla';

    const capcalera = document.createElement('h3');
    capcalera.className = 'bombolla__titol';
    capcalera.append(...(Array.isArray(titol) ? titol : [titol]));
    caixa.appendChild(capcalera);

    if (files.length === 0) {
        const avis = document.createElement('p');
        avis.className = 'taula-buida';
        avis.textContent = buit || 'Encara no hi ha ningú.';
        caixa.appendChild(avis);
        return caixa;
    }

    caixa.append(...files);
    return caixa;
}

/** Les files d'un rànquing: la posició, el sobrenom i amb què ho va fer. */
function filesRanquing(entrades, elMeuSobrenom) {
    return (entrades || []).map((e, i) => filaRecord({
        posicio: i + 1,
        etiqueta: e.sobrenom,
        subtitol: subtitolEntrada(e),
        punts: e.punts,
        destacada: elMeuSobrenom && e.sobrenom.toLowerCase() === elMeuSobrenom.toLowerCase(),
    }));
}

/**
 * Les pastilles d'il·limitat: una fila per dificultat, separades per una ratlla.
 *
 * Totes sis seguides no es llegien: «Difícil · Llampec» i «Fàcil · Llampec»
 * s'assemblen massa per distingir-les de cua d'ull, i per ordre de clau sortien
 * barrejades i amb els rellotges desordenats (180, 45, 90). Partides per
 * dificultat i de la més ràpida a la més lenta, la graella queda com la de la
 * pantalla de configuració.
 */
export function pintarSelectorModalitats(grups, actiu, alTriar) {
    el.classificacioSelector.className = 'selector-modalitat selector-modalitat--grups';
    el.classificacioSelector.replaceChildren(
        ...grups.map((grup) => {
            const fila = document.createElement('div');
            fila.className = 'selector-fila';
            fila.append(...grup.modalitats.map(({ clau, titol, segons }) => {
                const boto = document.createElement('button');
                boto.type = 'button';
                boto.className = 'pastilla';
                boto.append(titol, marcaTemps(segons));
                boto.setAttribute('aria-pressed', String(clau === actiu));
                boto.addEventListener('click', () => alTriar(clau));
                return boto;
            }));
            return fila;
        })
    );
}

/**
 * El subtítol d'una entrada de la classificació: amb quina paraula ho va fer i,
 * entre parèntesis, en quin dialecte.
 *
 * El dialecte va aquí i no pas al títol de la taula a posta: la classificació és
 * una de sola per modalitat, i partir-la en quatre voldria dir quatre taules de
 * quatre persones. Dit a cada fila, tothom surt junt i es veu en què jugava.
 */
function subtitolEntrada(e) {
    const trossos = [];
    if (e.paraula) trossos.push(`amb «${e.paraula}»`);
    if (e.dialecte) trossos.push(`(${nomDialecte(e.dialecte)})`);
    return trossos.join(' ');
}

/**
 * La taula d'una modalitat d'il·limitat. La capçalera repeteix la pastilla que
 * has triat: quan has baixat a mirar la llista, el selector ja no es veu.
 */
export function pintarClassificacio({ titol, segons, top }, elMeuSobrenom) {
    el.classificacioLlista.replaceChildren(
        bombolla([titol, marcaTemps(segons)], filesRanquing(top, elMeuSobrenom))
    );
}

export function estatClassificacio(text) {
    el.classificacioEstat.textContent = text || '';
    el.classificacioEstat.hidden = !text;
    if (text) el.classificacioLlista.replaceChildren();
}

export function subtitolClassificacio(text) {
    el.classificacioSubtitol.textContent = text;
}

/** Quina pestanya de la classificació es veu: 'modalitats' o 'diaria'. */
export function marcarPestanya(quina) {
    for (const boto of document.querySelectorAll('.pestanya')) {
        boto.setAttribute('aria-selected', String(boto.dataset.taula === quina));
    }
}

// -------------------------------------------------- Classificació del dia

const MESOS = ['gen.', 'febr.', 'març', 'abr.', 'maig', 'juny',
               'jul.', 'ag.', 'set.', 'oct.', 'nov.', 'des.'];

/** "2026-08-26" -> "26 d'ag." — prou curt per cabre en una pastilla. */
export function diaCurt(dia) {
    const [, mes, numero] = dia.split('-');
    const nom = MESOS[Number(mes) - 1] || mes;
    const de = 'aeiou'.includes(nom[0]) ? "d'" : 'de ';
    return `${Number(numero)} ${de}${nom}`;
}

/**
 * La tria de dificultat de la pestanya de la paraula del dia. Val tant per al
 * rànquing del dia com per al dels millors de sempre: són la mateixa pregunta
 * feta dues vegades i no tindria sentit poder-les descordar.
 */
export function pintarSelectorDificultat(actiu, alTriar) {
    el.classificacioDificultat.hidden = false;
    el.classificacioDificultat.replaceChildren(
        ...['facil', 'dificil'].map((dificultat) => {
            const boto = document.createElement('button');
            boto.type = 'button';
            boto.className = 'pastilla';
            boto.textContent = NOM_DIFICULTAT[dificultat];
            boto.setAttribute('role', 'radio');
            boto.setAttribute('aria-checked', String(dificultat === actiu));
            boto.setAttribute('aria-pressed', String(dificultat === actiu));
            boto.addEventListener('click', () => alTriar(dificultat));
            return boto;
        })
    );
}

export function amagarSelectorDificultat() {
    el.classificacioDificultat.hidden = true;
    el.classificacioDificultat.replaceChildren();
}

export function pintarSelectorDies(dies, actiu, alTriar) {
    // El mateix calaix que les pastilles d'il·limitat, que hi van per files:
    // aqui van totes seguides i cal treure-li la classe.
    el.classificacioSelector.className = 'selector-modalitat';
    el.classificacioSelector.replaceChildren(
        ...dies.map((dia) => {
            const boto = document.createElement('button');
            boto.type = 'button';
            boto.className = 'pastilla';
            boto.textContent = diaCurt(dia);
            boto.setAttribute('aria-pressed', String(dia === actiu));
            boto.addEventListener('click', () => alTriar(dia));
            return boto;
        })
    );
}

/**
 * La pestanya de la paraula del dia: el rànquing del dia que estiguis mirant i,
 * a sota, el dels millors de sempre. Tots dos en la dificultat triada, i cadascun
 * a la seva bombolla: enganxats semblaven una sola llista de vint noms.
 *
 * Vénen dels blocs "diaria" i "diaria_millors" de dades/classificacio.json, que
 * munta joc/eines/compilar_classificacio.py.
 *
 * No hi ha cap capçalera que digui quina era la paraula del dia, perquè no n'hi
 * ha una de sola: cada dialecte té la seva (vegeu clauDelDia a objectius.js).
 * Va a cada fila, al costat del dialecte.
 */
export function pintarDiaria({ delDia, millors, dia, dificultat }, elMeuSobrenom) {
    el.classificacioLlista.replaceChildren(
        bombolla(`Rànquing del ${diaCurt(dia)} · ${NOM_DIFICULTAT[dificultat]}`,
                 filesRanquing(delDia, elMeuSobrenom)),
        bombolla(`Els millors de sempre · ${NOM_DIFICULTAT[dificultat]}`,
                 filesRanquing(millors, elMeuSobrenom)),
    );
}

// ------------------------------------------------ Enviament a la classificació

export function reiniciarEnviament() {
    el.blocClassificacio.hidden = false;
    el.campSobrenom.disabled = false;
    el.botoEnviarRecord.disabled = false;
    el.estatEnviament.textContent = '';
    el.estatEnviament.className = 'estat-enviament';
}

export function estatEnviament(text, tipus) {
    el.estatEnviament.textContent = text;
    el.estatEnviament.className = `estat-enviament${tipus ? ' estat-enviament--' + tipus : ''}`;
}

export function enviamentFet(missatge) {
    el.campSobrenom.disabled = true;
    el.botoEnviarRecord.disabled = true;
    estatEnviament(missatge, 'ok');
}
