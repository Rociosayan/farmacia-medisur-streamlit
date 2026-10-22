import sqlite3
import unittest

from core import add_client, add_sale, clients_view, delete_client, kpis, new_database, sales_view, update_client


class MedisurCoreTests(unittest.TestCase):
    def setUp(self):
        self.conn = new_database()

    def tearDown(self):
        self.conn.close()

    def test_client_validation_permissions_and_crud(self):
        with self.assertRaises(ValueError):
            add_client(self.conn, "Vendedor", "Ana1", "Prueba", "10000004", "ana4@example.com", "900000004", "Lima")
        with self.assertRaises(PermissionError):
            add_client(self.conn, "Auditor", "Ana", "Prueba", "10000004", "ana4@example.com", "900000004", "Lima")
        client_id = add_client(self.conn, "Vendedor", "Ana", "Prueba", "10000004", "ana4@example.com", "900000004", "Lima")
        self.assertEqual(client_id, 4)
        self.assertNotIn("num_documento", clients_view(self.conn, "Vendedor").columns)
        self.assertIn("num_documento", clients_view(self.conn, "Auditor").columns)
        update_client(self.conn, "Cajero", client_id, "correo", "nuevo@example.com")
        self.assertEqual(self.conn.execute("SELECT correo FROM clientes WHERE id_cliente=?", (client_id,)).fetchone()[0], "nuevo@example.com")
        delete_client(self.conn, "Supervisor", client_id)
        self.assertIsNone(self.conn.execute("SELECT 1 FROM clientes WHERE id_cliente=?", (client_id,)).fetchone())

    def test_sale_writes_operation_detail_and_payment(self):
        code, total = add_sale(self.conn, "Vendedor", 1, 1, 2, "Efectivo")
        self.assertEqual((code, total), ("O00001", 37.0))
        for table in ("operaciones", "detalle_operacion", "pagos"):
            self.assertEqual(self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 1)
        self.assertEqual(len(sales_view(self.conn)), 1)
        self.assertEqual(kpis(self.conn)["ingresos"], 37.0)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM clientes WHERE id_cliente=1")
        with self.assertRaises(ValueError):
            add_sale(self.conn, "Vendedor", 1, 1, 0, "Efectivo")
        with self.assertRaises(PermissionError):
            add_sale(self.conn, "Auditor", 1, 1, 1, "Efectivo")


if __name__ == "__main__":
    unittest.main()
