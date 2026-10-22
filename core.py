"""Domain logic for the public, session-local MediSur demonstration."""

from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime

import pandas as pd

ROLES = ("Vendedor", "Cajero", "Supervisor", "Auditor", "DataOwner")
PERMISSIONS = {
    "Vendedor": {"SELECT", "INSERT"},
    "Cajero": {"SELECT", "UPDATE"},
    "Supervisor": {"SELECT", "DELETE"},
    "Auditor": {"SELECT"},
    "DataOwner": {"SELECT", "INSERT", "UPDATE", "DELETE"},
}
SENSITIVE_ROLES = {"Auditor", "DataOwner"}
EXPORT_COLUMNS = {
    "Vendedor": "id_cliente,codigo_cliente,nombres,apellidos,distrito,segmento",
    "Cajero": "id_cliente,codigo_cliente,nombres,apellidos,distrito,segmento",
    "Supervisor": "id_cliente,codigo_cliente,nombres,apellidos,correo,telefono,distrito,segmento",
    "Auditor": "id_cliente,codigo_cliente,num_documento,nombres,apellidos,correo,telefono,distrito,segmento",
    "DataOwner": "id_cliente,codigo_cliente,num_documento,nombres,apellidos,correo,telefono,distrito,segmento",
}

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE clientes (
 id_cliente INTEGER PRIMARY KEY, codigo_cliente TEXT UNIQUE NOT NULL,
 num_documento TEXT UNIQUE NOT NULL CHECK(num_documento GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
 nombres TEXT NOT NULL, apellidos TEXT NOT NULL,
 correo TEXT NOT NULL, telefono TEXT NOT NULL, distrito TEXT NOT NULL,
 segmento TEXT NOT NULL DEFAULT 'Nuevo', fecha_registro TEXT NOT NULL
);
CREATE TABLE productos_servicios (
 id_producto INTEGER PRIMARY KEY, nombre_producto TEXT NOT NULL,
 categoria TEXT NOT NULL, precio_base REAL NOT NULL CHECK(precio_base>=0), activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE operaciones (
 id_operacion INTEGER PRIMARY KEY, codigo_operacion TEXT UNIQUE NOT NULL,
 id_cliente INTEGER NOT NULL REFERENCES clientes(id_cliente) ON DELETE RESTRICT,
 fecha_operacion TEXT NOT NULL, canal TEXT NOT NULL,
 estado TEXT NOT NULL, monto_total REAL NOT NULL CHECK(monto_total>=0)
);
CREATE TABLE detalle_operacion (
 id_detalle INTEGER PRIMARY KEY, id_operacion INTEGER NOT NULL REFERENCES operaciones(id_operacion),
 id_producto INTEGER NOT NULL REFERENCES productos_servicios(id_producto),
 cantidad INTEGER NOT NULL CHECK(cantidad>0), precio_unitario REAL NOT NULL,
 subtotal REAL NOT NULL
);
CREATE TABLE pagos (
 id_pago INTEGER PRIMARY KEY, id_operacion INTEGER NOT NULL REFERENCES operaciones(id_operacion),
 fecha_pago TEXT NOT NULL, medio_pago TEXT NOT NULL,
 monto_pagado REAL NOT NULL, estado_pago TEXT NOT NULL
);
CREATE TABLE auditoria (
 id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, rol TEXT NOT NULL,
 accion TEXT NOT NULL, resultado TEXT NOT NULL, detalle TEXT NOT NULL
);
"""

PRODUCTS = [
    (1, "Producto demostrativo A", "Medicamentos", 18.50, 1),
    (2, "Producto demostrativo B", "Cuidado personal", 12.90, 1),
    (3, "Producto demostrativo C", "Bienestar", 24.00, 1),
    (4, "Producto demostrativo D", "Medicamentos", 8.40, 1),
    (5, "Producto demostrativo E", "Bienestar", 31.50, 1),
]
CLIENTS = [
    (1, "C00001", "10000001", "Ana", "Ejemplo", "ana@example.com", "900000001", "Lima", "Frecuente", "2026-07-01"),
    (2, "C00002", "10000002", "Luis", "Demostración", "luis@example.com", "900000002", "Callao", "Nuevo", "2026-07-02"),
    (3, "C00003", "10000003", "María", "Prueba", "maria@example.com", "900000003", "Ate", "Frecuente", "2026-07-03"),
]


def new_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO productos_servicios VALUES (?,?,?,?,?)", PRODUCTS)
    conn.executemany("INSERT INTO clientes VALUES (?,?,?,?,?,?,?,?,?,?)", CLIENTS)
    conn.commit()
    return conn


def audit(conn: sqlite3.Connection, role: str, action: str, result: str, detail: str) -> None:
    conn.execute(
        "INSERT INTO auditoria(fecha,rol,accion,resultado,detalle) VALUES(?,?,?,?,?)",
        (datetime.now().isoformat(timespec="seconds"), role, action, result, detail),
    )
    conn.commit()


def validate_client(names: str, surnames: str, dni: str, email: str, phone: str) -> None:
    for label, value in (("Nombres", names), ("Apellidos", surnames)):
        if not value.strip() or not all(ch.isalpha() or ch.isspace() for ch in value.strip()):
            raise ValueError(f"{label}: usa solo letras y espacios.")
    if not re.fullmatch(r"[0-9]{8}", dni):
        raise ValueError("El DNI debe tener exactamente 8 dígitos.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("El correo no tiene un formato válido.")
    if not re.fullmatch(r"[0-9]{9}", phone):
        raise ValueError("El teléfono debe tener exactamente 9 dígitos.")


def clients_view(conn: sqlite3.Connection, role: str, search: str = "") -> pd.DataFrame:
    if role not in PERMISSIONS:
        raise PermissionError("Rol no autorizado.")
    columns = EXPORT_COLUMNS[role]
    sql = f"SELECT {columns} FROM clientes WHERE nombres LIKE ? OR apellidos LIKE ? OR num_documento LIKE ? ORDER BY id_cliente DESC"
    term = f"%{search.strip()}%"
    return pd.read_sql_query(sql, conn, params=(term, term, term))


def add_client(conn: sqlite3.Connection, role: str, names: str, surnames: str, dni: str, email: str, phone: str, district: str) -> int:
    if "INSERT" not in PERMISSIONS.get(role, set()):
        audit(conn, role, "Agregar cliente", "DENEGADO", "Sin permiso")
        raise PermissionError("Este rol no puede agregar clientes.")
    try:
        validate_client(names, surnames, dni, email, phone)
        if conn.execute("SELECT 1 FROM clientes WHERE num_documento=?", (dni,)).fetchone():
            raise ValueError("Ya existe un cliente con ese DNI.")
        next_id = conn.execute("SELECT COALESCE(MAX(id_cliente),0)+1 FROM clientes").fetchone()[0]
        conn.execute(
            "INSERT INTO clientes VALUES(?,?,?,?,?,?,?,?,?,?)",
            (next_id, f"C{next_id:05d}", dni, names.strip().title(), surnames.strip().title(), email.strip(), phone, district.strip() or "Lima", "Nuevo", date.today().isoformat()),
        )
        conn.commit()
        audit(conn, role, "Agregar cliente", "OK", f"ID {next_id}")
        return next_id
    except (ValueError, sqlite3.Error) as exc:
        audit(conn, role, "Agregar cliente", "RECHAZADO", str(exc))
        raise ValueError(str(exc)) from exc


def update_client(conn: sqlite3.Connection, role: str, client_id: int, field: str, value: str) -> None:
    if "UPDATE" not in PERMISSIONS.get(role, set()):
        audit(conn, role, "Actualizar cliente", "DENEGADO", "Sin permiso")
        raise PermissionError("Este rol no puede editar clientes.")
    validators = {
        "correo": lambda v: re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v),
        "telefono": lambda v: re.fullmatch(r"[0-9]{9}", v),
        "apellidos": lambda v: v.strip() and all(ch.isalpha() or ch.isspace() for ch in v.strip()),
        "distrito": lambda v: v.strip() and all(ch.isalpha() or ch.isspace() for ch in v.strip()),
    }
    if field not in validators or not validators[field](value):
        audit(conn, role, "Actualizar cliente", "RECHAZADO", "Campo o valor inválido")
        raise ValueError("Campo o valor inválido.")
    cursor = conn.execute(f"UPDATE clientes SET {field}=? WHERE id_cliente=?", (value.strip(), client_id))
    conn.commit()
    if cursor.rowcount == 0:
        raise ValueError("Cliente no encontrado.")
    audit(conn, role, "Actualizar cliente", "OK", f"ID {client_id}, campo {field}")


def delete_client(conn: sqlite3.Connection, role: str, client_id: int) -> None:
    if "DELETE" not in PERMISSIONS.get(role, set()):
        audit(conn, role, "Eliminar cliente", "DENEGADO", "Sin permiso")
        raise PermissionError("Este rol no puede eliminar clientes.")
    try:
        cursor = conn.execute("DELETE FROM clientes WHERE id_cliente=?", (client_id,))
        conn.commit()
    except sqlite3.IntegrityError as exc:
        audit(conn, role, "Eliminar cliente", "RECHAZADO", "Tiene ventas asociadas")
        raise ValueError("No se puede eliminar un cliente con ventas asociadas.") from exc
    if cursor.rowcount == 0:
        raise ValueError("Cliente no encontrado.")
    audit(conn, role, "Eliminar cliente", "OK", f"ID {client_id}")


def products_view(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT id_producto,nombre_producto,categoria,precio_base FROM productos_servicios WHERE activo=1 ORDER BY categoria,nombre_producto", conn)


def add_sale(conn: sqlite3.Connection, role: str, client_id: int, product_id: int, quantity: int, payment_method: str) -> tuple[str, float]:
    if "INSERT" not in PERMISSIONS.get(role, set()):
        audit(conn, role, "Registrar venta", "DENEGADO", "Sin permiso")
        raise PermissionError("Este rol no puede registrar ventas.")
    if quantity <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")
    if not conn.execute("SELECT 1 FROM clientes WHERE id_cliente=?", (client_id,)).fetchone():
        raise ValueError("Cliente no encontrado.")
    product = conn.execute("SELECT nombre_producto,precio_base FROM productos_servicios WHERE id_producto=? AND activo=1", (product_id,)).fetchone()
    if product is None:
        raise ValueError("Producto no encontrado.")
    total = round(float(product["precio_base"]) * quantity, 2)
    next_id = conn.execute("SELECT COALESCE(MAX(id_operacion),0)+1 FROM operaciones").fetchone()[0]
    code = f"O{next_id:05d}"
    try:
        with conn:
            conn.execute("INSERT INTO operaciones VALUES(?,?,?,?,?,?,?)", (next_id, code, client_id, date.today().isoformat(), "Mostrador", "Completado", total))
            conn.execute("INSERT INTO detalle_operacion(id_operacion,id_producto,cantidad,precio_unitario,subtotal) VALUES(?,?,?,?,?)", (next_id, product_id, quantity, float(product["precio_base"]), total))
            conn.execute("INSERT INTO pagos(id_operacion,fecha_pago,medio_pago,monto_pagado,estado_pago) VALUES(?,?,?,?,?)", (next_id, date.today().isoformat(), payment_method, total, "Pagado"))
        audit(conn, role, "Registrar venta", "OK", code)
        return code, total
    except sqlite3.Error as exc:
        audit(conn, role, "Registrar venta", "RECHAZADO", "Error de transacción")
        raise ValueError("No se pudo registrar la venta.") from exc


def sales_view(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        """SELECT o.codigo_operacion AS codigo, o.fecha_operacion AS fecha,
           c.nombres || ' ' || c.apellidos AS cliente,
           p.nombre_producto AS producto, d.cantidad, o.monto_total AS total,
           o.estado
           FROM operaciones o JOIN clientes c ON c.id_cliente=o.id_cliente
           JOIN detalle_operacion d ON d.id_operacion=o.id_operacion
           JOIN productos_servicios p ON p.id_producto=d.id_producto
           ORDER BY o.id_operacion DESC""", conn,
    )


def sales_by_category(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        """SELECT p.categoria, ROUND(SUM(d.subtotal),2) AS ventas
           FROM detalle_operacion d JOIN productos_servicios p ON p.id_producto=d.id_producto
           GROUP BY p.categoria ORDER BY ventas DESC""", conn,
    )


def audit_view(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT fecha,rol,accion,resultado,detalle FROM auditoria ORDER BY id DESC LIMIT 50", conn)


def kpis(conn: sqlite3.Connection) -> dict[str, float]:
    clients = conn.execute("SELECT COUNT(*),SUM(CASE WHEN correo LIKE '%@%.%' THEN 1 ELSE 0 END) FROM clientes").fetchone()
    sales = conn.execute("SELECT COUNT(*),COALESCE(SUM(monto_total),0) FROM operaciones").fetchone()
    checks = conn.execute("SELECT COUNT(*) FROM auditoria").fetchone()[0]
    return {"clientes": float(clients[0]), "contacto": round(100 * (clients[1] or 0) / clients[0], 1) if clients[0] else 100.0, "ventas": float(sales[0]), "ingresos": float(sales[1]), "auditoria": float(checks)}
