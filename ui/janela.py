import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, QSignalBlocker, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QSlider, QVBoxLayout, QWidget,
)
from core.geometria import calcular_geometria
from ui.diagrama import DiagramaRaios
from ui.tema import TEMA_AZUL, TEMA_INFRAVERMELHO

MASSA_SOLAR_KG = 1.989e30
RAD_PARA_ARCSEC = 180.0 * 3600.0 / np.pi


class JanelaSimulador(QMainWindow):
    def __init__(self, motor, simulador, pos_inicial_x, pos_inicial_y, sigma):
        super().__init__()
        self.motor = motor
        self.simulador = simulador
        self.sigma = sigma
        self.escala_pos = 1e-7
        self.escala_sigma = 1e-8
        self.escala_observador = 0.5  # kpc comóveis por passo
        self.modo_infravermelho = False
        self.setWindowTitle("Simulador de Lente Gravitacional - Ray Tracing")
        self.resize(1440, 900)
        self.setMinimumSize(960, 660)
        self.timer_render = QTimer(self)
        self.timer_render.setSingleShot(True)
        self.timer_render.setInterval(16)
        self.timer_render.timeout.connect(self.atualizar_render)
        widget_central = QWidget()
        layout = QVBoxLayout(widget_central)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        self.setCentralWidget(widget_central)

        titulo = QLabel("Lente gravitacional · da trajetória da luz à imagem")
        titulo.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(titulo)
        paineis = QHBoxLayout()
        paineis.setSpacing(16)
        layout.addLayout(paineis, stretch=1)
        imagem = QVBoxLayout()
        esquema = QVBoxLayout()
        paineis.addLayout(imagem, stretch=1)
        paineis.addLayout(esquema, stretch=1)
        self.titulo_imagem = QLabel("VISÃO DO TELESCÓPIO")
        self.titulo_esquema = QLabel("TRAJETÓRIA DA LUZ")
        imagem.addWidget(self.titulo_imagem)
        esquema.addWidget(self.titulo_esquema)

        self.canvas = pg.GraphicsLayoutWidget()
        self.canvas.setBackground("#031823")
        imagem.addWidget(self.canvas, stretch=1)
        self.view_box = self.canvas.addViewBox()
        self.view_box.setAspectLocked(True)
        self.view_box.setDefaultPadding(0)
        self.img_item = pg.ImageItem(axisOrder="row-major")
        self.view_box.addItem(self.img_item)
        self.view_box.setRange(xRange=(0, motor.largura), yRange=(0, motor.altura), padding=0)
        self.view_box.disableAutoRange()
        self.lut_infravermelho = pg.colormap.get("inferno").getLookupTable()
        self.diagrama = DiagramaRaios()
        esquema.addWidget(self.diagrama, stretch=1)

        self.botao_modo = QPushButton("Ver em infravermelho")
        self.botao_modo.setCheckable(True)
        self.botao_modo.setToolTip("Alterna a aparência da imagem sem alterar os parâmetros físicos.")
        self.botao_modo.toggled.connect(self.alternar_modo)
        imagem.addWidget(self.botao_modo)
        # Reserva a mesma altura do botão para alinhar os dois painéis.
        self.espaco_botao = QWidget()
        esquema.addWidget(self.espaco_botao)

        controles = QHBoxLayout()
        layout.addLayout(controles)
        grupo_fonte = QGroupBox("Fonte")
        form_fonte = QFormLayout(grupo_fonte)
        self.slider_x = self.criar_slider(-250, 250, round(pos_inicial_x / self.escala_pos))
        self.slider_y = self.criar_slider(-250, 250, round(pos_inicial_y / self.escala_pos))
        self.slider_sigma = self.criar_slider(1, 200, round(sigma / self.escala_sigma))
        self.valor_x = self.adicionar_controle(form_fonte, "Posição X:", self.slider_x)
        self.valor_y = self.adicionar_controle(form_fonte, "Posição Y:", self.slider_y)
        self.valor_sigma = self.adicionar_controle(form_fonte, "Tamanho (σ):", self.slider_sigma)
        controles.addWidget(grupo_fonte, stretch=1)

        grupo_lente = QGroupBox("Lente gravitacional")
        form_lente = QFormLayout(grupo_lente)
        self.slider_massa = self.criar_slider(10, 500, round(simulador.M / (1e10 * MASSA_SOLAR_KG)))
        self.valor_massa = self.adicionar_controle(form_lente, "Massa:", self.slider_massa)
        self.valor_einstein = QLabel()
        form_lente.addRow("Raio de Einstein:", self.valor_einstein)
        self.botao_alinhar = QPushButton("Alinhar · formar anel")
        self.botao_alinhar.clicked.connect(self.alinhar_fonte)
        form_lente.addRow(self.botao_alinhar)
        controles.addWidget(grupo_lente, stretch=1)

        grupo_observador = QGroupBox("Observador")
        form_observador = QFormLayout(grupo_observador)
        self.slider_obs_x = self.criar_slider(-40, 40, 0)
        self.slider_obs_y = self.criar_slider(-40, 40, 0)
        self.valor_obs_x = self.adicionar_controle(form_observador, "Posição X:", self.slider_obs_x)
        self.valor_obs_y = self.adicionar_controle(form_observador, "Posição Y:", self.slider_obs_y)
        obs_nota = QLabel("Deslocamento transversal em kpc comóveis.")
        obs_nota.setWordWrap(True)
        form_observador.addRow(obs_nota)
        controles.addWidget(grupo_observador, stretch=1)

        self.aplicar_tema()
        self.atualizar_render()


    def aplicar_tema(self):
        tema = TEMA_INFRAVERMELHO if self.modo_infravermelho else TEMA_AZUL
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {tema['fundo']}; color: {tema['texto']}; }}
            QGroupBox {{ border: 1px solid {tema['borda']}; border-radius: 8px;
                         margin-top: 12px; padding: 16px 12px 10px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 5px; }}
            QLabel {{ background: transparent; }}
            QPushButton {{ background: {tema['botao']}; border: 1px solid {tema['borda_botao']};
                           border-radius: 6px; padding: 8px 12px; }}
            QPushButton:hover {{ background: {tema['hover']}; }}
            QPushButton:checked {{ background: {tema['botao']}; }}
            QSlider::groove:horizontal {{ height: 5px; background: {tema['borda']}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {tema['destaque']}; width: 14px;
                                         margin: -5px 0; border-radius: 7px; }}
        """)
        for cabecalho in (self.titulo_imagem, self.titulo_esquema):
            cabecalho.setStyleSheet(
                f"color: {tema['destaque']}; font-weight: 600; font-size: 13px;"
            )
        # O fundo da cena inteira coincide exatamente com a intensidade zero.
        # Mantemos pixels quadrados, sem esticar a imagem ou cortar o campo.
        fundo = (QColor(*map(int, self.lut_infravermelho[0][:3]))
                 if self.modo_infravermelho else QColor(tema["canvas"]))
        self.canvas.setBackground(fundo)
        self.diagrama.definir_tema(tema)
        self.espaco_botao.setFixedHeight(self.botao_modo.sizeHint().height())

    def criar_slider(self, minimo, maximo, valor):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimo, maximo)
        slider.setValue(valor)
        slider.valueChanged.connect(self.agendar_render)
        return slider

    def adicionar_controle(self, layout, titulo, slider):
        linha = QHBoxLayout()
        linha.addWidget(slider, stretch=1)
        valor = QLabel()
        valor.setMinimumWidth(90)
        linha.addWidget(valor)
        layout.addRow(titulo, linha)
        slider.setAccessibleName(titulo.rstrip(":"))
        return valor

    def agendar_render(self):
        if not self.timer_render.isActive():
            self.timer_render.start()

    def alinhar_fonte(self):
        # Coloca fonte, lente e observador no mesmo eixo.
        for slider in (self.slider_x, self.slider_y, self.slider_obs_x, self.slider_obs_y):
            with QSignalBlocker(slider):
                slider.setValue(0)
        self.atualizar_render()

    def alternar_modo(self, infravermelho):
        self.modo_infravermelho = infravermelho
        self.aplicar_tema()
        self.exibir_imagem()

    def exibir_imagem(self):
        if self.modo_infravermelho:
            self.img_item.setLookupTable(self.lut_infravermelho)
            self.img_item.setImage(self.frame, autoLevels=False, levels=(0, 255))
            self.titulo_imagem.setText("VISÃO EM INFRAVERMELHO")
            self.botao_modo.setText("Voltar ao anel azul")
        else:
            self.img_item.setLookupTable(None)
            self.img_item.setImage(self.frame_telescopio, autoLevels=False, levels=(0, 255))
            self.titulo_imagem.setText("VISÃO DO TELESCÓPIO")
            self.botao_modo.setText("Ver em infravermelho")

    def atualizar_render(self):
        self.timer_render.stop()
        pos_x = self.slider_x.value() * self.escala_pos
        pos_y = self.slider_y.value() * self.escala_pos
        obs_x = self.slider_obs_x.value() * self.escala_observador
        obs_y = self.slider_obs_y.value() * self.escala_observador
        self.sigma = self.slider_sigma.value() * self.escala_sigma
        self.simulador.atualizar_parametros(massa_lente=self.slider_massa.value() * 1e10 * MASSA_SOLAR_KG)
        geometria = calcular_geometria(self.simulador, pos_x, pos_y, self.sigma, obs_x, obs_y)
        self.frame = self.motor.renderizar_frame(self.simulador, *geometria.beta_efetivo, self.sigma)
        self.frame_telescopio = self.motor.renderizar_telescopio(self.simulador, self.frame)
        self.diagrama.atualizar(geometria)
        self.exibir_imagem()
        self.valor_x.setText(f"{pos_x * RAD_PARA_ARCSEC:.2f} arcsec")
        self.valor_y.setText(f"{pos_y * RAD_PARA_ARCSEC:.2f} arcsec")
        self.valor_sigma.setText(f"{self.sigma * RAD_PARA_ARCSEC:.2f} arcsec")
        self.valor_obs_x.setText(f"{obs_x:.1f} kpc")
        self.valor_obs_y.setText(f"{obs_y:.1f} kpc")
        self.valor_massa.setText(f"{self.slider_massa.value()} × 10¹⁰ M☉")
        self.valor_einstein.setText(f"{self.simulador.theta_E * RAD_PARA_ARCSEC:.2f} arcsec")
