import json

# --- CONFIGURACIÓ ---
FITXER_ENTRADA = 'verbs_anotats.json'

def filtrar_resultats():
    try:
        with open(FITXER_ENTRADA, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No s'ha trobat el fitxer '{FITXER_ENTRADA}'.")
        return

    verbs_no_ok = []
    totes_categories = set()

    # Analitzem cada verb del diccionari
    for verb, info in data.items():
        estat = info.get("estat", "")
        categories = info.get("categories", [])

        # 1. Filtrem els que no estan OK
        if estat != "OK":
            verbs_no_ok.append((verb, estat))

        # 2. Afegim les categories al conjunt global (el "set" evita duplicats)
        for cat in categories:
            totes_categories.add(cat)

    # --- PRESENTACIÓ DELS RESULTATS ---
    print("\n" + "=" * 60)
    print("📊 INFORME DE RESULTATS DELS VERBS")
    print("=" * 60)

    # Mostrar verbs amb incidències
    print(f"\n1️⃣ Verbs que NO estan OK ({len(verbs_no_ok)}):")
    if verbs_no_ok:
        for verb, estat in verbs_no_ok:
            print(f"   • {verb} ➔ Estat: {estat}")
    else:
        print("   ✔️ Perfecte! No hi ha cap verb amb errors o sense trobar.")

    # Mostrar totes les categories úniques trobades
    print(f"\n2️⃣ Llistat de totes les categories úniques trobades ({len(totes_categories)}):")
    if totes_categories:
        for cat in sorted(totes_categories):
            print(f"   • {cat}")
    else:
        print("   ⚠️ No s'ha trobat cap categoria enlloc.")
        
    print("\n" + "=" * 60)

if __name__ == "__main__":
    filtrar_resultats()