// Backend de la classificació del joc: apunta al full cada puntuació que arriba.
//
// Enganxa'l a Extensions > Apps Script del full de càlcul i desplega'l com a
// aplicació web (accés: qualsevol). L'URL /exec va a URL_ENVIAMENT de
// joc/js/classificacio.js.
//
// ESCRIU PER NOM DE COLUMNA, no per posició. Abans feia un appendRow() amb els
// valors en un ordre fix, i això vol dir que el full i aquest fitxer s'han de
// posar d'acord sense que ni l'un ni l'altre ho puguin comprovar: el dia que al
// full li faltava una columna (la DataPartida, per exemple, que es va afegir
// després), tot el que venia darrere quedava desplaçat una casella i el
// compilador llegia les dades barrejades sense adonar-se'n. Ara es llegeix la
// fila 1, es fa quadrar cada valor amb el seu títol i, si en falta cap, S'AFEGEIX
// SOLA al final. O sigui que per estrenar la DataPartida n'hi ha prou de tornar
// a desplegar aquest script: no s'ha de tocar el full a mà.
//
// LES COLUMNES, en l'ordre en què es creen si el full és buit:
//
//   Data | DataPartida | Sobrenom | Mode | Dificultat | Segons | Dialecte |
//   Punts | Paraula | Usuari
//
// Hi ha DUES dates a posta:
//   Data         quan ha arribat l'enviament (la posa el servidor de Google)
//   DataPartida  de quin dia era la partida (la diu el navegador)
//
// No són la mateixa cosa: qui juga la paraula del dia a les 23.55 i l'envia a
// les 00.05 ha jugat la d'ahir. El rànquing per dia de
// compilar_classificacio.py agrupa per DataPartida, que és la que ho diu bé; la
// Data serveix per veure quan va passar de debò i per desempatar.
//
// El dia de la partida el compta el joc en horari de Catalunya (vegeu avui() a
// joc/js/magatzem.js) i aquí s'apunta l'arribada en el mateix fus: les dues
// dates parlen del mateix rellotge.

var FUS = 'Europe/Madrid';

// L'ordre en què es creen les columnes si el full encara no en té cap. Si ja en
// té, mana el que digui la fila 1 i aquí només se n'afegeixen les que faltin.
var CAPCALERES = ['Data', 'DataPartida', 'Sobrenom', 'Mode', 'Dificultat',
                  'Segons', 'Dialecte', 'Punts', 'Paraula', 'Usuari'];

function doPost(e) {
  try {
    var p = (e && e.parameter) ? e.parameter : {};

    var punts = parseInt(p.punts, 10);
    if (isNaN(punts) || punts < 0 || punts > 10000) {
      return resposta({ ok: false, motiu: 'dades invalides' });
    }

    // La data de la partida ha de ser AAAA-MM-DD i prou. Si ve res més (o no
    // ve), es deixa buida i el compilador ja hi posarà la d'arribada.
    var dataPartida = String(p.data || '');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(dataPartida)) {
      dataPartida = '';
    }

    var valors = {
      'Data': Utilities.formatDate(new Date(), FUS, 'dd/MM/yyyy HH:mm:ss'),
      'DataPartida': dataPartida,
      'Sobrenom': String(p.sobrenom || '').trim().replace(/\s+/g, ' '),
      'Mode': String(p.mode || ''),
      'Dificultat': String(p.dificultat || ''),
      'Segons': String(p.segons || ''),
      'Dialecte': String(p.dialecte || ''),
      'Punts': punts,
      'Paraula': String(p.paraula || ''),
      'Usuari': String(p.usuari || '')
    };

    var full = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    full.appendRow(filaPerAlFull(full, valors));

    return resposta({ ok: true });
  } catch (err) {
    return resposta({ ok: false, motiu: String(err) });
  }
}

/**
 * Posa cada valor sota el seu títol, i crea els títols que faltin.
 *
 * Torna la fila ja ordenada com la vulgui el full. Una columna que el full
 * tingui i que aquí no sapiguem omplir (una que hi hagi afegit algú a mà) es
 * deixa buida en comptes de desplaçar-ho tot.
 */
function filaPerAlFull(full, valors) {
  var columnes = full.getLastColumn();

  // Full acabat de fer: se li escriu la capçalera sencera.
  if (columnes === 0) {
    full.getRange(1, 1, 1, CAPCALERES.length).setValues([CAPCALERES]);
    full.setFrozenRows(1);
    return CAPCALERES.map(function (nom) {
      return valors.hasOwnProperty(nom) ? valors[nom] : '';
    });
  }

  var capcalera = full.getRange(1, 1, 1, columnes).getValues()[0]
    .map(function (casella) { return String(casella).trim(); });

  // Les que falten, al final. Al final i no a la posició "bona" a posta: moure
  // columnes voldria dir moure totes les files que ja hi ha, i el compilador
  // llegeix el CSV per nom de columna i no per posició (vegeu COLUMNES i
  // COLUMNES_NOVES a compilar_classificacio.py), o sigui que l'ordre li és ben
  // igual.
  var afegides = [];
  for (var i = 0; i < CAPCALERES.length; i++) {
    if (capcalera.indexOf(CAPCALERES[i]) === -1) afegides.push(CAPCALERES[i]);
  }
  if (afegides.length > 0) {
    full.getRange(1, capcalera.length + 1, 1, afegides.length)
        .setValues([afegides]);
    capcalera = capcalera.concat(afegides);
  }

  return capcalera.map(function (nom) {
    return valors.hasOwnProperty(nom) ? valors[nom] : '';
  });
}

function resposta(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
