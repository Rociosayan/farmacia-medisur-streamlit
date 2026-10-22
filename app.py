"""Public Streamlit presentation of the existing Farmacia MediSur project."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core import (
    PERMISSIONS, ROLES, SENSITIVE_ROLES, add_client, add_sale, audit_view,
    clients_view, delete_client, kpis, new_database, products_view,
    sales_by_category, sales_view, update_client,
)

st.set_page_config(page_title="Farmacia MediSur | Laboratorio de datos", page_icon="💊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {font-family:'DM Sans',sans-serif;}
[data-testid="stApp"] {background:#f4f7f9;color:#173248;}
[data-testid="stSidebar"] {background:#102b3a;border-right:1px solid #1b4553;}
[data-testid="stSidebar"] * {color:#e9f2f2;}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {color:#9fbdc4 !important;}
[data-testid="stSidebar"] .stRadio label {padding:6px 0;}
.block-container {max-width:1280px;padding-top:2rem;padding-bottom:4rem;}
h1,h2,h3 {font-family:'Outfit',sans-serif;letter-spacing:-.03em;color:#143144;}
h1 {font-size:2.35rem !important;font-weight:700 !important;}
h2 {font-size:1.65rem !important;margin-top:.2rem !important;}
.eyebrow {font-size:.7rem;letter-spacing:.18em;color:#168d86;font-weight:800;margin-bottom:.45rem;}
.intro {font-size:.98rem;line-height:1.7;color:#5f7580;max-width:830px;margin:0 0 1.7rem;}
.hero {background:linear-gradient(110deg,#13394b 0%,#185c64 100%);padding:2rem 2.2rem;border-radius:18px;margin-bottom:1.6rem;color:white;box-shadow:0 14px 32px #0b3b4416;}
.hero .eyebrow {color:#83dfd1;}.hero h1 {color:white;margin:.45rem 0 !important;}.hero p {color:#d4e8e9;line-height:1.65;margin-bottom:0;}
.brand {font-family:'Outfit',sans-serif;font-size:1.52rem;font-weight:800;letter-spacing:.05em;color:white;margin:1.2rem 0 .15rem;}.brand span {color:#65d7c4;}
.brand-sub {font-size:.65rem;letter-spacing:.16em;color:#a7c5ca;margin-bottom:2rem;}
.sidebar-foot {font-size:.75rem;line-height:1.5;color:#9ebac0;margin-top:2rem;padding-top:1rem;border-top:1px solid #315462;}
.pill {display:inline-block;border-radius:100px;background:#e0f4f0;color:#177d71;padding:.4rem .75rem;font-size:.72rem;font-weight:700;margin-bottom:.8rem;}
.note {background:#e8f4f3;border-left:4px solid #27aa99;border-radius:7px;padding:.8rem 1rem;color:#346b6c;font-size:.8rem;margin:1rem 0;}
[data-testid="stMetric"] {background:white;padding:1.2rem 1.3rem;border:1px solid #e1eaed;border-radius:12px;box-shadow:0 6px 20px #204c5810;}
[data-testid="stMetricLabel"] {font-size:.78rem;color:#708692;}
[data-testid="stMetricValue"] {font-family:'Outfit',sans-serif;color:#183c4c;font-size:1.9rem;}
[data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {border-radius:12px;}
.section-lead {color:#6a7f8a;font-size:.9rem;margin-bottom:1.4rem;}
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {background:#128b7e;border-color:#128b7e;color:white;font-weight:700;}
.stButton button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover {background:#0c746a;border-color:#0c746a;color:white;}
a {color:#148b81;}
</style>
""", unsafe_allow_html=True)

if "db" not in st.session_state:
    st.session_state.db = new_database()
conn = st.session_state.db

with st.sidebar:
    st.markdown('<div class="brand">✚ MEDI<span>SUR</span></div><div class="brand-sub">LABORATORIO DE DATOS</div>', unsafe_allow_html=True)
    page = st.radio("EXPLORAR", ("Inicio", "Clientes", "Ventas", "Catálogo de datos", "Reportes", "Calidad", "Gobierno", "KPIs y DQM"), label_visibility="collapsed")
    st.divider()
    role = st.selectbox("ROL DE DEMOSTRACIÓN", ROLES, index=0)
    st.markdown('<div class="sidebar-foot">● DEMOSTRACIÓN PÚBLICA<br>Datos inventados y temporales.<br>El rol es una simulación educativa.</div>', unsafe_allow_html=True)

if page == "Inicio":
    st.markdown('<div class="hero"><div class="eyebrow">FARMACIA MEDISUR · PROYECTO EDUCATIVO</div><h1>De los datos a las decisiones.</h1><p>Una aplicación interactiva para explorar clientes, ventas, calidad y gobierno de datos en una cadena farmacéutica ficticia.</p></div>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Versión Streamlit del proyecto original en Python, SQLite y Gradio</span>', unsafe_allow_html=True)
    metrics = kpis(conn)
    a, b, c, d = st.columns(4)
    a.metric("Clientes", int(metrics["clientes"]))
    b.metric("Ventas registradas", int(metrics["ventas"]))
    c.metric("Ingresos de demostración", f"S/ {metrics['ingresos']:,.2f}")
    d.metric("Contactos válidos", f"{metrics['contacto']:.1f}%")
    st.markdown("### ¿Qué puedes explorar?")
    st.write("Registra clientes con validaciones, crea ventas y tickets, visualiza reportes por categoría y examina cómo se aplican permisos, auditoría y reglas de calidad.")
    st.markdown('<div class="note">Esta app usa únicamente datos ficticios. Los cambios existen solo durante tu sesión y no se guardan en un servidor.</div>', unsafe_allow_html=True)

elif page == "Clientes":
    st.markdown('<div class="eyebrow">01 / GESTIÓN</div>', unsafe_allow_html=True)
    st.title("Clientes")
    st.markdown('<p class="section-lead">Consulta, registra y corrige datos con las reglas de calidad del proyecto original. Las acciones dependen del rol de demostración.</p>', unsafe_allow_html=True)
    search = st.text_input("Buscar por nombre, apellido o DNI", placeholder="Escribe para filtrar...")
    st.dataframe(clients_view(conn, role, search), width="stretch", hide_index=True)
    if "INSERT" in PERMISSIONS[role]:
        with st.expander("＋ Registrar cliente", expanded=False):
            with st.form("new_client", clear_on_submit=True):
                c1, c2 = st.columns(2)
                names = c1.text_input("Nombres")
                surnames = c2.text_input("Apellidos")
                c3, c4 = st.columns(2)
                dni = c3.text_input("DNI · 8 dígitos", max_chars=8)
                phone = c4.text_input("Teléfono · 9 dígitos", max_chars=9)
                c5, c6 = st.columns(2)
                email = c5.text_input("Correo electrónico")
                district = c6.text_input("Distrito", value="Lima")
                if st.form_submit_button("Guardar cliente", type="primary"):
                    try:
                        new_id = add_client(conn, role, names, surnames, dni, email, phone, district)
                        st.success(f"Cliente de demostración C{new_id:05d} registrado.")
                        st.rerun()
                    except (ValueError, PermissionError) as exc:
                        st.error(str(exc))
    if "UPDATE" in PERMISSIONS[role]:
        with st.expander("✎ Actualizar cliente", expanded=False):
            ids = pd.read_sql_query("SELECT id_cliente,nombres,apellidos FROM clientes ORDER BY id_cliente", conn)
            with st.form("edit_client"):
                client_id = st.selectbox("Cliente", ids.id_cliente.tolist(), format_func=lambda x: f"{x} · {ids.loc[ids.id_cliente == x, 'nombres'].iloc[0]} {ids.loc[ids.id_cliente == x, 'apellidos'].iloc[0]}")
                field = st.selectbox("Campo", ("correo", "telefono", "apellidos", "distrito"))
                value = st.text_input("Nuevo valor")
                if st.form_submit_button("Guardar cambio", type="primary"):
                    try:
                        update_client(conn, role, int(client_id), field, value)
                        st.success("Cliente actualizado.")
                        st.rerun()
                    except (ValueError, PermissionError) as exc:
                        st.error(str(exc))
    if "DELETE" in PERMISSIONS[role]:
        with st.expander("Eliminar cliente", expanded=False):
            ids = pd.read_sql_query("SELECT id_cliente FROM clientes ORDER BY id_cliente", conn).id_cliente.tolist()
            with st.form("delete_client"):
                client_id = st.selectbox("ID de cliente", ids)
                confirmed = st.checkbox("Confirmo que deseo borrar este registro de la demo")
                if st.form_submit_button("Eliminar"):
                    if not confirmed:
                        st.warning("Confirma la eliminación.")
                    else:
                        try:
                            delete_client(conn, role, int(client_id))
                            st.success("Cliente eliminado de esta sesión.")
                            st.rerun()
                        except (ValueError, PermissionError) as exc:
                            st.error(str(exc))
    data = clients_view(conn, role)
    st.download_button("Descargar clientes visibles (CSV)", data.to_csv(index=False).encode("utf-8-sig"), "medisur_clientes_demo.csv", "text/csv")

elif page == "Ventas":
    st.markdown('<div class="eyebrow">02 / OPERACIONES</div>', unsafe_allow_html=True)
    st.title("Ventas")
    st.markdown('<p class="section-lead">Una venta crea operación, detalle y pago en una sola transacción.</p>', unsafe_allow_html=True)
    st.subheader("Catálogo de productos")
    st.dataframe(products_view(conn), width="stretch", hide_index=True)
    if "INSERT" in PERMISSIONS[role]:
        with st.form("new_sale"):
            clients = pd.read_sql_query("SELECT id_cliente,nombres,apellidos FROM clientes ORDER BY id_cliente", conn)
            products = products_view(conn)
            a, b, c = st.columns(3)
            client_id = a.selectbox("Cliente", clients.id_cliente.tolist(), format_func=lambda x: f"{x} · {clients.loc[clients.id_cliente == x, 'nombres'].iloc[0]}")
            product_id = b.selectbox("Producto", products.id_producto.tolist(), format_func=lambda x: products.loc[products.id_producto == x, "nombre_producto"].iloc[0])
            quantity = c.number_input("Cantidad", min_value=1, step=1, value=1)
            method = st.selectbox("Medio de pago", ("Efectivo", "Tarjeta", "Yape/Plin"))
            if st.form_submit_button("Registrar venta y emitir ticket", type="primary"):
                try:
                    code, total = add_sale(conn, role, int(client_id), int(product_id), int(quantity), method)
                    st.session_state.last_ticket = (code, total)
                    st.rerun()
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))
    if "last_ticket" in st.session_state:
        code, total = st.session_state.last_ticket
        st.success(f"Ticket {code} · Total S/ {total:,.2f} · Venta guardada en esta sesión.")
    st.subheader("Historial de ventas")
    history = sales_view(conn)
    st.dataframe(history, width="stretch", hide_index=True) if not history.empty else st.info("Aún no hay ventas en esta sesión.")

elif page == "Catálogo de datos":
    st.markdown('<div class="eyebrow">03 / METADATOS</div>', unsafe_allow_html=True)
    st.title("Catálogo de datos")
    st.markdown('<p class="section-lead">Qué significa cada dato y quién puede verlo.</p>', unsafe_allow_html=True)
    catalog = pd.DataFrame([
        ("clientes", "num_documento", "Texto", "Sensible", "Identificador del cliente"),
        ("clientes", "nombres", "Texto", "Confidencial", "Nombres del cliente"),
        ("clientes", "correo", "Texto", "Confidencial", "Contacto electrónico"),
        ("operaciones", "fecha_operacion", "Fecha ISO", "Interno", "Fecha de la venta"),
        ("operaciones", "monto_total", "Decimal", "Interno", "Importe de la operación"),
        ("productos_servicios", "precio_base", "Decimal", "Público", "Precio de catálogo"),
    ], columns=["Tabla", "Columna", "Tipo", "Sensibilidad", "Descripción"])
    if role not in SENSITIVE_ROLES:
        catalog = catalog[catalog.Sensibilidad != "Sensible"]
    st.dataframe(catalog, width="stretch", hide_index=True)
    st.caption("Diccionario ilustrativo adaptado del caso original. No contiene registros personales reales.")

elif page == "Reportes":
    st.markdown('<div class="eyebrow">04 / ANÁLISIS</div>', unsafe_allow_html=True)
    st.title("Reportes")
    st.markdown('<p class="section-lead">Resumen agregado de ventas por categoría, sin mostrar información personal.</p>', unsafe_allow_html=True)
    report = sales_by_category(conn)
    if report.empty:
        st.info("Registra una venta para visualizar el reporte.")
    else:
        st.bar_chart(report.set_index("categoria"), color="#22a99a", horizontal=True)
        st.dataframe(report, width="stretch", hide_index=True)
        st.metric("Ventas totales", f"S/ {report.ventas.sum():,.2f}")

elif page == "Calidad":
    st.markdown('<div class="eyebrow">05 / CALIDAD DE DATOS</div>', unsafe_allow_html=True)
    st.title("Reglas de calidad")
    st.markdown('<p class="section-lead">Validaciones que impiden registrar datos incompletos o inconsistentes.</p>', unsafe_allow_html=True)
    quality = pd.DataFrame([
        ("Exactitud", "Nombres y apellidos contienen solo letras", "Activa"),
        ("Exactitud", "DNI de exactamente ocho dígitos", "Activa"),
        ("Unicidad", "DNI sin duplicados", "Activa"),
        ("Exactitud", "Correo y teléfono con formato válido", "Activa"),
        ("Consistencia", "Cantidad de venta mayor a cero", "Activa"),
        ("Integridad", "Venta vinculada a cliente y producto existentes", "Activa"),
    ], columns=["Dimensión", "Regla", "Estado"])
    st.dataframe(quality, width="stretch", hide_index=True)
    a, b = st.columns(2)
    a.metric("Reglas activas", len(quality))
    b.metric("Contacto válido", f"{kpis(conn)['contacto']:.1f}%")

elif page == "Gobierno":
    st.markdown('<div class="eyebrow">06 / GOBIERNO</div>', unsafe_allow_html=True)
    st.title("Permisos y bitácora")
    matrix = pd.DataFrame([{"Rol": r, "Consultar": "Sí", "Agregar": "Sí" if "INSERT" in p else "No", "Editar": "Sí" if "UPDATE" in p else "No", "Eliminar": "Sí" if "DELETE" in p else "No", "Datos sensibles": "Sí" if r in SENSITIVE_ROLES else "No"} for r, p in PERMISSIONS.items()])
    st.dataframe(matrix, width="stretch", hide_index=True)
    if role in SENSITIVE_ROLES:
        st.subheader("Bitácora de esta sesión")
        records = audit_view(conn)
        st.dataframe(records, width="stretch", hide_index=True) if not records.empty else st.info("Sin acciones registradas todavía.")
    else:
        st.info("La bitácora está disponible para Auditor y DataOwner en esta demostración.")

elif page == "KPIs y DQM":
    st.markdown('<div class="eyebrow">07 / MEJORA CONTINUA</div>', unsafe_allow_html=True)
    st.title("KPIs y plan DQM")
    values = kpis(conn)
    a, b, c = st.columns(3)
    a.metric("Contacto completo", f"{values['contacto']:.1f}%", f"Meta 98%")
    b.metric("Ventas", int(values["ventas"]))
    c.metric("Acciones auditadas", int(values["auditoria"]))
    st.subheader("Cinco pilares")
    pillars = pd.DataFrame([
        ("Gobierno", "Roles y responsables"), ("Metadatos", "Definiciones y linaje"),
        ("Calidad", "Reglas y medición"), ("Arquitectura", "Almacenamiento y escala"),
        ("Cumplimiento", "Acceso y trazabilidad"),
    ], columns=["Pilar", "Aplicación en el caso"])
    st.dataframe(pillars, width="stretch", hide_index=True)
    st.subheader("Acción sugerida")
    if values["contacto"] < 98:
        st.warning("La completitud de contacto no alcanza la meta. Revisar correos faltantes o inválidos antes de generar campañas.")
    else:
        st.success("La completitud de contacto cumple la meta en esta demo.")

st.divider()
st.caption("Farmacia MediSur · Proyecto educativo de Pilar Rocío Sayán · Interfaz Streamlit con datos ficticios de sesión")
