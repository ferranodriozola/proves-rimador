function doPost(e) {
  try {
    var p = (e && e.parameter) ? e.parameter : {};

    var sobrenom = String(p.sobrenom || '').trim().replace(/\s+/g, ' ');
    var punts = parseInt(p.punts, 10);

    if (isNaN(punts) || punts < 0 || punts > 10000) {
      return resposta({ ok: false, motiu: 'dades invalides' });
    }

    var full = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    full.appendRow([
      Utilities.formatDate(new Date(), 'Europe/Madrid', 'dd/MM/yyyy HH:mm:ss'),
      sobrenom,
      String(p.mode || ''),
      String(p.dificultat || ''),
      String(p.segons || ''),
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

