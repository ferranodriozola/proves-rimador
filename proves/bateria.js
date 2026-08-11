// BATERIA DE PROVES DE LA CERCA
//
// Serveix per canviar les tripes de buscarParaula sense trencar-la. La idea és
// senzilla: abans de tocar res es desa una instantània del que dona la cerca
// ara mateix, i després de cada canvi es torna a passar i es compara. Si surt
// una sola diferència, el canvi és dolent.
//
// Es crida buscarParaula directament i no pas realitzarCerca, perquè la segona
// depèn dels desplegables de la pàgina i del que hi hagi pintat; la primera
// agafa els paràmetres i retorna el resultat, que és el que volem comparar.
//
// Dues coses es fixen abans de començar perquè el resultat no depengui de
// l'ordre en què s'executen els casos:
//
//   - El diàleg d'homògrafs se substitueix per una tria automàtica. Si no,
//     la bateria s'aturaria esperant que algú cliqui.
//   - Es carreguen les transcripcions (col_9) d'entrada. Com que es baixen
//     només quan cal, el primer cas amb homògrafs les carregaria i tots els
//     casos següents donarien una llistaParaulaCerca diferent de si haguessin
//     anat primers.

const CASOS = [
  // --- cerques corrents ---
  { nom: "peixet, consonant",            paraula: "peixet",  rima: "r.consonant" },
  { nom: "peixet, assonant",             paraula: "peixet",  rima: "r.assonant" },
  { nom: "casa, consonant",              paraula: "casa",    rima: "r.consonant" },
  { nom: "casa, assonant",               paraula: "casa",    rima: "r.assonant" },

  // --- la paraula no hi és ---
  { nom: "paraula inexistent",           paraula: "xyzzyxq", rima: "r.consonant" },
  { nom: "cadena buida",                 paraula: "",        rima: "r.consonant" },

  // --- homògrafs: cal que cada opció doni rimes diferents ---
  { nom: "be, homògraf opció 1",         paraula: "be",         rima: "r.consonant", homograf: 1 },
  { nom: "be, homògraf opció 2",         paraula: "be",         rima: "r.consonant", homograf: 2 },
  { nom: "alar, homògraf opció 1",       paraula: "alar",       rima: "r.consonant", homograf: 1 },
  { nom: "alar, homògraf opció 2",       paraula: "alar",       rima: "r.consonant", homograf: 2 },
  { nom: "basar, homògraf opció 2",      paraula: "basar",      rima: "r.assonant",  homograf: 2 },
  { nom: "articular, homògraf opció 1",  paraula: "articular",  rima: "r.consonant", homograf: 1 },
  { nom: "be, homògraf cancel·lat",      paraula: "be",         rima: "r.consonant", homograf: null },

  // --- nàufragues: no rimen amb res tret d'elles mateixes ---
  { nom: "abeuren, nàufraga",            paraula: "abeuren", rima: "r.consonant" },
  { nom: "abordi, nàufraga",             paraula: "abordi",  rima: "r.consonant" },

  // --- codis curts: aquí el 4t i el 5è caràcter del codi no existeixen, i el
  //     filtre de plurals els ha de deixar passar igualment ---
  { nom: "adeu, codi de 2 lletres (ZI)",   paraula: "adeu",  rima: "r.consonant", plurals: "no" },
  { nom: "abans, codi de 3 lletres (ZRG)", paraula: "abans", rima: "r.consonant", plurals: "no" },
  { nom: "adeu-siau, amb guionet",         paraula: "adeu-siau", rima: "r.consonant" },

  // --- extrems de síl·labes ---
  { nom: "a, una síl·laba",              paraula: "a", rima: "r.consonant" },
  { nom: "esofagogastro..., 13 síl·labes", paraula: "esofagogastroduodenoscòpia", rima: "r.consonant" },

  // --- primera lletra: vocal, hac i accent ---
  { nom: "ha, comença per hac",          paraula: "ha",   rima: "r.consonant", comenca: "vocal+h" },
  { nom: "ha, comença per consonant",    paraula: "ha",   rima: "r.consonant", comenca: "consonant" },
  { nom: "àbac, comença per accent",     paraula: "àbac", rima: "r.consonant", comenca: "vocal+h" },

  // --- rimes molt grosses ---
  { nom: "Aalen, assonant amb propis",   paraula: "Aalen", rima: "r.assonant", propis: "si" },
  { nom: "Aalen, assonant sense propis", paraula: "Aalen", rima: "r.assonant", propis: "no" },
];

// El filtre de síl·labes i els altres desplegables, provats un per un sobre
// una paraula amb prou rimes perquè el filtre es noti.
for (const s of ["0", "1", "2", "3", "4", "5", "6"]) {
  CASOS.push({ nom: `casa, síl·labes = ${s}`, paraula: "casa", rima: "r.assonant", silabes: s });
}
for (const c of ["indiferent", "vocal+h", "consonant"]) {
  CASOS.push({ nom: `casa, comença per ${c}`, paraula: "casa", rima: "r.assonant", comenca: c });
}
for (const p of ["si", "no"]) {
  CASOS.push({ nom: `casa, propis = ${p}`,  paraula: "casa", rima: "r.assonant", propis: p });
  CASOS.push({ nom: `casa, plurals = ${p}`, paraula: "casa", rima: "r.assonant", plurals: p });
}

async function resum(text) {
  const dades = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(dades)].map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 16);
}

async function executarBateria(informar = () => {}) {
  // Les transcripcions, d'entrada (vegeu el comentari de dalt).
  await assegurarArray9();

  const originalTriar = triarHomograf;
  let triaDelCas = 1;
  triarHomograf = (paraula, opcions) =>
    Promise.resolve(triaDelCas === null ? null : (opcions[triaDelCas - 1] || opcions[0]));

  const resultats = [];
  try {
    for (let n = 0; n < CASOS.length; n++) {
      const cas = CASOS[n];
      triaDelCas = "homograf" in cas ? cas.homograf : 1;

      const params = {
        paraula: cas.paraula,
        silabes: cas.silabes ?? "0",
        comenca: cas.comenca ?? "indiferent",
        rima: cas.rima,
        propis: cas.propis ?? "no",
        plurals: cas.plurals ?? "si",
      };

      const sortida = await buscarParaula(
        params.paraula, params.silabes, params.comenca, params.rima,
        params.propis, params.plurals,
        array0, col1, col2, col3, col4, col5, col6, col7, col8
      );

      if (sortida === null) {
        resultats.push({ nom: cas.nom, params, cancellat: true });
      } else {
        const [trobades, paraulaCerca] = sortida;
        const serialitzat = JSON.stringify(trobades);
        resultats.push({
          nom: cas.nom,
          params,
          trobades: trobades.length,
          resum: await resum(serialitzat),
          paraulaCerca,
          // Les primeres i les últimes: si un resum no quadra, aquestes
          // ensenyen de seguida per on va la diferència.
          primeres: trobades.slice(0, 3),
          ultimes: trobades.slice(-3),
        });
      }
      informar(n + 1, CASOS.length, cas.nom);
    }
  } finally {
    triarHomograf = originalTriar;
  }

  return { generat: new Date().toISOString(), files: array0.length, casos: resultats };
}

// Compara dues instantànies i retorna només el que no quadra.
function comparar(abans, ara) {
  const diferencies = [];
  const perNom = new Map(abans.casos.map(c => [c.nom, c]));

  for (const nou of ara.casos) {
    const vell = perNom.get(nou.nom);
    if (!vell) { diferencies.push({ nom: nou.nom, què: "cas nou, no era a la instantània" }); continue; }
    perNom.delete(nou.nom);

    if (!!vell.cancellat !== !!nou.cancellat) {
      diferencies.push({ nom: nou.nom, què: "cancel·lació", abans: !!vell.cancellat, ara: !!nou.cancellat });
    } else if (!nou.cancellat) {
      if (vell.trobades !== nou.trobades) {
        diferencies.push({ nom: nou.nom, què: "nombre de rimes", abans: vell.trobades, ara: nou.trobades });
      } else if (vell.resum !== nou.resum) {
        diferencies.push({ nom: nou.nom, què: "el contingut de les rimes", abans: vell.primeres, ara: nou.primeres });
      }
      if (JSON.stringify(vell.paraulaCerca) !== JSON.stringify(nou.paraulaCerca)) {
        diferencies.push({ nom: nou.nom, què: "la fila de la paraula cercada", abans: vell.paraulaCerca, ara: nou.paraulaCerca });
      }
    }
  }
  for (const perdut of perNom.keys()) {
    diferencies.push({ nom: perdut, què: "aquest cas ha desaparegut" });
  }
  return diferencies;
}
