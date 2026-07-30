function pintarFiltresHTML(dadesSempre) {
    const contenidor = document.getElementById('contenidor-filtres');
    if (!contenidor) return;
    contenidor.innerHTML = '';

    const filtres = [
        { id: 'recompte_num_sil', titol: 'Filtre de síl·labes' },
        { id: 'recompte_comenca_per', titol: 'Comença per...' },
        { id: 'recompte_incloure_np', titol: 'Incloure noms propis?' },
        { id: 'recompte_incloure_pl', titol: 'Incloure plurals?' }
    ];

    const nomsTraduïts = {
        '0': 'Indiferent', '1': '1 síl·laba', '2': '2 síl·labes', '3': '3 síl·labes',
        '4': '4 síl·labes', '5': '5 síl·labes', '6': '6 síl·labes',
        'indiferent': 'qualsevol lletra', 'consonant': 'Consonant', 'vocal+h': 'vocal / h',
        'si': 'Sí', 'no': 'No'
    };

    const paletaColors = ['#FF91FF', '#00ffff', '#ffe680', '#b3ffb3', '#ffb3b3', '#d9b3ff', '#ffc266'];

    filtres.forEach(filtre => {
        const dadesFiltre = dadesSempre[filtre.id];
        if (!dadesFiltre) return;

        let totalFiltre = 0;
        let entrades = [];

        for (const [opcio, vegades] of Object.entries(dadesFiltre)) {
            if (opcio !== 'nan' && opcio !== 'None') {
                totalFiltre += vegades;
                entrades.push({ opcio, vegades });
            }
        }

        if (totalFiltre === 0) return;

        entrades.sort((a, b) => b.vegades - a.vegades);

        const divCategoria = document.createElement('div');
        divCategoria.className = 'filtre-categoria';

        const titolElement = document.createElement('h4');
        titolElement.textContent = filtre.titol;
        divCategoria.appendChild(titolElement);

        const barraApilada = document.createElement('div');
        barraApilada.className = 'barra-apilada';

        const llegenda = document.createElement('div');
        llegenda.className = 'llegenda-filtre';

        entrades.forEach((item, index) => {
            const percentatge = ((item.vegades / totalFiltre) * 100).toFixed(1);
            const nomMostrar = nomsTraduïts[item.opcio] || item.opcio;
            const colorTros = paletaColors[index % paletaColors.length];

            const esPetit = parseFloat(percentatge) < 12;

            const segment = document.createElement('div');
            segment.className = 'segment-barra';
            segment.style.width = `${percentatge}%`;
            segment.style.backgroundColor = colorTros;
            segment.title = `${nomMostrar}: ${percentatge}%`;
            
            if (esPetit) {
                segment.innerHTML = `<span class="text-amagat-mobil">${percentatge}%</span>`;
            } else {
                segment.innerHTML = `<span>${percentatge}%</span>`;
            }
            barraApilada.appendChild(segment);

            const itemLlegenda = document.createElement('div');
            itemLlegenda.className = 'item-llegenda';
            itemLlegenda.style.width = `${percentatge}%`;

            const textExtraMobil = esPetit ? `<span class="text-visible-mobil"> (${percentatge}%)</span>` : '';

            itemLlegenda.innerHTML = `
                <div class="color-box" style="background-color: ${colorTros}"></div>
                <span>${nomMostrar}${textExtraMobil}</span>
            `;
            llegenda.appendChild(itemLlegenda);
                });

        divCategoria.appendChild(barraApilada);
        divCategoria.appendChild(llegenda);
        contenidor.appendChild(divCategoria);
    });
}






function omplirLlistesHTML(idElement, arrayDades, esRima = false) {
    const contenidor = document.getElementById(idElement);
    if (!contenidor) return;
    contenidor.innerHTML = '';

    if (!Array.isArray(arrayDades)) {
        console.warn(`[dades] no hi ha dades per a "${idElement}"`);
        return;
    }

    arrayDades.forEach(item => {
        const li = document.createElement('li');
        const negreta = document.createElement('b');
        negreta.textContent = item.paraula;
        li.appendChild(negreta);
        if (esRima) {
            const tipusNet = String(item.tipus).replace('r.', '');
            li.appendChild(document.createTextNode(` (${tipusNet})`));
        }

        li.appendChild(document.createTextNode(`: ${item.cerques}`));
        contenidor.appendChild(li);
    });
}


async function carregarEstadistiques(arxiuJson) {
    const loaderText2 = document.getElementById('loader-text2');
    const loader = document.getElementById('loader');

    try {
        if (loaderText2) loaderText2.textContent = "Descarregant estadístiques (0/2)";

        const resposta = await fetch(`${arxiuJson}?t=${Date.now()}`);
        
        if (!resposta.ok) throw new Error(`Error HTTP: ${resposta.status}`);

        if (loaderText2) loaderText2.textContent = "Dibuixant els gràfics (1/2)";

        const dades = await resposta.json();

        document.getElementById('data-actualitzacio').textContent = dades.actualitzacio;
        document.getElementById('rang-setmana').textContent = "(" + dades.setmana.text_dies + ")";
        document.getElementById('cerques-setmana').textContent = dades.setmana.total_cerques;
        document.getElementById('usuaris-setmana').textContent = dades.setmana.numero_usuaris;
        document.getElementById('cerques-sempre').textContent = dades.sempre.total_cerques;
        document.getElementById('usuaris-sempre').textContent = dades.sempre.numero_usuaris;
        document.getElementById('assonant-sempre').textContent = dades.sempre.recompte_tipus_rima['r.assonant'] || 0;
        document.getElementById('consonant-sempre').textContent = dades.sempre.recompte_tipus_rima['r.consonant'] || 0;

        pintarFiltresHTML(dades.sempre, dades.sempre.total_cerques);
        
        omplirLlistesHTML('llista-paraules-setmana', dades.setmana.top_10_paraules, false);
        omplirLlistesHTML('llista-rimes-setmana', dades.setmana.top_10_rimes, true);
        
        omplirLlistesHTML('llista-paraules-sempre', dades.sempre.top_10_paraules, false);
        omplirLlistesHTML('llista-rimes-sempre', dades.sempre.top_10_rimes, true);
        
        omplirLlistesHTML('llista-fenix', dades.sempre.top_10_fenix, false);
        omplirLlistesHTML('llista-typos', dades.sempre.top_10_typos, false);

        const dadesLinia = dades.sempre.grafic_linia_diaria;
        const ctxLinia = document.getElementById('graficLinia').getContext('2d');
        
        new Chart(ctxLinia, {
            type: 'line',
            data: {
                labels: dadesLinia.map(item => item.data),
                datasets: [{
                    label: 'Cerques',
                    data: dadesLinia.map(item => item.cerques),
                    borderColor: '#d30505',
                    backgroundColor: 'rgba(255, 145, 255, 0.55)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });

        const dadesFormatge = dades.sempre.grafic_formatge_exit;
        const ctxFormatge = document.getElementById('graficFormatge').getContext('2d');
        
        const PALETA = ['#ff0000', '#ff7300', '#fffb00', '#48ff00', '#00ffd5', '#002bff', '#7a00ff', '#ff00c8'];
        const colorsFormatge = dadesFormatge.map((_, i) => PALETA[i % PALETA.length]);

        new Chart(ctxFormatge, {
            type: 'pie',
            data: {
                labels: dadesFormatge.map(item => item.rima),
                datasets: [{
                    data: dadesFormatge.map(item => item.vegades),
                    backgroundColor: colorsFormatge,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let valor = context.raw || 0;
                                return ` ${valor} cerques`;
                            }
                        }
                    }
                }
            }
        });

        setTimeout(() => {
            if (loader) loader.style.display = 'none';
        }, 300);

    } catch (error) {
        console.error(error);
        if (loaderText2) loaderText2.textContent = "ERROR REAL: " + error.message;
        setTimeout(() => {
            if (loader) loader.style.display = 'none';
        }, 5000); 
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.body.id === 'dades') {
        carregarEstadistiques('stats/estadistiques_rimador.json');
    }
});