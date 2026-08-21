import hashlib
import pandas as pd
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# hora no utc
tz_espanya = ZoneInfo("Europe/Madrid") 

# agafar excel drive i netejar dades
url_google_sheet = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQu2bwhVaSdCKFkzXsqpVdufvVrOFankBE5CTTD1dHMbzhFXnSBgn2mXYgnGjrXt41FgHU6WmIGr7Gw/pub?gid=0&single=true&output=csv"
df = pd.read_csv(url_google_sheet)

df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
df = df.dropna(subset=['Data']).copy()
df['Dia'] = df['Data'].dt.date
df['Usuari'] = df['Usuari'].astype(str)
df['Paraula'] = df['Paraula'].astype(str)
df['Codi'] = df['Codi'].astype(str)
df['Rima'] = df['Rima'].astype(str)
df['Tipus de rima'] = df['Tipus de rima'].astype(str)
df['Num. síl·'] = df['Num. síl·'].astype(str)
df['Comença per'] = df['Comença per'].astype(str)
df['Incloure NP'] = df['Incloure NP'].astype(str)
df['Incloure pl.'] = df['Incloure pl.'].astype(str)

#dades i coses del temps
avui = datetime.now(tz_espanya).date()
inici_setmana = avui - timedelta(days=7)
ahir = avui - timedelta(days=1)

data_inici = pd.to_datetime(inici_setmana)
data_fi = pd.to_datetime(ahir) + timedelta(days=1, seconds=-1)

# VARIABLES
cerques_totals = df.drop_duplicates(subset=['Dia', 'Usuari', 'Paraula', 'Tipus de rima', 'Num. síl·', 'Comença per', 'Incloure NP', 'Incloure pl.']).copy()
cerques_totals = cerques_totals[cerques_totals['Dia'] < avui].copy()

paraules_cercades = cerques_totals[cerques_totals['Rima'] != '***'].drop_duplicates(subset=['Paraula']).copy()

paraules_cercades_usuaris_diferents = cerques_totals.drop_duplicates(subset=['Paraula', 'Usuari']).copy()
paraules_cercades_usuaris_diferents_trobades = paraules_cercades_usuaris_diferents[paraules_cercades_usuaris_diferents['Rima'] != '***'].copy()

rimes_usuaris_diferents = cerques_totals.drop_duplicates(subset=['Paraula', 'Tipus de rima', 'Usuari']).copy()
rimes_usuaris_diferents = rimes_usuaris_diferents[['Rima', 'Tipus de rima']]
rimes_usuaris_diferents = rimes_usuaris_diferents[rimes_usuaris_diferents['Rima'] != '***'].copy()


#df paraules nàufragues
# El del CENTRAL: ara cada dialecte té la seva llista
# (llistes/generar_naufragues.py). Aquí es queda el central perquè les cerques
# registrades fins ara no diuen en quin dialecte es va cercar: el web hi envia
# un camp "dialecte" (vegeu registrarCerca a js/script.js), però és nou i el
# gruix del full encara és d'abans. Quan n'hi hagi prou, aquest top es pot
# partir per dialecte fent servir aquella columna i la llista que li toqui.
ruta_json_naufragues = 'llistes/paraules_naufragues_ca.json'

with open(ruta_json_naufragues, 'r', encoding='utf-8') as arxiu:
    dades_naufragues = json.load(arxiu)
llista_paraules_naufragues = [item['paraula'].lower() for item in dades_naufragues]

df_rimes_naufragues = cerques_totals[cerques_totals['Tipus de rima'] == 'r.consonant'].drop_duplicates(subset=['Paraula', 'Usuari']).copy()
df_rimes_naufragues = df_rimes_naufragues[df_rimes_naufragues['Paraula'].isin(llista_paraules_naufragues)].copy()


#les dues llistes
df_typos = paraules_cercades_usuaris_diferents[paraules_cercades_usuaris_diferents['Rima'] == '***'].copy()


mascara_cerques = (cerques_totals['Data'] >= data_inici) & (cerques_totals['Data'] <= data_fi)
cerques_totals_emmascarat = cerques_totals[mascara_cerques].copy()

paraules_cercades_emmascarades = cerques_totals_emmascarat.drop_duplicates(subset=['Paraula']).copy()
paraules_cercades_emmascarades = paraules_cercades_emmascarades[paraules_cercades_emmascarades['Rima'] != '***'].copy()

paraules_cercades_usuaris_diferents_emmascarat = cerques_totals_emmascarat.drop_duplicates(subset=['Paraula', 'Usuari']).copy()
paraules_cercades_usuaris_diferents_emmascarat_trobades = paraules_cercades_usuaris_diferents_emmascarat[paraules_cercades_usuaris_diferents_emmascarat['Rima'] != '***'].copy()

rimes_usuaris_diferents_emmascarat = cerques_totals_emmascarat.drop_duplicates(subset=['Paraula', 'Tipus de rima', 'Usuari']).copy()
rimes_usuaris_diferents_emmascarat = rimes_usuaris_diferents_emmascarat[['Rima', 'Tipus de rima']]
rimes_usuaris_diferents_emmascarat = rimes_usuaris_diferents_emmascarat[rimes_usuaris_diferents_emmascarat['Rima'] != '***'].copy()

noms_propis = paraules_cercades[paraules_cercades['Codi'].str.startswith('NP')].copy()

#dfs de recència: només serveixen per desempatar els tops (data de l'última cerca),
#no intervenen en cap recompte
recencia_paraules = cerques_totals[cerques_totals['Rima'] != '***']
recencia_paraules_emmascarat = cerques_totals_emmascarat[cerques_totals_emmascarat['Rima'] != '***']
recencia_naufragues = cerques_totals[(cerques_totals['Tipus de rima'] == 'r.consonant') & (cerques_totals['Paraula'].isin(llista_paraules_naufragues))]
recencia_typos = cerques_totals[cerques_totals['Rima'] == '***']

#funcions
def obtenir_top_paraules(df_dades, n, paraula, df_recencia):
    if paraula == 'paraula':
        claus = ['Paraula']
    elif paraula == 'rima':
        claus = ['Rima', 'Tipus de rima']
    else:
        raise ValueError("El paràmetre 'paraula' només pot ser 'paraula' o 'rima'.")

    recompte = df_dades.groupby(claus).size().reset_index(name='cerques')
    ultima_cerca = df_recencia.groupby(claus)['Data'].max().rename('ultima_cerca')
    recompte = recompte.merge(ultima_cerca, on=claus, how='left')

    #en cas d'empat de cerques, primer la que s'ha cercat més recentment
    recompte = recompte.sort_values(by=['cerques', 'ultima_cerca'], ascending=[False, False], kind='stable')
    return recompte.head(n).drop(columns='ultima_cerca')

def obtenir_top_dies(df_dades):
    df_dades = df_dades[df_dades['Dia'] < avui]  
    cerques_per_dia = df_dades['Dia'].value_counts().reset_index()
    cerques_per_dia.columns = ['Dia', 'cerques']
    cerques_top = cerques_per_dia.sort_values(by='cerques', ascending=False).head(3)
    cerques_anti = cerques_per_dia.sort_values(by='cerques', ascending=True).head(3)
    
    usuaris_per_dia = df_dades.groupby('Dia')['Usuari'].nunique().reset_index()
    usuaris_per_dia.columns = ['Dia', 'usuaris']
    usuaris_top = usuaris_per_dia.sort_values(by='usuaris', ascending=False).head(3)
    usuaris_anti = usuaris_per_dia.sort_values(by='usuaris', ascending=True).head(3)

    return {
        "top_cerques": [{"data": d.strftime("%d/%m/%Y"), "total": int(c)} for d, c in zip(cerques_top['Dia'], cerques_top['cerques'])],
        "top_usuaris": [{"data": d.strftime("%d/%m/%Y"), "total": int(u)} for d, u in zip(usuaris_top['Dia'], usuaris_top['usuaris'])],
        "anti_top_cerques": [{"data": d.strftime("%d/%m/%Y"), "total": int(c)} for d, c in zip(cerques_anti['Dia'], cerques_anti['cerques'])],
        "anti_top_usuaris": [{"data": d.strftime("%d/%m/%Y"), "total": int(u)} for d, u in zip(usuaris_anti['Dia'], usuaris_anti['usuaris'])]

    }

def dades_grafic_linia(df_dades):
    avui = datetime.now(tz_espanya).date()
    data_inici = avui - timedelta(days=30)
    data_fi = avui - timedelta(days=1)

    mascara_temps = (df_dades['Dia'] >= data_inici) & (df_dades['Dia'] <= data_fi)
    df_filtrat = df_dades[mascara_temps]

    recompte_diari = df_filtrat['Dia'].value_counts()

    resultat = []

    for i in range(30, 0, -1):
        dia_actual = avui - timedelta(days=i)
        total_cerques = recompte_diari.get(dia_actual, 0)
        total_usuaris = df_filtrat[df_filtrat['Dia'] == dia_actual]['Usuari'].nunique()

        resultat.append({
            "data": dia_actual.strftime("%d/%m"),
            "cerques": int(total_cerques),
            "usuaris": int(total_usuaris)
        })

    return resultat

def dades_grafic_formatge_totes(df_dades, tipus_rima):
    df_filtrat = df_dades[df_dades['Tipus de rima'] == tipus_rima]
    recompte = df_filtrat['Rima'].value_counts()

    return [
        {"rima": str(rima), "vegades": int(total)}
        for rima, total in recompte.items()
    ]


def formatar_top_per_json(dades):
    df_temp = dades.rename(columns={'Paraula': 'paraula', 'Rima': 'paraula', 'Tipus de rima': 'tipus'})
    return df_temp.to_dict(orient='records')


#execució
dades_json = {
    "actualitzacio": datetime.now(tz_espanya).strftime("%d/%m/%Y %H:%M:%S"),
    "setmana": {
        "text_dies": f"{inici_setmana.day}/{inici_setmana.month} > {ahir.day}/{ahir.month}",
        "top_10_paraules": formatar_top_per_json(obtenir_top_paraules(paraules_cercades_usuaris_diferents_emmascarat_trobades, 10, 'paraula', recencia_paraules_emmascarat)),
        "top_10_rimes": formatar_top_per_json(obtenir_top_paraules(rimes_usuaris_diferents_emmascarat, 10, 'rima', recencia_paraules_emmascarat)),
        "total_cerques": len(cerques_totals_emmascarat),
        "paraules_cercades_uniques": len(paraules_cercades_emmascarades),
        "numero_usuaris": cerques_totals_emmascarat['Usuari'].nunique(),

    },
    "sempre": {
        "top_10_paraules": formatar_top_per_json(obtenir_top_paraules(paraules_cercades_usuaris_diferents_trobades, 10, 'paraula', recencia_paraules)),
        "top_10_rimes": formatar_top_per_json(obtenir_top_paraules(rimes_usuaris_diferents, 10, 'rima', recencia_paraules)),
        "total_cerques": len(cerques_totals),
        "paraules_cercades_uniques": len(paraules_cercades),
        "numero_usuaris": cerques_totals['Usuari'].nunique(),
        "recompte_tipus_rima": cerques_totals['Tipus de rima'].value_counts().to_dict(),
        "top_10_naufragues": formatar_top_per_json(obtenir_top_paraules(df_rimes_naufragues, 10, 'paraula', recencia_naufragues)),
        "top_10_typos": formatar_top_per_json(obtenir_top_paraules(df_typos, 10, 'paraula', recencia_typos)),
        "total_noms_propis": len(noms_propis),
        "recompte_num_sil": cerques_totals['Num. síl·'].value_counts().to_dict(),
        "recompte_comenca_per": cerques_totals['Comença per'].value_counts().to_dict(),
        "recompte_incloure_np": cerques_totals['Incloure NP'].value_counts().to_dict(),
        "recompte_incloure_pl": cerques_totals['Incloure pl.'].value_counts().to_dict(),
        "top_dies": obtenir_top_dies(cerques_totals)
    },
    "grafics": {
        "grafic_linia_diaria": dades_grafic_linia(cerques_totals),
        "grafic_formatge_exit_assonant": dades_grafic_formatge_totes(rimes_usuaris_diferents, "r.assonant"),
        "grafic_formatge_exit_consonant": dades_grafic_formatge_totes(rimes_usuaris_diferents, "r.consonant"),
    }
}

ruta_json = 'stats/estadistiques_rimador.json'
ruta_versions = 'stats/versions_stats.json'

with open(ruta_json, 'w', encoding='utf-8') as arxiu:
    json.dump(dades_json, arxiu, ensure_ascii=False, indent=4)


def resum(cami):
    """Sha256 truncat, igual que diccionaris/python/versions.py i
    llistes/versions.py: la versió és un resum del contingut, no un
    comptador ni una hora que caldria recordar de pujar."""
    calculador = hashlib.sha256()
    with open(cami, 'rb') as fitxer:
        for tros in iter(lambda: fitxer.read(1024 * 1024), b''):
            calculador.update(tros)
    return calculador.hexdigest()[:12]


with open(ruta_versions, 'w', encoding='utf-8') as arxiu:
    json.dump({
        "fitxers": {"estadistiques_rimador.json": resum(ruta_json)},
        "generat": datetime.now(tz_espanya).strftime("%Y-%m-%d %H:%M:%S %Z"),
    }, arxiu, ensure_ascii=False, indent=2)

print(f"Exportació completada amb èxit (hora: {datetime.now(tz_espanya).strftime('%H:%M:%S')})")