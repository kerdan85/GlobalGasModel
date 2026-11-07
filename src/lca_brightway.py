# -*- coding: utf-8 -*-
"""
=====================================================================
ACV / LCA en Brightway 2.5  --  Energy Sovereignty Leakage (gas paper)
Ivan Garcia Kerdan (Tec de Monterrey)
=====================================================================
Proceso-LCA de los dos combustibles que compiten en el margen de fuga:
gas de esquisto de EE.UU. entregado a Asia como GNL, frente al carbon
asiatico que desplazaria. Calcula la intensidad de GEI POR ETAPA del
ciclo de vida, en gCO2e por MJ entregado, a GWP100 y GWP20, con fondo
ecoinvent. Escribe el MISMO esquema CSV que src/lca.py (parametrico),
para que la misma figura / balance de emisiones lo consuman -- y para
comparar parametrico vs ecoinvent (punto de robustez).

Convenciones reutilizadas del proyecto de materiales
(brightway_acv_completo.py): resolver_metodos() por palabras clave,
_find() determinista por nombre+producto+ubicacion, buscar(), CONFIG/EI_MAP.

EJECUTAR EN TU EQUIPO (Brightway + ecoinvent con licencia; no en el sandbox):
    python -m src.lca_brightway
Primero verifica CONFIG, EI_MAP y las CANTIDADES por MJ con buscar()/_find().
=====================================================================
"""
import os, csv
import numpy as np

import bw2data as bd
import bw2calc as bc

# =====================================================================
# CONFIG  (EDITA a tu instalacion)
# =====================================================================
CONFIG = dict(
    # Proyecto DEDICADO a este paper (separado del de materiales). Un proyecto
    # nuevo esta VACIO: hay que provisionarlo UNA vez con ecoinvent + metodos.
    # Opciones (ver preparar_proyecto()): clonar un proyecto que ya tenga
    # ecoinvent, o importar ecoinvent de cero con tus credenciales.
    PROJECT   = "gas_leakage_lca",
    FG_DB     = "fg_gas_leakage",
    EI_DB     = "ecoinvent-3.9.1-cutoff",      # de tu proyecto 'bw25-tuto'
    BIOSPHERE = "ecoinvent-3.9.1-biosphere",   # de tu proyecto 'bw25-tuto'
    OUT_DIR   = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs"),
    N_MONTECARLO = 500,
    SEED      = 42,
    # densidades energeticas (LHV). En ecoinvent 3.9.1 el gas natural esta en
    # METRO CUBICO y el carbon en KILOGRAMO.
    GAS_MJ_PER_M3  = 36.0,     # gas natural (~36 MJ/m3 LHV)
    COAL_MJ_PER_KG = 24.0,     # carbon (hard coal)
    COAL_TRANSPORT_KM = 600.0, # distancia ferroviaria media del carbon (tkm)
    KG_TO_G   = 1000.0,        # score de Brightway (kgCO2e) -> gCO2e
    # Metodos LCIA EXACTOS (de tu ecoinvent 3.9.1). IPCC 2021, categoria
    # agregada 'climate change' (incluye CO2 fosil + CH4 fosil). Metano fosil:
    # GWP100~30, GWP20~82.5 (coincide con el ledger parametrico del paper).
    METHOD_GWP100 = ('ecoinvent-3.9.1', 'IPCC 2021', 'climate change', 'global warming potential (GWP100)'),
    METHOD_GWP20  = ('ecoinvent-3.9.1', 'IPCC 2021', 'climate change', 'global warming potential (GWP20)'),
)

# Indicadores por PALABRAS CLAVE (robusto a la version de LCIA instalada).
# Se prueban varios juegos de palabras por indicador (los nombres varian:
# "GWP100", "GWP 100", "100 year", "100a"...). Se prefiere IPCC 2021.
DESIRED = {
    "GWP100": [["gwp100"], ["gwp", "100"], ["global warming", "100"], ["climate change", "100"]],
    "GWP20":  [["gwp20"],  ["gwp", "20"],  ["global warming", "20"],  ["climate change", "20"]],
}
PREFERIR = "IPCC 2021"
METODOS = {}   # se llena con resolver_metodos()

# =====================================================================
# PROCESOS ECOINVENT DE FONDO (verifica cada uno con buscar())
# =====================================================================
# Procesos ecoinvent 3.9.1 confirmados con buscar():
#  * El GNL importado de EE.UU. "evaporado" a alta presion en destino agrupa
#    TODA la cadena (extraccion -> licuefaccion -> transporte -> regasificacion)
#    en "natural gas, high pressure" (m3). Le sumamos solo la COMBUSTION.
#  * Carbon: mina+preparacion (kg) + transporte ferroviario (tkm) + combustion.
EI_MAP = dict(
    gas_us_chain = dict(name="evaporation of natural gas, import from US",
                        product="natural gas, high pressure", loc="RoW"),
    coal_mine    = dict(name="hard coal mine operation and hard coal preparation",
                        product="hard coal", loc="RoW"),
    coal_train   = dict(name="market group for transport, freight train",
                        product="transport, freight train", loc="GLO"),
)

# Cantidades por 1 MJ ENTREGADO.
#   tech = exchange a ecoinvent (amount en la unidad del proceso)
#   bio  = emision directa de biosfera (combustion CO2)
# La fuga de metano upstream va DENTRO de la cadena ecoinvent (no se anade a mano)
# -> es la estimacion independiente que queremos comparar con el parametrico.
def _gas_stage_specs():
    m3_gas = 1.0 / CONFIG["GAS_MJ_PER_M3"]          # m3 gas por MJ
    co2_comb_kg = 0.0561                            # kg CO2 fosil por MJ (combustion gas)
    return {
        "Supply chain (extraction-liquefaction-shipping-regas)":
            [("tech", "gas_us_chain", m3_gas)],
        "Combustion": [("bio", "CO2", co2_comb_kg)],
    }

def _coal_stage_specs():
    kg_coal = 1.0 / CONFIG["COAL_MJ_PER_KG"]
    tkm = (kg_coal / 1000.0) * CONFIG["COAL_TRANSPORT_KM"]   # ton-km por MJ
    co2_comb_kg = 0.0946                            # kg CO2 fosil por MJ (combustion carbon)
    return {
        "Mining & preparation": [("tech", "coal_mine", kg_coal)],
        "Transport":            [("tech", "coal_train", tkm)],
        "Combustion":           [("bio", "CO2", co2_comb_kg)],
    }

# =====================================================================
# HELPERS (reutilizados del proyecto de materiales)
# =====================================================================
def _set_current(name):
    """set_current SIN el auto-update de bw2data 4.7 (que revienta si un metodo
    LCIA tiene datos intermedios corruptos, p.ej. 'cml-v48-2016-no-ltaa')."""
    try:
        bd.projects.set_current(name, update=False)
    except TypeError:      # versiones sin el kwarg 'update'
        bd.projects.set_current(name)


def setup_proyecto():
    _set_current(CONFIG["PROJECT"])
    print("Proyecto:", CONFIG["PROJECT"])


def guardar_credenciales_ecoinvent(username=None, password=None):
    """Guarda credenciales ecoinvent UNA vez (no en el codigo)."""
    import ecoinvent_interface as ei
    user = username or os.environ.get("ECOINVENT_USERNAME")
    pwd = password or os.environ.get("ECOINVENT_PASSWORD")
    if not (user and pwd):
        raise ValueError("Pasa username/password o exporta ECOINVENT_USERNAME/PASSWORD.")
    ei.permanent_setting("username", user); ei.permanent_setting("password", pwd)
    print("Credenciales ecoinvent guardadas.")


def preparar_proyecto(desde=None, version="3.10", system_model="cutoff"):
    """Provisiona el proyecto DEDICADO (CONFIG['PROJECT']) UNA sola vez.

    desde = nombre de un proyecto que YA tiene ecoinvent  -> lo CLONA (rapido,
            sin volver a descargar).  Descubrelo con estado_proyectos().
    desde = None  -> importa ecoinvent de cero (requiere credenciales; usa
            guardar_credenciales_ecoinvent() antes, o variables de entorno).
    """
    import bw2io as bi
    if desde:
        if desde not in bd.projects:
            raise ValueError(f"El proyecto origen '{desde}' no existe. Ve estado_proyectos().")
        _set_current(desde)
        # borra el destino si ya existe (vacio) -- copy_project no sobrescribe
        if CONFIG["PROJECT"] in bd.projects:
            print(f"Borrando proyecto destino vacio '{CONFIG['PROJECT']}'...")
            bd.projects.delete_project(CONFIG["PROJECT"], delete_dir=True)
            _set_current(desde)   # asegurar que seguimos en el origen
        bd.projects.copy_project(CONFIG["PROJECT"], switch=True)
        print(f"Clonado '{desde}' -> '{CONFIG['PROJECT']}'. "
              f"{len(bd.databases)} dbs, {len(bd.methods)} metodos.")
        return
    # importacion fresca
    _set_current(CONFIG["PROJECT"])
    bi.bw2setup()                                   # biosphere + metodos LCIA base
    if CONFIG["EI_DB"] not in bd.databases:
        print("Importando ecoinvent (puede tardar)...")
        bi.import_ecoinvent_release(version=version, system_model=system_model)
    print(f"Listo '{CONFIG['PROJECT']}': {len(bd.databases)} dbs, {len(bd.methods)} metodos.")
    print("Confirma que CONFIG['EI_DB'] y ['BIOSPHERE'] coinciden con:", list(bd.databases))

def buscar(texto, db=None, n=12):
    db = db or CONFIG["EI_DB"]
    for a in bd.Database(db).search(texto, limit=n):
        print(f"  {a['name']} | {a.get('reference product','')} | {a.get('location','')} | {a.get('unit','')}")

def listar_metodos(filtro=""):
    f = filtro.lower()
    for m in sorted(bd.methods):
        if f in " | ".join(m).lower():
            print("  ", m)

def resolver_metodos(preferir=PREFERIR):
    """Empareja cada indicador con el metodo REAL instalado. Prueba varios
    juegos de palabras clave por indicador (nombres varian entre versiones)."""
    todos = list(bd.methods); res = {}
    for etiqueta, kw_sets in DESIRED.items():
        best = None
        for kws in kw_sets:                       # prueba juegos en orden
            cand = []
            for m in todos:
                s = " | ".join(m).lower()
                if all(k.lower() in s for k in kws):
                    pts = (10 if preferir.lower() in s else 0) \
                          - (8 if "obsolete" in s else 0) - (4 if "superseded" in s else 0)
                    cand.append((pts, m))
            if cand:
                cand.sort(key=lambda x: x[0], reverse=True); best = cand[0][1]; break
        if best:
            res[etiqueta] = best
        else:
            print(f"  [!] sin metodo automatico para '{etiqueta}'.")
    return res


def diagnostico_metodos():
    """Imprime metodos candidatos (para fijar CONFIG['METHOD_GWP100/20'])."""
    print(f"  (proyecto actual: {bd.projects.current}; {len(bd.methods)} metodos totales)")
    print("Metodos que contienen ipcc / warming / gwp / climate:")
    n = 0
    for m in sorted(bd.methods):
        s = " | ".join(m).lower()
        if any(k in s for k in ("ipcc", "warming", "gwp", "climate")):
            print("   ", m); n += 1
    if n == 0:
        print("   (ninguno) -> este proyecto no tiene metodos LCIA importados.")
        print("   Corre  estado_proyectos()  para ver que proyecto SI tiene datos.")


def estado_proyectos():
    """Enumera TODOS los proyectos Brightway de ESTA maquina con su numero de
    bases de datos y metodos, para encontrar cual tiene ecoinvent + LCIA.
    Usa update=False para no disparar el auto-update que revienta, y tolera
    proyectos con datos corruptos."""
    print(f"Directorio de datos Brightway: {getattr(bd.projects, 'dir', '?')}\n")
    print(f"{'proyecto':38s} {'#dbs':>5} {'#metodos':>9}   bases de datos")
    for p in list(bd.projects):
        try:
            _set_current(p.name)
            dbs = list(bd.databases)
            print(f"{p.name:38s} {len(dbs):5d} {len(bd.methods):9d}   {dbs}")
        except Exception as e:
            print(f"{p.name:38s}   [error: {type(e).__name__}: {str(e)[:50]}]")
    print("\n-> Elige el proyecto con ecoinvent (muchas dbs/metodos) para "
          "preparar_proyecto(desde='<ese>'), y confirma EI_DB/BIOSPHERE.")

_FIND_CACHE = {}
def _find(spec, db=None):
    db = db or CONFIG["EI_DB"]
    ck = (db, spec["name"], spec.get("product", ""), spec.get("loc", ""))
    if ck in _FIND_CACHE:
        return _FIND_CACHE[ck]
    name, prod, loc = spec["name"], spec.get("product", ""), spec.get("loc", "")
    cands = [a for a in bd.Database(db)
             if name in a["name"] and prod in a.get("reference product", "")]
    if not cands:
        cands = [a for a in bd.Database(db) if name in a["name"]]
    if not cands:
        raise ValueError(f"Sin coincidencias ecoinvent para {spec}. Usa buscar('{name}').")
    def _rank(a):
        l = a.get("location", "")
        pref = 0 if l == loc else 1 if l == "RoW" else 2 if l == "GLO" else 3
        return (pref, a.get("name", ""), str(a.get("code", "")))
    cands.sort(key=_rank)
    _FIND_CACHE[ck] = cands[0]
    return cands[0]

def _bio_flow(kind):
    """Devuelve la key del flujo de biosfera para CO2 fosil o CH4 fosil (aire)."""
    bio = bd.Database(CONFIG["BIOSPHERE"])
    want = "Carbon dioxide, fossil" if kind == "CO2" else "Methane, fossil"
    cands = [f for f in bio if f.get("name") == want
             and (f.get("categories") or ("",))[0] == "air"]
    if not cands:
        cands = [f for f in bio if want.split(",")[0] in f.get("name", "")
                 and (f.get("categories") or ("",))[0] == "air"]
    if not cands:
        raise ValueError(f"No se encontro el flujo de biosfera '{want}' en {CONFIG['BIOSPHERE']}.")
    return cands[0].key

# =====================================================================
# CONSTRUCCION DEL PRIMER PLANO: una actividad por (combustible, etapa)
# =====================================================================
def construir_foreground():
    ei = CONFIG["EI_DB"]
    if CONFIG["FG_DB"] in bd.databases:
        del bd.databases[CONFIG["FG_DB"]]
    fg = bd.Database(CONFIG["FG_DB"]); data = {}
    co2_key, ch4_key = _bio_flow("CO2"), _bio_flow("CH4")

    def add_stage(fuel, stage, specs):
        key = (CONFIG["FG_DB"], f"{fuel}__{stage}")
        exch = [dict(input=key, amount=1.0, type="production")]
        for kind, ref, amount in specs:
            if amount == 0:
                continue
            if kind == "tech":
                act = _find(EI_MAP[ref], ei)
                exch.append(dict(input=act.key, amount=amount, type="technosphere"))
            else:  # bio
                bkey = co2_key if ref == "CO2" else ch4_key
                exch.append(dict(input=bkey, amount=amount, type="biosphere"))
        data[key] = dict(name=f"{fuel}: {stage}", unit="megajoule",
                         location="GLO", exchanges=exch)

    for stage, specs in _gas_stage_specs().items():
        add_stage("gas", stage, specs)
    for stage, specs in _coal_stage_specs().items():
        add_stage("coal", stage, specs)
    fg.write(data)
    print(f"  primer plano '{CONFIG['FG_DB']}' con {len(data)} actividades-etapa.")
    return fg

# =====================================================================
# CALCULO: intensidad por etapa (gCO2e/MJ) a GWP100 y GWP20
# =====================================================================
def intensidades_por_etapa():
    fg = bd.Database(CONFIG["FG_DB"])
    rows = {"gas": {}, "coal": {}}
    for act in fg:
        fuel, stage = act["name"].split(":", 1)
        fuel = fuel.strip(); stage = stage.strip()
        lca = bc.LCA({act: 1}, next(iter(METODOS.values()))); lca.lci()
        vals = {}
        for etq, m in METODOS.items():
            lca.switch_method(m); lca.lcia()
            vals[etq] = lca.score * CONFIG["KG_TO_G"]
        rows[fuel][stage] = (round(vals.get("GWP100", 0), 2), round(vals.get("GWP20", 0), 2))
        print(f"  {fuel:4s} {stage:26s}: {vals.get('GWP100',0):7.1f} / {vals.get('GWP20',0):7.1f}")
    return rows["gas"], rows["coal"]

def run(save=True):
    setup_proyecto()
    METODOS.update(resolver_metodos())
    # overrides manuales de CONFIG (tienen prioridad)
    if CONFIG.get("METHOD_GWP100"):
        METODOS["GWP100"] = tuple(CONFIG["METHOD_GWP100"])
    if CONFIG.get("METHOD_GWP20"):
        METODOS["GWP20"] = tuple(CONFIG["METHOD_GWP20"])
    print("Metodos LCIA en uso:", {k: v for k, v in METODOS.items()})
    if "GWP100" not in METODOS:
        print("\n[!] No se resolvio GWP100. Elige una tupla de abajo y ponla en "
              "CONFIG['METHOD_GWP100'] (y METHOD_GWP20), luego vuelve a correr:\n")
        diagnostico_metodos()
        raise RuntimeError("Fija CONFIG['METHOD_GWP100'] con una tupla de las de arriba.")
    if "GWP20" not in METODOS:
        print("  [!] GWP20 no resuelto -> se calculara solo GWP100. Para el horizonte "
              "de 20 anos, fija CONFIG['METHOD_GWP20'] (ver diagnostico_metodos()).")
    construir_foreground()
    gas, coal = intensidades_por_etapa()
    gtot = (round(sum(v[0] for v in gas.values()), 1), round(sum(v[1] for v in gas.values()), 1))
    ctot = (round(sum(v[0] for v in coal.values()), 1), round(sum(v[1] for v in coal.values()), 1))
    print(f"TOTAL (ecoinvent) gas {gtot}  coal {ctot}  gCO2e/MJ (GWP100/GWP20)")
    if save:
        os.makedirs(CONFIG["OUT_DIR"], exist_ok=True)
        path = os.path.join(CONFIG["OUT_DIR"], "lca_brightway_intensities.csv")
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["Fuel", "Stage", "GWP100_gCO2e_per_MJ", "GWP20_gCO2e_per_MJ"])
            for s, (a, b) in gas.items():
                w.writerow(["Gas (US shale-LNG)", s, a, b])
            for s, (a, b) in coal.items():
                w.writerow(["Coal (Asian)", s, a, b])
            w.writerow(["Gas (US shale-LNG)", "TOTAL", *gtot])
            w.writerow(["Coal (Asian)", "TOTAL", *ctot])
        print("  ->", path, "\n  (grafica: reutiliza src/lca.figure() o compara parametrico vs ecoinvent)")
    return gas, coal

# ---- opcional: incertidumbre Monte Carlo del total GWP100 de una etapa ----
def monte_carlo_total(fuel="gas", metodo="GWP100", n=None):
    n = n or CONFIG["N_MONTECARLO"]
    fg = bd.Database(CONFIG["FG_DB"])
    acts = [a for a in fg if a["name"].startswith(fuel)]
    tot = np.zeros(n)
    for act in acts:
        lca = bc.LCA({act: 1}, METODOS[metodo], use_distributions=True); lca.lci(); lca.lcia()
        s = np.array([lca.score for _ in zip(range(n), lca)]) * CONFIG["KG_TO_G"]
        tot[:len(s)] += s
    print(f"{fuel} {metodo}: media {tot.mean():.1f}  P5-P95 {np.percentile(tot,5):.1f}-{np.percentile(tot,95):.1f}")
    return tot

if __name__ == "__main__":
    run()
