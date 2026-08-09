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
        '0': 'Indiferent', '1': '1s', '2': '2s', '3': '3s',
        '4': '4s', '5': '5s', '6': '6+',
        'indiferent': 'qualsevol lletra', 'consonant': 'consonant', 'vocal+h': 'vocal / h',
        'si': 'Sí', 'no': 'No'
    };

    const temaSober = document.documentElement.getAttribute('data-theme') === 'sober' || document.body.getAttribute('data-theme') === 'sober';
    
    const paletaColors = temaSober 
        ? ['#4d4d4d', '#737373', '#999999', '#bfbfbf', '#d9d9d9', '#8c8c8c', '#e6e6e6']
        : ['#FF91FF', '#00ffff', '#ffe680', '#b3ffb3', '#ffb3b3', '#d9b3ff', '#ffc266']; 

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

        if (filtre.id === 'recompte_num_sil') {
            const opcionsOrdenades = ['1', '2', '3', '4', '5', '6'];
            entrades.sort((a, b) => opcionsOrdenades.indexOf(a.opcio) - opcionsOrdenades.indexOf(b.opcio));
        } else {
            entrades.sort((a, b) => b.vegades - a.vegades);
        }

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

            const segment = document.createElement('div');
            segment.className = 'segment-barra';
            segment.style.width = `${percentatge}%`;
            segment.style.backgroundColor = colorTros;
            segment.title = `${nomMostrar}: ${percentatge}%`;
            // es pinta sempre, l'amaga depurarPercentatges() si no hi cap
            segment.innerHTML = `<span>${percentatge}%</span>`;

            barraApilada.appendChild(segment);

            const itemLlegenda = document.createElement('div');
            itemLlegenda.className = 'item-llegenda';
            itemLlegenda.style.width = `${percentatge}%`;
            itemLlegenda.dataset.pes = percentatge;

            itemLlegenda.innerHTML = `
                <div class="color-box" style="background-color: ${colorTros}"></div>
                <span>${nomMostrar}</span>
            `;
            llegenda.appendChild(itemLlegenda);
        });

        divCategoria.appendChild(barraApilada);
        divCategoria.appendChild(llegenda);
        contenidor.appendChild(divCategoria);
    });

    ajustarEtiquetesFiltres();
}

function ajustarEtiquetesFiltres() {
    depurarPercentatges();
    depurarLlegendes();
}

function depurarPercentatges() {
    const RESPIR = 6; 

    document.querySelectorAll('#contenidor-filtres .segment-barra').forEach(segment => {
        const text = segment.querySelector('span');
        if (!text) return;

        text.classList.remove('text-segment-amagat');

        const ampladaText = text.getBoundingClientRect().width;
        const ampladaSegment = segment.getBoundingClientRect().width;

        if (ampladaText + RESPIR > ampladaSegment) {
            text.classList.add('text-segment-amagat');
        }
    });
}

function depurarLlegendes() {
    const SEPARACIO_MINIMA = 4; 

    document.querySelectorAll('#contenidor-filtres .llegenda-filtre').forEach(llegenda => {
        const items = Array.from(llegenda.querySelectorAll('.item-llegenda'));
        items.forEach(item => item.classList.remove('item-llegenda-amagat'));

        const ocupats = [];

        items
            .sort((a, b) => parseFloat(b.dataset.pes) - parseFloat(a.dataset.pes))
            .forEach(item => {
                const text = item.querySelector('span').getBoundingClientRect();

                const xoca = ocupats.some(altre =>
                    text.left < altre.right + SEPARACIO_MINIMA &&
                    text.right + SEPARACIO_MINIMA > altre.left
                );

                if (xoca) {
                    item.classList.add('item-llegenda-amagat');
                } else {
                    ocupats.push(text);
                }
            });
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
            // Les rimes s'escriuen en transcripció fonètica (aðə, esək):
            // les dibuixem senceres amb la font que té l'AFI, si no la
            // 'a' i la 'ð' surten amb tipografies diferents.
            negreta.className = 'transcripcio';

            const tipusNet = String(item.tipus).replace('r.', '');
            li.appendChild(document.createTextNode(` (${tipusNet})`));
        }

        li.appendChild(document.createTextNode(`: ${item.cerques}`));
        contenidor.appendChild(li);
    });
}

function omplirPodiHTML(idElement, arrayDades, etiqueta) {
    const contenidor = document.getElementById(idElement);
    if (!contenidor) return;
    contenidor.innerHTML = '';

    if (!Array.isArray(arrayDades)) return;

    contenidor.classList.add('podi-graella');

    arrayDades.forEach((item, index) => {
        const lloc = index + 1;

        const li = document.createElement('li');
        li.className = `podi-lloc podi-lloc-${lloc}`;
        li.title = `${item.data}: ${item.total} ${etiqueta}`;

        li.innerHTML = `
            <div class="podi-placa">
                <span class="podi-xifra">${item.total}</span>
                <span class="podi-data">${item.data}</span>
            </div>
            <div class="podi-bloc"><span class="podi-numero">${lloc}</span></div>
        `;
        contenidor.appendChild(li);
    });
}

async function carregarEstadistiques(arxiuJson) {
    const loaderText2 = document.getElementById('loader-text2');
    const loader = document.getElementById('loader');

    try {
        if (loaderText2) loaderText2.textContent = "Descarregant estadístiques (0/2)";

        const resposta = await fetch(`${ARREL}${arxiuJson}?t=${Date.now()}`);

        if (!resposta.ok) throw new Error(`Error HTTP: ${resposta.status}`);

        if (loaderText2) loaderText2.textContent = "Dibuixant els gràfics (1/2)";

        const dades = await resposta.json();

        document.getElementById('data-actualitzacio').textContent = dades.actualitzacio;
        document.getElementById('rang-setmana').textContent = "(" + dades.setmana.text_dies + ")";
        document.getElementById('paraules_uniques_setmana').textContent = dades.setmana.paraules_cercades_uniques;
        document.getElementById('cerques-setmana').textContent = dades.setmana.total_cerques;
        document.getElementById('usuaris-setmana').textContent = dades.setmana.numero_usuaris;
        document.getElementById('paraules_uniques_sempre').textContent = dades.sempre.paraules_cercades_uniques;
        document.getElementById('cerques-totals').textContent = dades.sempre.total_cerques;
        document.getElementById('usuaris-sempre').textContent = dades.sempre.numero_usuaris;
        document.getElementById('assonant-sempre').textContent = dades.sempre.recompte_tipus_rima['r.assonant'];
        document.getElementById('consonant-sempre').textContent = dades.sempre.recompte_tipus_rima['r.consonant'];
        document.getElementById('noms-propis-sempre').textContent = dades.sempre.total_noms_propis;

        window.dadesSempre = dades.sempre; 
        pintarFiltresHTML(dades.sempre);
        
        omplirLlistesHTML('llista-paraules-setmana', dades.setmana.top_10_paraules, false);
        omplirLlistesHTML('llista-rimes-setmana', dades.setmana.top_10_rimes, true);
        
        omplirLlistesHTML('llista-paraules-sempre', dades.sempre.top_10_paraules, false);
        omplirLlistesHTML('llista-rimes-sempre', dades.sempre.top_10_rimes, true);
        
        omplirLlistesHTML('llista-naufragues', dades.sempre.top_10_naufragues, false);
        omplirLlistesHTML('llista-typos', dades.sempre.top_10_typos, false);
        
        if (dades.sempre.top_dies) {
            omplirPodiHTML('podi-cerques', dades.sempre.top_dies.top_cerques, 'cerques');
            omplirPodiHTML('podi-usuaris', dades.sempre.top_dies.top_usuaris, 'usuaris');
            omplirPodiHTML('anti-podi-cerques', dades.sempre.top_dies.anti_top_cerques, 'cerques');
            omplirPodiHTML('anti-podi-usuaris', dades.sempre.top_dies.anti_top_usuaris, 'usuaris');
        }

        // Les etiquetes dels gràfics de formatge també són rimes en
        // transcripció fonètica, i els gràfics es dibuixen en un canvas,
        // on el CSS no hi arriba: li hem de dir a Chart.js quina font ha
        // de fer servir.
        if (window.Chart) {
            Chart.defaults.font.family = getComputedStyle(document.documentElement)
                .getPropertyValue('--font-transcripcio').trim();
        }

        const temaSober = document.documentElement.getAttribute('data-theme') === 'sober' || document.body.getAttribute('data-theme') === 'sober';
        const dadesLinia = dades.grafics.grafic_linia_diaria;
        const ctxLinia = document.getElementById('graficLinia').getContext('2d');
        
        window.graficLiniaObj = new Chart(ctxLinia, {
            type: 'line',
            data: {
                labels: dadesLinia.map(item => item.data),
                datasets: [{
                    label: 'Cerques',
                    data: dadesLinia.map(item => item.cerques),
                    borderColor: temaSober ? '#aa0000' : '#d30505',
                    backgroundColor: temaSober ? 'rgba(170, 0, 0, 0.2)' : 'rgba(255, 145, 255, 0.55)',                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Usuaris únics',
                    data: dadesLinia.map(item => item.usuaris),
                    borderColor: temaSober ? '#555555' : '#0055ff', 
                    backgroundColor: temaSober ? 'rgba(85, 85, 85, 0.2)' : 'rgba(0, 85, 255, 0.2)',
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
                plugins: { legend: { display: true } }
            }
        });

        
        const PALETA = temaSober 
            ? ['#222222', '#4d4d4d', '#737373', '#999999', '#bfbfbf', '#aa0000', '#800000', '#555555'] 
            : ['#ff0000', '#ff7300', '#fffb00', '#48ff00', '#00ffd5', '#002bff', '#7a00ff', '#ff00c8'];

        //agrupar dades petites
        function agruparMenors(dadesArray) {
            const total = dadesArray.reduce((suma, item) => suma + item.vegades, 0);
            const resultat = [];
            let altres = 0;

            dadesArray.forEach(item => {
                const percentatge = (item.vegades / total) * 100;
                if (percentatge < 1) {
                    altres += item.vegades;
                } else {
                    resultat.push(item);
                }
            });

            resultat.sort((a, b) => b.vegades - a.vegades);

            if (altres > 0) {
                resultat.push({ rima: 'Altres', vegades: altres });
            }
            return resultat;
        }


        const dadesFormatgeAss = agruparMenors(dades.grafics.grafic_formatge_exit_assonant);
        const dadesFormatgeCons = agruparMenors(dades.grafics.grafic_formatge_exit_consonant);

        window.dadesFormatgeAss = dadesFormatgeAss; 
        window.dadesFormatgeCons = dadesFormatgeCons;

        //gràfic assonant
        const ctxFormatgeAss = document.getElementById('graficFormatgeASS').getContext('2d');
        const colorsFormatgeAss = dadesFormatgeAss.map((item, i) => 
                    item.rima === 'Altres' ? '#aeaeae' : PALETA[i % PALETA.length]
        );
        window.graficFormatgeAssObj = new Chart(ctxFormatgeAss, {
            type: 'pie',
            data: {
                labels: dadesFormatgeAss.map(item => item.rima),
                datasets: [{
                    data: dadesFormatgeAss.map(item => item.vegades),
                    backgroundColor: colorsFormatgeAss,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
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

        //gràfic consonant
        const ctxFormatgeCons = document.getElementById('graficFormatgeCONS').getContext('2d');
        const colorsFormatgeCons = dadesFormatgeCons.map((item, i) => 
                    item.rima === 'Altres' ? '#aeaeae' : PALETA[i % PALETA.length]
        );

        window.graficFormatgeConsObj = new Chart(ctxFormatgeCons, { 
            type: 'pie',
            data: {
                labels: dadesFormatgeCons.map(item => item.rima),
                datasets: [{
                    data: dadesFormatgeCons.map(item => item.vegades),
                    backgroundColor: colorsFormatgeCons,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
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


let temporitzadorEtiquetes;
window.addEventListener('resize', () => {
    clearTimeout(temporitzadorEtiquetes);
    temporitzadorEtiquetes = setTimeout(ajustarEtiquetesFiltres, 150);
});

function actualitzarColorsGrafics() {
    const temaSober = document.documentElement.getAttribute('data-theme') === 'sober' || document.body.getAttribute('data-theme') === 'sober';
    
    if (window.dadesSempre) {
        pintarFiltresHTML(window.dadesSempre);
    }

    if (window.graficLiniaObj) {
        window.graficLiniaObj.data.datasets[0].borderColor = temaSober ? '#aa0000' : '#d30505';
        window.graficLiniaObj.data.datasets[0].backgroundColor = temaSober ? 'rgba(170, 0, 0, 0.2)' : 'rgba(255, 145, 255, 0.55)';
        
        window.graficLiniaObj.data.datasets[1].borderColor = temaSober ? '#555555' : '#0055ff';
        window.graficLiniaObj.data.datasets[1].backgroundColor = temaSober ? 'rgba(85, 85, 85, 0.2)' : 'rgba(0, 85, 255, 0.2)';
        
        window.graficLiniaObj.update();
    }

    const PALETA = temaSober 
        ? ['#222222', '#4d4d4d', '#737373', '#999999', '#bfbfbf', '#aa0000', '#800000', '#555555'] 
        : ['#ff0000', '#ff7300', '#fffb00', '#48ff00', '#00ffd5', '#002bff', '#7a00ff', '#ff00c8'];

    if (window.graficFormatgeAssObj && window.dadesFormatgeAss) {
        window.graficFormatgeAssObj.data.datasets[0].backgroundColor = window.dadesFormatgeAss.map((item, i) => 
            item.rima === 'Altres' ? (temaSober ? '#e6e4e5' : '#aeaeae') : PALETA[i % PALETA.length]
        );
        window.graficFormatgeAssObj.update();
    }

    if (window.graficFormatgeConsObj && window.dadesFormatgeCons) {
        window.graficFormatgeConsObj.data.datasets[0].backgroundColor = window.dadesFormatgeCons.map((item, i) => 
            item.rima === 'Altres' ? (temaSober ? '#e6e4e5' : '#aeaeae') : PALETA[i % PALETA.length]
        );
        window.graficFormatgeConsObj.update();
    }
}