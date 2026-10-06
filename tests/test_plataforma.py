import os
import unittest
from unittest.mock import patch
from main import configurar_plataforma_qt


class PlataformaTests(unittest.TestCase):
    def test_wsl_com_display_prefere_xcb(self):
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True), \
             patch("main.sys.platform", "linux"), \
             patch("main.platform.release", return_value="6.6.87.2-microsoft-standard-WSL2"):
            configurar_plataforma_qt()
            self.assertEqual(os.environ["QT_QPA_PLATFORM"], "xcb")

    def test_preserva_backend_explicito(self):
        for backend in ("offscreen", "wayland", "xcb"):
            with self.subTest(backend=backend), \
                 patch.dict(os.environ, {"DISPLAY": ":0", "QT_QPA_PLATFORM": backend}, clear=True), \
                 patch("main.sys.platform", "linux"), \
                 patch("main.platform.release", return_value="microsoft-standard-WSL2"):
                configurar_plataforma_qt()
                self.assertEqual(os.environ["QT_QPA_PLATFORM"], backend)

    def test_outros_ambientes_nao_sao_alterados(self):
        for sistema, kernel, ambiente in (
            ("linux", "6.8.0-generic", {"DISPLAY": ":0"}),
            ("win32", "10", {}),
            ("linux", "microsoft-standard-WSL2", {}),
        ):
            with self.subTest(sistema=sistema, kernel=kernel), \
                 patch.dict(os.environ, ambiente, clear=True), \
                 patch("main.sys.platform", sistema), \
                 patch("main.platform.release", return_value=kernel):
                configurar_plataforma_qt()
                self.assertNotIn("QT_QPA_PLATFORM", os.environ)

