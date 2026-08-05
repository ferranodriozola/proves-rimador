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

# VARIABLES
cerques_totals = df.drop_duplicates(subset=['Dia', 'Usuari', 'Paraula', 'Tipus de rima', 'Num. síl·', 'Comença per', 'Incloure NP', 'Incloure pl.']).copy()

paraules_cercades = cerques_totals.drop_duplicates(subset=['Paraula']).copy()
paraules_cercades = paraules_cercades[paraules_cercades['Rima'] != '***'].copy()

paraules_cercades_usuaris_diferents = cerques_totals.drop_duplicates(subset=['Paraula', 'Usuari']).copy()

rimes_usuaris_diferents = cerques_totals.drop_duplicates(subset=['Paraula', 'Tipus de rima', 'Usuari']).copy()
rimes_usuaris_diferents = rimes_usuaris_diferents[['Rima', 'Tipus de rima']]
rimes_usuaris_diferents = rimes_usuaris_diferents[rimes_usuaris_diferents['Rima'] != '***'].copy()


#dades i coses del temps
avui = datetime.now(tz_espanya).date()
inici_setmana = avui - timedelta(days=7)
ahir = avui - timedelta(days=1)

data_inici = pd.to_datetime(inici_setmana)
data_fi = pd.to_datetime(ahir) + timedelta(days=1, seconds=-1)


#df paraules fènix
ruta_json_fenix = 'llistes/paraules_fenixs.json' 

with open(ruta_json_fenix, 'r', encoding='utf-8') as arxiu:
    dades_fenix = json.load(arxiu)
llista_paraules_fenix = [item['paraula'] for item in dades_fenix]

df_rimes_fenix = paraules_cercades_usuaris_diferents[paraules_cercades_usuaris_diferents['Paraula'].isin(llista_paraules_fenix)].copy()


#les dues llistes
df_typos = paraules_cercades_usuaris_diferents[paraules_cercades_usuaris_diferents['Rima'] == '***'].copy()


mascara_cerques = (cerques_totals['Data'] >= data_inici) & (cerques_totals['Data'] <= data_fi)
cerques_totals_emmascarat = cerques_totals[mascara_cerques].copy()

paraules_cercades_emmascarades = cerques_totals_emmascarat.drop_duplicates(subset=['Paraula']).copy()
paraules_cercades_emmascarades = paraules_cercades_emmascarades[paraules_cercades_emmascarades['Rima'] != '***'].copy()

paraules_cercades_usuaris_diferents_emmascarat = cerques_totals_emmascarat.drop_duplicates(subset=['Paraula', 'Usuari']).copy()

rimes_usuaris_diferents_emmascarat = cerques_totals_emmascarat.drop_duplicates(subset=['Paraula', 'Tipus de rima', 'Usuari']).copy()
rimes_usuaris_diferents_emmascarat = rimes_usuaris_diferents_emmascarat[['Rima', 'Tipus de rima']]
rimes_usuaris_diferents_emmascarat = rimes_usuaris_diferents_emmascarat[rimes_usuaris_diferents_emmascarat['Rima'] != '***'].copy()

noms_propis = paraules_cercades[paraules_cercades['Codi'].str.startswith('NP')].copy()

print(noms_propis.head())

#funcions
def obtenir_top_paraules(df_dades, n, paraula):
    if paraula == 'paraula':
        return df_dades['Paraula'].value_counts().head(n)
    elif paraula == 'rima':
        recompte = df_dades.groupby(['Rima', 'Tipus de rima']).size().reset_index(name='cerques')
        return recompte.sort_values(by='cerques', ascending=False).head(n)
    else:
        raise ValueError("El paràmetre 'paraula' només pot ser 'paraula' o 'rima'.")

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
    if isinstance(dades, pd.Series):
        df_temp = dades.reset_index()
        df_temp.columns = ['paraula', 'cerques']
        return df_temp.to_dict(orient='records')

    elif isinstance(dades, pd.DataFrame):
        df_temp = dades.rename(columns={'Rima': 'paraula', 'Tipus de rima': 'tipus'})
        return df_temp.to_dict(orient='records')


#execució
dades_json = {
    "actualitzacio": datetime.now(tz_espanya).strftime("%d/%m/%Y %H:%M:%S"),
    "setmana": {
        "text_dies": f"{inici_setmana.day}/{inici_setmana.month} > {ahir.day}/{ahir.month}",
        "top_10_paraules": formatar_top_per_json(obtenir_top_paraules(paraules_cercades_usuaris_diferents_emmascarat, 10, 'paraula')),
        "top_10_rimes": formatar_top_per_json(obtenir_top_paraules(rimes_usuaris_diferents_emmascarat, 10, 'rima')),
        "total_cerques": len(cerques_totals_emmascarat),
        "paraules_cercades_uniques": len(paraules_cercades_emmascarades),
        "numero_usuaris": cerques_totals_emmascarat['Usuari'].nunique(),

    },
    "sempre": {
        "top_10_paraules": formatar_top_per_json(obtenir_top_paraules(paraules_cercades_usuaris_diferents, 10, 'paraula')),
        "top_10_rimes": formatar_top_per_json(obtenir_top_paraules(rimes_usuaris_diferents, 10, 'rima')),
        "total_cerques": len(cerques_totals),
        "paraules_cercades_uniques": len(paraules_cercades),
        "numero_usuaris": cerques_totals['Usuari'].nunique(),
        "recompte_tipus_rima": cerques_totals['Tipus de rima'].value_counts().to_dict(),
        "top_10_fenix": formatar_top_per_json(obtenir_top_paraules(df_rimes_fenix, 10, 'paraula')),
        "top_10_typos": formatar_top_per_json(obtenir_top_paraules(df_typos, 10, 'paraula')),
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

dades_json_versio = {
    "actualitzacio": datetime.now(tz_espanya).strftime("%d/%m/%Y %H:%M:%S")}

ruta_json = 'stats/estadistiques_rimador.json'
ruta_json_versio = 'stats/versio_estadistiques_rimador.json'

with open(ruta_json, 'w', encoding='utf-8') as arxiu:
    json.dump(dades_json, arxiu, ensure_ascii=False, indent=4)

with open(ruta_json_versio, 'w', encoding='utf-8') as arxiu:
    json.dump(dades_json_versio, arxiu, ensure_ascii=False, indent=4)

print(f"Exportació completada amb èxit (hora: {datetime.now(tz_espanya).strftime('%H:%M:%S')})")