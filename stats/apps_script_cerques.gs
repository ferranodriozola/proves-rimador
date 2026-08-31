// Backend de les estadístiques: apunta al full cada cerca que arriba del web.
//
// Enganxa'l a Extensions > Apps Script del full de càlcul de les cerques i
// desplega'l com a aplicació web (accés: qualsevol). L'URL /exec va a
// URL_GOOGLE_SCRIPT de js/script.js, que és qui l'envia (vegeu registrarCerca).
//
// Després, stats/stats.py llegeix aquell full publicat en CSV cada nit i
// n'escriu stats/estadistiques_rimador.json, que és el que veu dades.html.
//
// LES COLUMNES DEL FULL, a la fila 1 i en aquest ordre:
//
//   Data | Usuari | Paraula | Codi | Rima | Tipus de rima | Num. síl· |
//   Comença per | Incloure NP | Incloure pl. | Dialecte
//
// Els noms han de ser EXACTAMENT aquests: l'stats.py hi busca les columnes pel
// nom, accents i punt de "Incloure pl." inclosos.
//
// SI EL FULL VE D'ABANS I NO TÉ LA COLUMNA "Dialecte", afegeix-la a la fila 1
// A L'ÚLTIMA POSICIÓ (K1), mai entremig: inserida al mig, totes les files
// velles queden desplaçades una columna i el full anterior es fa malbé. Les
// files d'abans del canvi la duran buida, i l'stats.py ja ho té previst: les
// deixa fora dels recomptes de dialecte en comptes de descartar-les.
//
// I RECORDA DESPLEGAR: l'aplicació web serveix la versió DESPLEGADA, no pas la
// que tens desada a l'editor. Desar el codi no canvia res del que rep el full;
// cal Desplega > Gestiona els desplegaments > editar el desplegament > versió
// nova. És l'errada d'una tarda sencera, aquesta.

function doPost(e) {
  try {
    // getSheets()[0] i no getActiveSheet(): en una crida web no hi ha ningú
    // mirant cap pestanya, i "l'activa" acaba depenent de coses que no manem.
    // El full de les cerques és el primer i prou. Mateix criteri que
    // joc/eines/apps_script_classificacio.gs.
    var full = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];

    var p = (e && e.parameter) ? e.parameter : {};

    var paraula = String(p.paraula || '').trim();

    // Sense paraula no hi ha cerca que apuntar. El web ja no n'envia cap de
    // buida ni de menys de dues lletres (vegeu registrarCerca), però l'adreça
    // /exec és oberta a qui la sàpiga i val més no escriure al full el que
    // arribi de qualsevol banda.
    if (!paraula) {
      return resposta('Sense paraula');
    }

    full.appendRow([
      // La data com a TEXT amb un format fixat, i no pas un new Date().
      //
      // Amb un objecte Date, el que surt al CSV publicat és com el full
      // decideixi ENSENYAR la data, i l'stats.py el llegeix amb un format
      // clavat ('%d/%m/%Y %H:%M:%S'). Si algú toca el format de la columna A,
      // el pd.to_datetime no reconeix res, l'errors='coerce' ho torna tot buit
      // i el dropna se salta totes les files: unes estadístiques a zero sense
      // que peti res enlloc. Escrivint-la nosaltres, el que llegeix l'stats.py
      // no depèn de com es vegi el full.
      //
      // La zona horària també la diem aquí: el servidor de Google no corre a
      // Barcelona, i les dades es tallen per dies (vegeu tz_espanya a
      // stats/stats.py).
      Utilities.formatDate(new Date(), 'Europe/Madrid', 'dd/MM/yyyy HH:mm:ss'),
      String(p.usuari || 'Anònim'),
      paraula,
      String(p.codi || ''),
      String(p.rima || ''),
      String(p.tipusRima || ''),
      String(p.numeroSilabes || ''),
      String(p.comencaPer || ''),
      String(p.inclourePropis || ''),
      String(p.inclourePlurals || ''),
      // El dialecte en què s'ha cercat: 'ca', 'nw', 'va' o 'ba'.
      //
      // Aquí NO es comprova que sigui un dels quatre, a posta. Qui sap quins hi
      // ha és la llista DIALECTES de js/components.js, i el dia que s'hi
      // afegeixi el rossellonès ningú no se'n recordaria, d'aquest fitxer: una
      // llista escrita aquí voldria dir tirar a les escombraries, sense dir-ho,
      // les cerques del dialecte nou. Els codis estranys ja els deixa fora
      // l'stats.py, que sí que té la llista al costat de tota la resta.
      String(p.dialecte || '')
    ]);

    return resposta('OK');

  } catch (error) {
    // El motiu, escrit: el web fa el fetch amb mode 'no-cors' i no llegeix mai
    // la resposta, però quan es prova l'adreça a mà des del navegador, un
    // "Error" pelat no diu on mirar.
    return resposta('Error: ' + error);
  }
}


function resposta(text) {
  return ContentService.createTextOutput(text);
}
