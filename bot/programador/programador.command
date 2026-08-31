#!/bin/bash
# Doble clic per obrir el programador de tuits. S'hi mou tot sol, tant se val
# des d'on s'obri. Per aturar-lo: Ctrl+C, o tanca la finestra del Terminal.

cd "$(dirname "$0")" || exit 1

# El Finder no carrega el PATH de l'intèrpret interactiu; hi afegim els llocs
# habituals del Python (Homebrew a Intel i a Apple Silicon) per si de cas.
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

if ! command -v python3 >/dev/null 2>&1; then
    echo "No es troba el python3. Cal instal·lar el Python: https://www.python.org"
    echo "Prem Intro per tancar."
    read -r
    exit 1
fi

python3 servidor.py "$@"
codi=$?

echo
echo "El programador s'ha aturat (codi $codi). Prem Intro per tancar."
read -r
