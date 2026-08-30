// Backend de la classificació del joc: apunta al full cada puntuació que arriba.
//
// Enganxa'l a Extensions > Apps Script del full de càlcul i desplega'l com a
// aplicació web (accés: qualsevol). L'URL /exec va a URL_ENVIAMENT de
// joc/js/classificacio.js.
//
// LES COLUMNES DEL FULL, a la fila 1 i en aquest ordre:
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
// Si el full ve d'abans i no té les columnes DataPartida ni Dialecte, afegeix-les
// a la fila 1 en aquestes posicions: el compilador dona per fetes les files
// velles que no les duguin (partida del dia que es va enviar, dialecte central).

function doPost(e) {
  try {
    var p = (e && e.parameter) ? e.parameter : {};

    var sobrenom = String(p.sobrenom || '').trim().replace(/\s+/g, ' ');
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

    var full = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    full.appendRow([
      Utilities.formatDate(new Date(), 'Europe/Madrid', 'dd/MM/yyyy HH:mm:ss'),
      dataPartida,
      sobrenom,
      String(p.mode || ''),
      String(p.dificultat || ''),
      String(p.segons || ''),
      String(p.dialecte || ''),
      punts,
      String(p.paraula || ''),
      String(p.usuari || '')
    ]);

    return resposta({ ok: true });
  } catch (err) {
    return resposta({ ok: false, motiu: String(err) });
  }
}

function resposta(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
