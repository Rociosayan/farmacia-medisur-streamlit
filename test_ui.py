import unittest

from streamlit.testing.v1 import AppTest


class MedisurUiTests(unittest.TestCase):
    def test_every_section_renders(self):
        app = AppTest.from_file("app.py", default_timeout=20).run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        for page in ("Clientes", "Ventas", "Catálogo de datos", "Reportes", "Calidad", "Gobierno", "KPIs y DQM"):
            app.sidebar.radio[0].set_value(page).run()
            self.assertFalse(app.exception, f"{page}: {[e.message for e in app.exception]}")


if __name__ == "__main__":
    unittest.main()
