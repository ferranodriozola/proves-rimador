document.addEventListener("DOMContentLoaded", function() {
    // 1. Data límit global: El banner deixa d'existir per a TOTHOM passat aquest dia
    const dataLimitGlobal = new Date("2026-09-18T23:59:59").getTime(); 
    const tempsActual = new Date().getTime();
    
    // 2. Clau d'usuari: Comprovem si aquest usuari concret ja l'ha tancat
    const clauBanner = "bannerTancatDefinitivament";
    const bannerJaTancat = localStorage.getItem(clauBanner);

    // 3. Condició: Si NO l'ha tancat mai I encara estem dins dels 7 dies globals, el mostrem
    if (!bannerJaTancat && tempsActual <= dataLimitGlobal) {
        mostrarBanner();
    }

    function mostrarBanner() {
        // Creem l'element del banner dinàmicament
        const banner = document.createElement("div");
        banner.id = "el-meu-banner";
        banner.innerHTML = `
            <div class="banner-contingut">
                <p>Hola! Aquesta és una notificació important per als propers 7 dies.</p>
                <!-- El botó comença desactivat i mostrant els segons -->
                <button id="tancar-banner" disabled>✕ (5s)</button>
            </div>
        `;
        
        document.body.prepend(banner);

        const botoTancar = document.getElementById("tancar-banner");
        
        // 4. Temporitzador de 5 segons
        let segonsRestants = 5;
        const interval = setInterval(() => {
            segonsRestants--;
            if (segonsRestants > 0) {
                botoTancar.innerText = `✕ (${segonsRestants}s)`;
            } else {
                // Han passat els 5 segons: activem el botó
                clearInterval(interval);
                botoTancar.innerText = "✕"; // Deixem només la creu
                botoTancar.disabled = false; // Permetem fer clic
                botoTancar.classList.add("actiu"); // Hi afegim una classe per canviar l'estil
            }
        }, 1000); // S'executa cada 1000 ms (1 segon)

        // 5. Acció en fer clic a la creu
        botoTancar.addEventListener("click", function() {
            // Només fa cas si el botó ja no està desactivat
            if (!botoTancar.disabled) {
                // Guardem al navegador que AQUEST usuari ja l'ha tancat PER SEMPRE
                localStorage.setItem(clauBanner, "true");
                // Eliminem el banner
                banner.remove();
            }
        });
    }
});