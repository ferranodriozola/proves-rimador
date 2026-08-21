/*
    PROVA A · Desplegable natiu, a la capçalera i al costat del peixet.

    La més barata de totes: un <select> de tota la vida. Cap JS de menú, cap
    trampa d'accessibilitat, i al mòbil surt el selector del sistema (la roda
    de l'iPhone, la llista d'Android), que és el que la gent ja sap fer anar.

    El preu és que un <option> és text pelat: no hi caben ni el subtítol de
    comarques, ni la marca de "triat", ni el "aviat" com a etiqueta. El
    disabled sí que hi és, però l'única manera de dir per què és posar-ho dins
    del text mateix, entre parèntesis.

    Va DINS de .header-icons, davant del peixet: allà ja hi ha el gap de 22px
    i l'alineació vertical fetes, i el dia que això sigui de debò només vol dir
    afegir el <select> a la plantilla `header` de js/components.js.
*/
(function provaA() {
    const icones = document.querySelector('.header-icons');
    if (!icones) return;

    const actual = provaDialecteActual();

    const capsa = document.createElement('div');
    capsa.className = 'pd-a';

    const etiqueta = document.createElement('label');
    etiqueta.className = 'pd-a-etiqueta';
    etiqueta.setAttribute('for', 'pd-a-select');
    etiqueta.textContent = 'Dialecte';

    const selector = document.createElement('select');
    selector.id = 'pd-a-select';
    PROVA_DIALECTES.forEach(d => {
        const opcio = document.createElement('option');
        opcio.value = d.codi;
        // Els parèntesis són l'únic lloc on cap el "encara no": un <option>
        // no admet cap marca ni cap segona línia.
        opcio.textContent = d.disponible ? d.nom : d.nom + ' (aviat)';
        opcio.disabled = !d.disponible;
        opcio.selected = d.codi === actual;
        selector.appendChild(opcio);
    });

    selector.addEventListener('change', () => {
        provaDesarDialecte(selector.value);
        provaAvisar(selector.value);
    });

    capsa.appendChild(etiqueta);
    capsa.appendChild(selector);
    icones.insertBefore(capsa, icones.firstChild);
})();
