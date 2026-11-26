# ============================================================
# ¿CUÁNTAS HORAS DE TRABAJO CUESTA TU GUSTO?  ·  Aplicación Streamlit
# Parcial II · Programación para Economistas · UADE
# ============================================================
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import seaborn as sns
import streamlit as st

# La configuración de la página tiene que ser el PRIMER comando de Streamlit
st.set_page_config(page_title="¿Cuántas horas de trabajo cuesta tu gusto?", page_icon="⏱️", layout="wide")
sns.set_theme(style="white", font_scale=0.95)

# ------------------------------------------------------------
# 1. FÓRMULAS ECONÓMICAS (el "motor" de cálculo)
# ------------------------------------------------------------
SEMANAS_POR_MES = 52 / 12   # ≈ 4,33 semanas por mes


def horas_mensuales(horas_dia, dias_semana):
    """Horas trabajadas en un mes promedio."""
    return horas_dia * dias_semana * SEMANAS_POR_MES


def sueldo_por_hora_desde_mensual(sueldo_mensual, horas_dia=8, dias_semana=5):
    """Convierte un sueldo mensual en sueldo por hora."""
    return sueldo_mensual / horas_mensuales(horas_dia, dias_semana)


def horas_necesarias(precio, sueldo_hora):
    """FÓRMULA PRINCIPAL: horas de trabajo = precio / sueldo por hora."""
    if sueldo_hora <= 0:
        raise ValueError("El sueldo por hora debe ser mayor a 0.")
    return precio / sueldo_hora


def dias_necesarios(horas, horas_dia):
    """Días de trabajo (jornadas) que equivalen a esas horas."""
    return horas / horas_dia


def porcentaje_jornada(horas, horas_dia):
    """Qué porcentaje de una jornada laboral representan esas horas."""
    return horas / horas_dia * 100


def porcentaje_ingreso_mensual(precio, sueldo_hora, horas_dia, dias_semana):
    """Qué porcentaje del ingreso mensual representa el precio."""
    ingreso_mensual = sueldo_hora * horas_mensuales(horas_dia, dias_semana)
    return precio / ingreso_mensual * 100


def simular_ahorro(precio, ahorro_mensual, tasa_mensual=0.0, ahorro_inicial=0.0, max_meses=600):
    """Simula el ahorro mes a mes. Devuelve (meses, historia); meses = None si no se llega."""
    saldo = ahorro_inicial
    historia = [saldo]
    if saldo >= precio:
        return 0, historia
    if ahorro_mensual <= 0 and tasa_mensual <= 0:
        return None, historia
    for mes in range(1, max_meses + 1):
        saldo = saldo * (1 + tasa_mensual) + ahorro_mensual
        historia.append(saldo)
        if saldo >= precio:
            return mes, historia
    return None, historia


def formatear_numero(x, decimales=1):
    s = f"{x:,.{decimales}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def formatear_pesos(x):
    return "$" + formatear_numero(x, 0)


def formatear_horas(horas):
    """30 -> '30 h 0 min'; 1.6 -> '1 h 36 min'; 0.5 -> '30 min'."""
    minutos_totales = int(round(horas * 60))
    h, m = divmod(minutos_totales, 60)
    if h == 0:
        return f"{m} min"
    return f"{h} h {m} min"


# ------------------------------------------------------------
# 2. CATÁLOGO DE PRODUCTOS (datos simulados y editables)
# ------------------------------------------------------------
CATALOGO_BASE = [
    ("Tecnología", "📱", "Celular gama media", 600000),
    ("Tecnología", "🎧", "Auriculares inalámbricos", 120000),
    ("Tecnología", "💻", "Notebook", 1400000),
    ("Tecnología", "⌚", "Smartwatch", 250000),
    ("Indumentaria", "👟", "Zapatillas", 150000),
    ("Indumentaria", "👖", "Jeans", 70000),
    ("Indumentaria", "👜", "Cartera", 110000),
    ("Indumentaria", "🧥", "Campera", 180000),
    ("Gastronomía", "☕", "Café con medialunas", 8000),
    ("Gastronomía", "🍽️", "Cena para dos", 90000),
    ("Gastronomía", "🍕", "Pizza con amigos", 35000),
    ("Gastronomía", "🍔", "Delivery de hamburguesa", 18000),
    ("Entretenimiento", "🎬", "Entrada de cine", 9000),
    ("Entretenimiento", "🎤", "Entrada a un recital", 120000),
    ("Entretenimiento", "🏖️", "Escapada de fin de semana", 450000),
    ("Entretenimiento", "✈️", "Viaje internacional", 2500000),
    ("Gustos personales", "🌸", "Perfume", 130000),
    ("Gustos personales", "💄", "Set de maquillaje", 60000),
    ("Gustos personales", "🕶️", "Anteojos de sol", 85000),
    ("Gustos personales", "💇", "Corte y color", 45000),
]
ICONO_CATEGORIA = {"Tecnología": "💻", "Indumentaria": "👕", "Gastronomía": "🍴",
                   "Entretenimiento": "🎟️", "Gustos personales": "✨"}
CATEGORIAS = list(ICONO_CATEGORIA.keys())

CATALOGO_ORIGINAL = pd.DataFrame(CATALOGO_BASE, columns=["categoria", "icono", "producto", "precio"])
CATALOGO_ORIGINAL["fuente"] = "Dato simulado (ref. 17/11/2026)"

# En Streamlit el catálogo vive en "session_state": así los cambios de precios
# se conservan mientras la persona usa la app.
if "catalogo" not in st.session_state:
    st.session_state["catalogo"] = CATALOGO_ORIGINAL.copy()
catalogo = st.session_state["catalogo"]


# ------------------------------------------------------------
# 3. CÁLCULO AUTOMÁTICO, ANÁLISIS, COMPARADOR Y AHORRO
# ------------------------------------------------------------
def calcular_tabla(df, sueldo_hora, horas_dia=8, dias_semana=5):
    """Agrega al catálogo los indicadores de tiempo de trabajo."""
    if sueldo_hora <= 0:
        raise ValueError("El sueldo por hora debe ser mayor a 0.")
    t = df.copy()
    t["horas"] = t["precio"] / sueldo_hora
    t["tiempo"] = t["horas"].apply(formatear_horas)
    t["dias"] = t["horas"] / horas_dia
    t["pct_jornada"] = t["horas"] / horas_dia * 100
    ingreso_mensual = sueldo_hora * horas_mensuales(horas_dia, dias_semana)
    t["pct_ingreso"] = t["precio"] / ingreso_mensual * 100
    return t


def interpretar(producto, precio, sueldo_hora, horas_dia=8, dias_semana=5):
    horas = horas_necesarias(precio, sueldo_hora)
    pct_jor = porcentaje_jornada(horas, horas_dia)
    pct_mes = porcentaje_ingreso_mensual(precio, sueldo_hora, horas_dia, dias_semana)
    if horas < horas_dia:
        parte = f"{formatear_numero(pct_jor, 0)}% de una jornada de {horas_dia} h"
    else:
        parte = f"{formatear_numero(dias_necesarios(horas, horas_dia), 1)} jornadas completas de {horas_dia} h"
    if pct_mes < 5:
        lectura = "Es una compra de bajo impacto en tu presupuesto mensual."
    elif pct_mes < 25:
        lectura = "Es una compra de impacto moderado en tu presupuesto mensual."
    elif pct_mes <= 100:
        lectura = "Es una compra de alto impacto: conviene planificarla o ahorrar para ella."
    else:
        lectura = "Supera lo que ganás en un mes: requiere ahorrar durante varios meses."
    return (f"Para comprar {producto} ({formatear_pesos(precio)}) necesitás trabajar "
            f"{formatear_horas(horas)}, es decir {parte}. "
            f"Representa el {formatear_numero(pct_mes, 1)}% de tu ingreso mensual. {lectura}")


def comparar(df, productos, sueldo_hora, horas_dia=8, dias_semana=5):
    t = calcular_tabla(df[df["producto"].isin(productos)], sueldo_hora, horas_dia, dias_semana)
    return t.sort_values("horas", ascending=False).reset_index(drop=True)


def texto_comparacion(t):
    if len(t) < 2:
        return "Elegí al menos dos productos para comparar."
    mayor, menor = t.iloc[0], t.iloc[-1]
    veces = mayor["horas"] / menor["horas"]
    return (f"{mayor['producto']} requiere {formatear_numero(veces, 1)} veces más horas de trabajo "
            f"que {menor['producto']} ({mayor['tiempo']} contra {menor['tiempo']}).")


def simulador_ahorro(precio, sueldo_hora, ahorro_mensual, horas_dia=8, dias_semana=5,
                     tasa_mensual_pct=0.0, ahorro_inicial=0.0):
    meses, historia = simular_ahorro(precio, ahorro_mensual, tasa_mensual_pct / 100, ahorro_inicial)
    ingreso_mensual = sueldo_hora * horas_mensuales(horas_dia, dias_semana)
    return {"meses": meses, "historia": historia,
            "horas_ahorro_mes": ahorro_mensual / sueldo_hora,
            "pct_ingreso_ahorrado": ahorro_mensual / ingreso_mensual * 100,
            "horas_precio": horas_necesarias(precio, sueldo_hora)}


def texto_ahorro(producto, precio, res):
    if res["meses"] is None:
        return (f"Con ese ritmo de ahorro no se llega a {formatear_pesos(precio)} en 50 años. "
                f"Probá aumentando el ahorro mensual.")
    if res["meses"] == 0:
        return f"Ya tenés lo necesario para comprar {producto}."
    anios, meses = divmod(res["meses"], 12)
    plazo = f"{res['meses']} meses"
    if anios > 0:
        plazo += f" ({anios} año{'s' if anios > 1 else ''}" + (f" y {meses} meses)" if meses else ")")
    return (f"Ahorrando {formatear_numero(res['pct_ingreso_ahorrado'], 1)}% de tu ingreso "
            f"({formatear_numero(res['horas_ahorro_mes'], 1)} h de trabajo por mes) "
            f"juntás {formatear_pesos(precio)} para {producto} en {plazo}.")


# ------------------------------------------------------------
# 4. VISUALIZACIONES
# ------------------------------------------------------------
PALETA = {"Tecnología": "#2563EB", "Indumentaria": "#DB2777", "Gastronomía": "#F59E0B",
          "Entretenimiento": "#7C3AED", "Gustos personales": "#10B981"}
TINTA, ACENTO, SUAVE, BORDE = "#111827", "#FF5A36", "#6B7280", "#E5E7EB"


def _color_categoria(cat):
    return PALETA.get(cat, "#6B7280")


def grafico_horas_por_producto(t):
    d = t.sort_values("horas")
    fig, ax = plt.subplots(figsize=(9, max(3.2, 0.34 * len(d) + 1.2)))
    ax.barh(d["producto"], d["horas"], color=[_color_categoria(c) for c in d["categoria"]])
    ax.bar_label(ax.containers[0], labels=list(d["tiempo"]), padding=3, fontsize=8)
    ax.set_xlabel("Horas de trabajo")
    ax.set_title("Horas de trabajo necesarias por producto", loc="left", fontweight="bold")
    cats = [c for c in d["categoria"].unique()]
    ax.legend(handles=[Patch(color=_color_categoria(c), label=c) for c in cats],
              loc="lower right", frameon=False, fontsize=8)
    ax.margins(x=0.15)
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def grafico_horas_interactivo(t):
    """Versión interactiva (con hover) del gráfico 1. Devuelve None si algo falla."""
    try:
        import plotly.express as px
        d = t.sort_values("horas")
        fig = px.bar(d, x="horas", y="producto", color="categoria", orientation="h",
                     color_discrete_map=PALETA, text="tiempo",
                     hover_data={"tiempo": True, "horas": ":.1f", "producto": False, "categoria": False})
        fig.update_layout(template="plotly_white", height=max(320, 28 * len(d) + 120),
                          margin=dict(l=10, r=10, t=40, b=10), legend_title_text="",
                          yaxis_title=None, xaxis_title="Horas de trabajo",
                          title="Horas de trabajo necesarias (pasá el mouse por las barras)")
        return fig
    except Exception:
        return None


def grafico_esfuerzo_por_categoria(t):
    g = t.groupby("categoria", as_index=False)["horas"].mean().sort_values("horas", ascending=False)
    orden = list(g["categoria"])
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.bar(range(len(g)), g["horas"], color=[_color_categoria(c) for c in orden], width=0.6)
    sns.stripplot(data=t, x="categoria", y="horas", order=orden, color="black", alpha=0.45, size=4, ax=ax)
    ax.bar_label(ax.containers[0], labels=[formatear_horas(h) for h in g["horas"]], padding=3, fontsize=8)
    ax.set_xlabel("")
    ax.set_ylabel("Horas de trabajo (promedio)")
    ax.set_title("¿Qué categorías exigen más esfuerzo laboral?", loc="left", fontweight="bold")
    ax.margins(y=0.12)
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def grafico_sueldo_vs_capacidad(df, productos, sueldo_hora, horas_dia=8, dias_semana=5):
    sueldos = np.linspace(1000, max(20000, sueldo_hora * 2), 120)
    hm = horas_mensuales(horas_dia, dias_semana)
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    for p in productos:
        precio = df.loc[df["producto"] == p, "precio"].iloc[0]
        ax.plot(sueldos, sueldos * hm / precio, linewidth=2, label=p)
    ax.set_yscale("log")
    ax.axhline(1, color="gray", linestyle="--", linewidth=1)
    ax.text(sueldos[0], 1, " 1 unidad por mes", va="bottom", ha="left", color="gray", fontsize=8)
    ax.axvline(sueldo_hora, color=ACENTO, linestyle=":", linewidth=1.5)
    ax.text(sueldo_hora, ax.get_ylim()[0], " tu sueldo", color=ACENTO, fontsize=8, va="bottom")
    ax.set_xlabel("Sueldo por hora ($)")
    ax.set_ylabel("Unidades que se compran con un mes de trabajo")
    ax.set_title("Sueldo por hora y capacidad de compra", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8)
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def grafico_niveles_de_ingreso(df, producto, sueldo_hora, multiplos=(0.5, 1, 1.5, 2)):
    precio = df.loc[df["producto"] == producto, "precio"].iloc[0]
    sueldos = np.linspace(sueldo_hora * 0.3, sueldo_hora * 2.5, 150)
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ax.plot(sueldos, precio / sueldos, color=TINTA, linewidth=2)
    for m in multiplos:
        w = sueldo_hora * m
        h = horas_necesarias(precio, w)
        ax.scatter([w], [h], color=ACENTO, zorder=3)
        ax.annotate(f"{formatear_pesos(w)}/h\n{formatear_horas(h)}", (w, h),
                    textcoords="offset points", xytext=(8, 8), fontsize=8)
    ax.set_xlabel("Sueldo por hora ($)")
    ax.set_ylabel("Horas de trabajo necesarias")
    ax.set_title(f"{producto} ({formatear_pesos(precio)}): tiempo de trabajo según ingreso",
                 loc="left", fontweight="bold")
    ax.margins(x=0.12, y=0.15)
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def grafico_ahorro(historia, precio):
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.plot(range(len(historia)), historia, color=TINTA, linewidth=2, label="Ahorro acumulado")
    ax.axhline(precio, color=ACENTO, linestyle="--", label=f"Precio: {formatear_pesos(precio)}")
    ax.set_xlabel("Meses")
    ax.set_ylabel("Ahorro acumulado ($)")
    ax.set_title("Camino hacia la meta de ahorro", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def mostrar_figura(fig):
    """Muestra un gráfico de matplotlib en Streamlit y libera la memoria."""
    st.pyplot(fig)
    plt.close(fig)


def mostrar_horas(t, clave):
    """Gráfico 1: interactivo (plotly) si se puede; si no, el de matplotlib."""
    fig = grafico_horas_interactivo(t)
    if fig is not None:
        try:
            st.plotly_chart(fig, key=clave)
            return
        except Exception:
            pass
    mostrar_figura(grafico_horas_por_producto(t))


# ------------------------------------------------------------
# 5. DISEÑO VISUAL (HTML con estilos en línea)
# ------------------------------------------------------------
FUENTE = "font-family:Inter,'Segoe UI',Arial,sans-serif;"


def html_encabezado():
    return (
        f'<div style="{FUENTE}padding:24px 28px;border-radius:16px;background:{TINTA};color:#fff;margin-bottom:12px;">'
        f'<div style="letter-spacing:3px;font-size:12px;color:{ACENTO};font-weight:700;">CALCULADORA DE COSTO EN TIEMPO</div>'
        f'<div style="font-size:30px;font-weight:800;line-height:1.15;margin-top:6px;">¿CUÁNTAS HORAS DE TRABAJO CUESTA TU GUSTO?</div>'
        f'<div style="font-size:14px;color:#D1D5DB;margin-top:8px;">Convertí el precio de lo que querés comprar en tiempo de tu vida laboral.</div>'
        f'</div>')


def _metrica(titulo, valor):
    return (f'<div style="{FUENTE}flex:1;min-width:140px;background:#fff;color:{TINTA};border:1px solid {BORDE};'
            f'border-radius:12px;padding:12px 14px;">'
            f'<div style="font-size:12px;color:{SUAVE};">{titulo}</div>'
            f'<div style="font-size:20px;font-weight:700;">{valor}</div></div>')


def html_resultado(fila, horas_dia):
    dias_txt = formatear_numero(fila["dias"], 1) + " días"
    jornada_txt = formatear_numero(fila["pct_jornada"], 0) + "%"
    ingreso_txt = formatear_numero(fila["pct_ingreso"], 1) + "%"
    return (
        f'<div style="{FUENTE}margin:6px 0;">'
        f'<div style="background:{ACENTO};color:#fff;border-radius:16px;padding:22px 24px;">'
        f'<div style="font-size:14px;opacity:.95;">{fila["icono"]} {fila["producto"]} · {formatear_pesos(fila["precio"])}</div>'
        f'<div style="font-size:52px;font-weight:800;line-height:1.1;margin:6px 0;">{fila["tiempo"]}</div>'
        f'<div style="font-size:14px;">de trabajo para comprarlo</div></div>'
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;">'
        f'{_metrica("Días de trabajo (jornadas de " + str(horas_dia) + " h)", dias_txt)}'
        f'{_metrica("% de una jornada", jornada_txt)}'
        f'{_metrica("% del ingreso mensual", ingreso_txt)}'
        f'</div></div>')


def html_texto(texto):
    return (f'<div style="{FUENTE}margin-top:10px;padding:14px 16px;border-left:4px solid {ACENTO};'
            f'background:#F9FAFB;color:{TINTA};font-size:15px;border-radius:0 10px 10px 0;">{texto}</div>')


def _tarjeta(r):
    return (f'<div style="{FUENTE}width:175px;background:#fff;color:{TINTA};border:1px solid {BORDE};'
            f'border-radius:14px;padding:14px;">'
            f'<div style="font-size:28px;">{r.icono}</div>'
            f'<div style="font-size:14px;font-weight:600;margin-top:4px;">{r.producto}</div>'
            f'<div style="font-size:12px;color:{SUAVE};">{formatear_pesos(r.precio)}</div>'
            f'<div style="font-size:18px;font-weight:800;color:{ACENTO};margin-top:6px;">{r.tiempo}</div></div>')


def html_catalogo(t):
    bloques = []
    for cat, g in t.groupby("categoria", sort=False):
        tarjetas = "".join(_tarjeta(r) for r in g.itertuples())
        bloques.append(
            f'<div style="{FUENTE}margin:14px 0 6px;font-size:13px;font-weight:700;letter-spacing:1px;'
            f'color:{_color_categoria(cat)};text-transform:uppercase;">{cat}</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:10px;">{tarjetas}</div>')
    return "".join(bloques)


# ------------------------------------------------------------
# 6. INTERFAZ DE LA APLICACIÓN
# ------------------------------------------------------------
def indice_de(nombres, preferido):
    return nombres.index(preferido) if preferido in nombres else 0


st.markdown(html_encabezado(), unsafe_allow_html=True)

# ---- Barra lateral: ingreso del sueldo ----
with st.sidebar:
    st.header("1) Ingresá tu sueldo")
    modo = st.radio("¿Cómo querés ingresarlo?", ["Por hora", "Mensual"], horizontal=True)
    hd = st.slider("Horas por día", 1, 12, 8)
    ds = st.slider("Días por semana", 1, 7, 5)
    if modo == "Por hora":
        sueldo_hora = st.number_input("Sueldo por hora ($)", min_value=0.0, value=5000.0, step=500.0)
    else:
        sueldo_mensual = st.number_input("Sueldo mensual ($)", min_value=0.0, value=866667.0, step=10000.0)
        sueldo_hora = sueldo_por_hora_desde_mensual(sueldo_mensual, hd, ds)
    st.caption("Los precios del catálogo son datos simulados y se pueden modificar en la pestaña Precios.")

if sueldo_hora <= 0:
    st.warning("Ingresá un sueldo mayor a 0 para ver los resultados.")
    st.stop()

st.markdown(html_texto(
    f"Tu sueldo equivale a <b>{formatear_pesos(sueldo_hora)} por hora</b> · "
    f"<b>{formatear_pesos(sueldo_hora * horas_mensuales(hd, ds))} por mes</b> · "
    f"{formatear_numero(horas_mensuales(hd, ds), 0)} horas de trabajo al mes."), unsafe_allow_html=True)

tabla = calcular_tabla(catalogo, sueldo_hora, hd, ds)
nombres = list(catalogo["producto"])

tab_cat, tab_calc, tab_comp, tab_aho, tab_graf, tab_prec = st.tabs(
    ["🛍️ Catálogo", "⏱️ Calculadora", "⚖️ Comparador", "🐷 Ahorro", "📊 Gráficos", "✏️ Precios"])

# ---- Catálogo ----
with tab_cat:
    cat = st.selectbox("Categoría", ["Todas"] + CATEGORIAS)
    t_cat = tabla if cat == "Todas" else tabla[tabla["categoria"] == cat]
    st.markdown(html_catalogo(t_cat), unsafe_allow_html=True)
    csv = tabla[["categoria", "producto", "precio", "horas", "tiempo", "dias", "pct_jornada", "pct_ingreso", "fuente"]]
    st.download_button("Descargar tabla completa (CSV)", csv.to_csv(index=False).encode("utf-8"),
                       "horas_de_trabajo.csv", "text/csv")

# ---- Calculadora ----
with tab_calc:
    prod = st.selectbox("Producto", nombres, index=indice_de(nombres, "Zapatillas"), key="calc_prod")
    fila = tabla[tabla["producto"] == prod].iloc[0]
    st.markdown(html_resultado(fila, hd), unsafe_allow_html=True)
    st.markdown(html_texto(interpretar(prod, fila["precio"], sueldo_hora, hd, ds)), unsafe_allow_html=True)

# ---- Comparador ----
with tab_comp:
    pref = [p for p in ["Zapatillas", "Cena para dos", "Celular gama media"] if p in nombres]
    elegidos = st.multiselect("Elegí dos o más productos para comparar", nombres, default=pref, key="comp_prod")
    if len(elegidos) < 2:
        st.warning("Elegí al menos dos productos.")
    else:
        comp = comparar(catalogo, elegidos, sueldo_hora, hd, ds)
        st.markdown(html_texto(texto_comparacion(comp)), unsafe_allow_html=True)
        vista = comp[["producto", "precio", "tiempo", "dias", "pct_ingreso"]].copy()
        vista["precio"] = vista["precio"].map(formatear_pesos)
        vista["dias"] = vista["dias"].map(lambda x: formatear_numero(x, 1))
        vista["pct_ingreso"] = vista["pct_ingreso"].map(lambda x: formatear_numero(x, 1) + "%")
        vista.columns = ["Producto", "Precio", "Tiempo de trabajo", "Días", "% ingreso mensual"]
        st.dataframe(vista, hide_index=True)
        mostrar_horas(comp, "plotly_comparador")

# ---- Ahorro ----
with tab_aho:
    p_aho = st.selectbox("Quiero comprar", nombres, index=indice_de(nombres, "Celular gama media"), key="aho_prod")
    c1, c2, c3 = st.columns(3)
    ahorro = c1.number_input("Ahorro por mes ($)", min_value=0.0, value=100000.0, step=10000.0)
    inicial = c2.number_input("Ahorro inicial ($)", min_value=0.0, value=0.0, step=10000.0)
    tasa = c3.number_input("Tasa mensual (%)", min_value=0.0, value=0.0, step=0.5)
    precio_aho = float(catalogo.loc[catalogo["producto"] == p_aho, "precio"].iloc[0])
    res = simulador_ahorro(precio_aho, sueldo_hora, ahorro, hd, ds, tasa, inicial)
    st.markdown(html_texto(texto_ahorro(p_aho, precio_aho, res)), unsafe_allow_html=True)
    mostrar_figura(grafico_ahorro(res["historia"], precio_aho))

# ---- Gráficos ----
with tab_graf:
    opcion = st.selectbox("Gráfico", ["1. Horas por producto", "2. Esfuerzo por categoría",
                                      "3. Sueldo y capacidad de compra", "4. Un producto según nivel de ingreso"])
    if opcion.startswith("1"):
        mostrar_horas(tabla, "plotly_graficos")
    elif opcion.startswith("2"):
        mostrar_figura(grafico_esfuerzo_por_categoria(tabla))
    elif opcion.startswith("3"):
        pref3 = [p for p in ["Café con medialunas", "Zapatillas", "Celular gama media", "Viaje internacional"] if p in nombres]
        sel3 = st.multiselect("Productos a graficar", nombres, default=pref3, key="graf3_prod")
        if sel3:
            mostrar_figura(grafico_sueldo_vs_capacidad(catalogo, sel3, sueldo_hora, hd, ds))
        else:
            st.warning("Elegí al menos un producto.")
    else:
        p4 = st.selectbox("Producto", nombres, index=indice_de(nombres, "Zapatillas"), key="graf4_prod")
        mostrar_figura(grafico_niveles_de_ingreso(catalogo, p4, sueldo_hora))

# ---- Precios: modificar y agregar productos ----
with tab_prec:
    mensaje = st.session_state.pop("mensaje", None)
    if mensaje:
        st.success(mensaje)
    izq, der = st.columns(2)
    with izq:
        st.subheader("Modificar un precio")
        p_edit = st.selectbox("Producto", nombres, key="edit_prod")
        actual = float(catalogo.loc[catalogo["producto"] == p_edit, "precio"].iloc[0])
        nuevo = st.number_input("Nuevo precio ($)", min_value=0.0, value=actual, step=1000.0, key=f"precio_{p_edit}")
        if st.button("Actualizar precio"):
            if nuevo <= 0:
                st.error("El precio debe ser mayor a 0.")
            else:
                catalogo.loc[catalogo["producto"] == p_edit, "precio"] = nuevo
                catalogo.loc[catalogo["producto"] == p_edit, "fuente"] = "Modificado por el usuario"
                st.session_state["mensaje"] = f"Precio de {p_edit} actualizado a {formatear_pesos(nuevo)}."
                st.rerun()
        if st.button("Restaurar precios originales"):
            st.session_state["catalogo"] = CATALOGO_ORIGINAL.copy()
            st.session_state["mensaje"] = "Se restauraron los precios y productos originales."
            st.rerun()
    with der:
        st.subheader("Agregar un producto nuevo")
        with st.form("form_nuevo"):
            n_nombre = st.text_input("Nombre", placeholder="Ej: Bicicleta")
            n_cat = st.selectbox("Categoría", CATEGORIAS)
            n_precio = st.number_input("Precio ($)", min_value=0.0, value=0.0, step=1000.0)
            enviado = st.form_submit_button("Agregar producto")
        if enviado:
            n_nombre = n_nombre.strip()
            if not n_nombre or n_precio <= 0:
                st.error("Completá el nombre y un precio mayor a 0.")
            elif n_nombre in nombres:
                st.error("Ya existe un producto con ese nombre.")
            else:
                fila_nueva = pd.DataFrame([{"categoria": n_cat, "icono": ICONO_CATEGORIA[n_cat], "producto": n_nombre,
                                            "precio": n_precio, "fuente": "Cargado por el usuario"}])
                st.session_state["catalogo"] = pd.concat([catalogo, fila_nueva], ignore_index=True)
                st.session_state["mensaje"] = f"Se agregó {n_nombre} ({formatear_pesos(n_precio)}) a {n_cat}."
                st.rerun()

st.caption("Proyecto Parcial II · Programación para Economistas · UADE · Precios simulados con fecha de referencia 17/11/2026.")
