"""
procesar_datos.py
Lee ventas desde MySQL local, genera datos.json y lo sube a GitHub.
Ejecutar manualmente: python procesar_datos.py
Ejecucion automatica: Programador de tareas de Windows (ver README)
"""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import mysql.connector

# ══════════════════════════════════════════════════════════
#  CONFIGURACION — editá estos valores
# ══════════════════════════════════════════════════════════
DB = {
    'host':     'localhost',
    'port':     3306,
    'user':     'root',
    'password': 'tu_password',   # <-- cambiá esto
    'database': 'tu_base',       # <-- cambiá esto
}

TABLA        = 'ventas'          # nombre de la tabla
OUTPUT_PATH  = 'datos.json'
GITHUB_PUSH  = True              # False para solo generar el JSON sin subir

COMBUSTIBLES = ['SUPER 95', 'PREMIUM', 'GASOIL', 'GAS OIL', 'QUANTIUM', 'NAFTA']

# ══════════════════════════════════════════════════════════
#  LECTURA DESDE MYSQL
# ══════════════════════════════════════════════════════════
def leer_mysql():
    print("Conectando a MySQL...")
    try:
        conn = mysql.connector.connect(**DB)
    except mysql.connector.Error as e:
        print(f"ERROR al conectar a MySQL: {e}")
        sys.exit(1)

    query = f"""
        SELECT
            id, fecha, caja, concepto, matricula, kmts,
            cuenta_corriente, titular, rut, producto,
            cantidad, dto, chofer, costo_ref_franquicia,
            tipo_iva, total_sin_imp, total_impuestos, total
        FROM {TABLA}
        ORDER BY fecha
    """
    print("Leyendo datos...")
    df = pd.read_sql(query, conn)
    conn.close()
    print(f"  {len(df):,} registros leídos")
    return df

# ══════════════════════════════════════════════════════════
#  PROCESAMIENTO
# ══════════════════════════════════════════════════════════
def es_combustible(p):
    if pd.isna(p): return False
    return any(k in str(p).upper() for k in COMBUSTIBLES)

def preparar(df):
    df = df.copy()
    df['total']          = pd.to_numeric(df['total'],          errors='coerce').fillna(0)
    df['total_sin_imp']  = pd.to_numeric(df['total_sin_imp'],  errors='coerce').fillna(0)
    df['total_impuestos']= pd.to_numeric(df['total_impuestos'],errors='coerce').fillna(0)
    df['cantidad']       = pd.to_numeric(df['cantidad'],        errors='coerce').fillna(0)
    df['fecha']          = pd.to_datetime(df['fecha'],          errors='coerce')
    df['Anio']           = df['fecha'].dt.year.astype('Int64')
    df['Mes']            = df['fecha'].dt.month.astype('Int64')
    df['DiaStr']         = df['fecha'].dt.strftime('%-d/%-m')
    df['Hora']           = df['fecha'].dt.hour.astype('Int64')
    df['DiaSemana']      = df['fecha'].dt.day_name().map({
        'Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miércoles',
        'Thursday':'Jueves','Friday':'Viernes','Saturday':'Sábado','Sunday':'Domingo'
    })
    df['cat'] = df['producto'].apply(lambda p: 'comb' if es_combustible(p) else 'mini')
    return df

def top_prod(sub, n=15):
    g = sub.groupby(['producto','cat'])['total'].sum().sort_values(ascending=False).head(n)
    return [{'n': p, 'v': round(float(v), 2), 'cat': c} for (p, c), v in g.items()]

def vd(sub, dias):
    g = sub.groupby('DiaStr')['total'].sum()
    return {d: round(float(g.get(d, 0)), 2) for d in dias}

def horas(sub):
    g = sub.groupby('Hora')['total'].sum()
    return {str(int(h)): round(float(v), 2) for h, v in g.items()}

def procesar(df):
    raw = {}
    for (anio, mes), grp in df.groupby(['Anio', 'Mes']):
        a, m = str(int(anio)), str(int(mes))
        dias = sorted(grp['DiaStr'].dropna().unique(),
                      key=lambda x: (int(x.split('/')[1]), int(x.split('/')[0])))
        comb = grp[grp['cat'] == 'comb']
        mini = grp[grp['cat'] == 'mini']
        raw.setdefault(a, {})[m] = {
            'dias':  dias,
            'todas': {
                'vd':         vd(grp, dias),
                'tt':         int(grp['concepto'].nunique()),
                'pr':         top_prod(grp, 15),
                'totComb':    round(float(comb['total'].sum()), 2),
                'totMini':    round(float(mini['total'].sum()), 2),
                'litrosComb': round(float(comb['cantidad'].sum()), 1),
            },
            'comb': {
                'vd':    vd(comb, dias),
                'tt':    int(comb['concepto'].nunique()),
                'pr':    top_prod(comb, 10),
                'litros':round(float(comb['cantidad'].sum()), 1),
            },
            'mini': {
                'vd': vd(mini, dias),
                'tt': int(mini['concepto'].nunique()),
                'pr': top_prod(mini, 10),
            },
            'horas': horas(grp),
        }

    # Día de semana
    dias_ord = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
    vds = df.groupby('DiaSemana').agg(
        Total=('total','sum'),
        Dias=('fecha', lambda x: x.dt.date.nunique())
    ).reindex(dias_ord).fillna(0)
    vds['Prom'] = (vds['Total'] / vds['Dias'].replace(0, 1)).round(2)
    dia_semana = [{'d': d, 'v': round(float(vds.loc[d, 'Prom']), 2)}
                  for d in dias_ord if d in vds.index]

    # Distribución ticket
    boletas = df.groupby('concepto')['total'].sum()
    bins   = [0, 500, 2000, 10000, 50000, float('inf')]
    labels = ['< $500','$500–$2k','$2k–$10k','$10k–$50k','> $50k']
    dist   = pd.cut(boletas, bins=bins, labels=labels).value_counts().reindex(labels).fillna(0)
    ticket_dist  = [{'r': r, 'n': int(n)} for r, n in dist.items()]
    ticket_stats = {
        'promedio': round(float(boletas.mean()), 2),
        'mediana':  round(float(boletas.median()), 2),
        'max':      round(float(boletas.max()), 2),
        'total':    int(len(boletas)),
    }

    # Top RUTs crédito combustible
    cred = df[df['cuenta_corriente'].notna() & df['rut'].notna() & (df['cat'] == 'comb')]
    top_rut_g = cred.groupby(['rut','titular']).agg(
        total=('total','sum'), litros=('cantidad','sum'), boletas=('concepto','nunique')
    ).sort_values('total', ascending=False).head(10).reset_index()
    top_rut = [{
        'rut':     str(r['rut']),
        'titular': str(r['titular']) if pd.notna(r['titular']) else str(r['rut']),
        'total':   round(float(r['total']), 2),
        'litros':  round(float(r['litros']), 1),
        'boletas': int(r['boletas']),
    } for _, r in top_rut_g.iterrows()]

    # Top matrículas
    mat = df[df['matricula'].notna() & (df['cat'] == 'comb')]
    top_mat_g = mat.groupby('matricula').agg(
        total=('total','sum'), litros=('cantidad','sum'), visitas=('concepto','nunique')
    ).sort_values('total', ascending=False).head(10).reset_index()
    top_mat = [{
        'mat':    str(r['matricula']),
        'total':  round(float(r['total']), 2),
        'litros': round(float(r['litros']), 1),
        'visitas':int(r['visitas']),
    } for _, r in top_mat_g.iterrows()]

    return {
        'generado':    pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
        'raw':         raw,
        'diaSemana':   dia_semana,
        'ticketDist':  ticket_dist,
        'ticketStats': ticket_stats,
        'topRUT':      top_rut,
        'topMat':      top_mat,
    }

# ══════════════════════════════════════════════════════════
#  SUBIDA A GITHUB
# ══════════════════════════════════════════════════════════
def push_github():
    print("Subiendo a GitHub...")
    cmds = [
        ['git', 'add', 'datos.json'],
        ['git', 'commit', '-m', f'datos: actualización automática {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}'],
        ['git', 'push'],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # "nothing to commit" no es un error real
            if 'nothing to commit' in result.stdout + result.stderr:
                print("  Sin cambios para subir")
                return
            print(f"  ERROR en '{' '.join(cmd)}':\n{result.stderr}")
            sys.exit(1)
    print("  ✓ GitHub actualizado")

# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════
if __name__ == '__main__':
    df_raw   = leer_mysql()
    df       = preparar(df_raw)
    output   = procesar(df)

    Path(OUTPUT_PATH).write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    meses = {a: list(m.keys()) for a, m in output['raw'].items()}
    print(f"✓ {OUTPUT_PATH} generado — {meses}")

    if GITHUB_PUSH:
        push_github()

    print("✓ Proceso completado")
