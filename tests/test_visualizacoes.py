import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
import numpy as np
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from core.equacoes import SimuladorLente
from render.ray_tracing import MotorRenderizacao
from ui.janela import JanelaSimulador

ARCSEC = np.pi / (180 * 3600)


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.motor = MotorRenderizacao(240, 200, 10)
        self.lente = SimuladorLente(2e42, 0.5, 2)

    def test_anel_no_raio_de_einstein(self):
        frame = self.motor.renderizar_frame(self.lente, 0, 0, 0.08 * ARCSEC)
        raio = self.motor.raio[frame > 250]
        self.assertGreater(raio.size, 0)
        self.assertAlmostEqual(np.median(raio) / self.lente.theta_E, 1, delta=0.02)

    def test_telescopio_deterministico_rgb(self):
        frame = self.motor.renderizar_frame(self.lente, ARCSEC, 0.5 * ARCSEC, 0.2 * ARCSEC)
        rgb = self.motor.renderizar_telescopio(self.lente, frame)
        self.assertEqual(rgb.shape, (200, 240, 3))
        self.assertEqual(rgb.dtype, np.uint8)
        np.testing.assert_array_equal(rgb, self.motor.renderizar_telescopio(self.lente, frame))
        sem_fonte = self.motor.renderizar_telescopio(self.lente, np.zeros_like(frame))
        diferenca = rgb.astype(int) - sem_fonte.astype(int)
        self.assertTrue(np.all(diferenca[frame == 0] == 0))
        self.assertTrue(np.any(diferenca[frame > 0] > 0))

    def test_massa_muda_raio_e_ambas_imagens(self):
        frame1 = self.motor.renderizar_frame(self.lente, 0, 0, 0.1 * ARCSEC)
        rgb1 = self.motor.renderizar_telescopio(self.lente, frame1)
        raio1 = self.lente.theta_E
        self.lente.atualizar_parametros(massa_lente=4 * self.lente.M)
        self.assertAlmostEqual(self.lente.theta_E / raio1, 2)
        frame2 = self.motor.renderizar_frame(self.lente, 0, 0, 0.1 * ARCSEC)
        rgb2 = self.motor.renderizar_telescopio(self.lente, frame2)
        self.assertFalse(np.array_equal(frame1, frame2))
        self.assertFalse(np.array_equal(rgb1, rgb2))


class GeometriaTests(unittest.TestCase):
    def setUp(self):
        self.lente = SimuladorLente(2e42, .5, 2)

    def test_solucoes_satisfazem_equacao_inversa(self):
        from core.geometria import imagens_pontuais
        for beta in ((0, 0), (ARCSEC, -.4 * ARCSEC), (-2 * ARCSEC, ARCSEC)):
            theta = imagens_pontuais(beta, self.lente.theta_E)
            bx, by = self.lente.equacao_lente_inversa(theta[:, 0], theta[:, 1])
            np.testing.assert_allclose(bx, beta[0], atol=1e-14)
            np.testing.assert_allclose(by, beta[1], atol=1e-14)

    def test_raios_conectam_fonte_lente_e_observador(self):
        from core.geometria import calcular_geometria
        g = calcular_geometria(self.lente, ARCSEC, .3 * ARCSEC, .2 * ARCSEC, 8, -4)
        for raio in g.raios:
            np.testing.assert_allclose(raio[2, 1:], g.observador)
            theta = (raio[1, 1:] - (1 - g.fracao_lente) * g.observador) / g.fracao_lente
            beta = np.array(self.lente.equacao_lente_inversa(*theta))
            esperado = raio[0, 1:] + g.observador * (1 / g.fracao_lente - 1)
            np.testing.assert_allclose(beta, esperado, atol=1e-14)
        self.assertTrue(np.all(g.raios[:, 0, 0] == 0))
        self.assertTrue(np.all(g.raios[:, 2, 0] == 1))

    def test_distancias_e_redshifts_permanecem_sincronizados(self):
        from core.geometria import calcular_geometria
        self.lente.atualizar_parametros(z_l=.8, z_s=3)
        g = calcular_geometria(self.lente, 0, 0, .2 * ARCSEC)
        self.assertEqual((self.lente.z_l, self.lente.z_s), (.8, 3))
        self.assertAlmostEqual(g.fracao_lente, self.lente.Dl * 1.8 / (self.lente.Ds * 4))


class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.janela = JanelaSimulador(
            MotorRenderizacao(240, 240, 10), SimuladorLente(2e42, .5, 2),
            ARCSEC, .5 * ARCSEC, .2 * ARCSEC,
        )

    def tearDown(self):
        self.janela.close()

    def test_sigma_inicial_e_orientacao(self):
        self.assertAlmostEqual(self.janela.sigma, .2 * ARCSEC, delta=.5e-8)
        self.assertEqual(self.janela.img_item.axisOrder, "row-major")
        self.assertEqual(self.janela.img_item.image.shape, (240, 240, 3))

    def test_todos_controles_atualizam_imagem_e_raios(self):
        for slider in (self.janela.slider_massa, self.janela.slider_x,
                       self.janela.slider_y, self.janela.slider_sigma,
                       self.janela.slider_obs_x, self.janela.slider_obs_y):
            with self.subTest(controle=slider.accessibleName()):
                frame = self.janela.frame.copy()
                raios = self.janela.diagrama.geometria.raios.copy()
                slider.setValue(slider.value() + 10)
                QTest.qWait(80)
                self.assertFalse(np.array_equal(frame, self.janela.frame))
                self.assertFalse(np.array_equal(raios, self.janela.diagrama.geometria.raios))
                g = self.janela.diagrama.geometria
                esperado = self.janela.motor.renderizar_frame(
                    self.janela.simulador, *g.beta_efetivo, self.janela.sigma)
                np.testing.assert_array_equal(esperado, self.janela.frame)

    def test_botao_alterna_sem_alterar_fisica_e_preserva_modo(self):
        frame = self.janela.frame.copy()
        raios = self.janela.diagrama.geometria.raios.copy()
        self.janela.botao_modo.click()
        self.assertTrue(self.janela.modo_infravermelho)
        np.testing.assert_array_equal(self.janela.img_item.image, frame)
        np.testing.assert_array_equal(self.janela.diagrama.geometria.raios, raios)
        self.janela.slider_massa.setValue(180)
        QTest.qWait(80)
        self.assertTrue(self.janela.modo_infravermelho)
        self.assertFalse(np.array_equal(frame, self.janela.frame))
        np.testing.assert_array_equal(self.janela.img_item.image, self.janela.frame)
        self.janela.botao_modo.click()
        self.assertFalse(self.janela.modo_infravermelho)
        self.assertIsNone(self.janela.img_item.lut)
        np.testing.assert_array_equal(self.janela.img_item.image, self.janela.frame_telescopio)

    def test_alinhamento_e_extremos(self):
        self.janela.slider_obs_x.setValue(20)
        self.janela.botao_alinhar.click()
        for slider in (self.janela.slider_x, self.janela.slider_y,
                       self.janela.slider_obs_x, self.janela.slider_obs_y):
            self.assertEqual(slider.value(), 0)
        np.testing.assert_array_equal(self.janela.frame, np.flipud(self.janela.frame))
        np.testing.assert_array_equal(self.janela.frame, np.fliplr(self.janela.frame))
        for valor in (10, 500):
            self.janela.slider_massa.setValue(valor)
            self.janela.slider_sigma.setValue(1)
            self.janela.slider_x.setValue(250)
            self.janela.slider_obs_y.setValue(-40)
            QTest.qWait(80)
            self.assertTrue(np.isfinite(self.janela.frame_telescopio).all())
            self.assertTrue(np.isfinite(self.janela.diagrama.geometria.raios).all())


if __name__ == "__main__":
    unittest.main()