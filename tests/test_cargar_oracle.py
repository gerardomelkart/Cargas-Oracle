import tempfile
import unittest
from datetime import date
from pathlib import Path

import cargar_oracle


class CargarOracleTests(unittest.TestCase):
    def test_periodo_anterior_cambia_de_anio(self):
        self.assertEqual(cargar_oracle.periodo_anterior(date(2026, 1, 15)), (2025, 12))

    def test_sufijo_periodo_explicito(self):
        self.assertEqual(cargar_oracle.sufijo_periodo("202607"), "JUL2026")

    def test_busqueda_no_distingue_mayusculas(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "subcarpeta"
            ruta.mkdir()
            esperado = ruta / "cni_rnip_01.DAT"
            esperado.touch()
            self.assertEqual(cargar_oracle.buscar_archivo(Path(temporal), "CNI_RNIP_01.dat"), esperado)

    def test_estructura_incluye_ultimo_caracter(self):
        columnas = [("CAMPO", 1, 3)]
        self.assertEqual(cargar_oracle.convertir_fila("ABC\n", columnas, "datos.dat"), ("ABC", "datos.dat"))


if __name__ == "__main__":
    unittest.main()
