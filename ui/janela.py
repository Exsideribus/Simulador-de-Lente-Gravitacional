import sys
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel
from PyQt6.QtCore import Qt
import pyqtgraph as pg

class JanelaSimulador(QMainWindow):
    def __init__(self, motor, simulador, pos_inicial_x, pos_inicial_y, sigma):
        super().__init__()
        self.motor = motor
        self.simulador = simulador
        self.sigma = sigma
        
        # Configuração da Janela (1920x1080)
        self.setWindowTitle("Simulador de Lente Gravitacional - Ray Tracing")
        self.setGeometry(0, 0, 1920, 1080)
        
        # Layout Principal
        widget_central = QWidget()
        layout_principal = QHBoxLayout()
        widget_central.setLayout(layout_principal)
        self.setCentralWidget(widget_central)
        
        # Área de Renderização Gráfica
        self.canvas = pg.GraphicsLayoutWidget()
        layout_principal.addWidget(self.canvas, stretch=3) # Ocupa 3/4 da tela
        
        view_box = self.canvas.addViewBox()
        view_box.setAspectLocked(True)
        self.img_item = pg.ImageItem()
        view_box.addItem(self.img_item)
        
        # Painel de Controles
        painel_controles = QVBoxLayout()
        layout_principal.addLayout(painel_controles, stretch=1)
        
        # Fator de conversão do slider para radianos (resolução mais fina)
        self.escala_slider = 1e-7
        
        # Limite de +/- 250 unidades * 1e-7 = +/- 2.5e-5 radianos (~5 arco-segundos)
        limite_slider = 250
        
        # Slider X
        self.label_x = QLabel("Posição X da Fonte")
        self.slider_x = QSlider(Qt.Orientation.Horizontal)
        self.slider_x.setRange(-limite_slider, limite_slider) 
        self.slider_x.setValue(int(pos_inicial_x / self.escala_slider))
        self.slider_x.valueChanged.connect(self.atualizar_render)
        
        # Slider Y
        self.label_y = QLabel("Posição Y da Fonte")
        self.slider_y = QSlider(Qt.Orientation.Horizontal)
        self.slider_y.setRange(-limite_slider, limite_slider)
        self.slider_y.setValue(int(pos_inicial_y / self.escala_slider))
        self.slider_y.valueChanged.connect(self.atualizar_render)
        
        painel_controles.addWidget(self.label_x)
        painel_controles.addWidget(self.slider_x)
        painel_controles.addWidget(self.label_y)
        painel_controles.addWidget(self.slider_y)
        painel_controles.addStretch()
        
        # Primeira Renderização
        self.atualizar_render()

    def atualizar_render(self):
        # Captura os valores da interface e converte para radianos
        pos_x = self.slider_x.value() * self.escala_slider
        pos_y = self.slider_y.value() * self.escala_slider
        
        # Processa o motor numérico
        frame = self.motor.renderizar_frame(self.simulador, pos_x, pos_y, self.sigma)
        
        # Atualiza o buffer de vídeo do pyqtgraph. 
        # transpose() é necessário porque pyqtgraph inverte os eixos X e Y por padrão.
        self.img_item.setImage(frame.T, autoLevels=False, levels=(0, 255))