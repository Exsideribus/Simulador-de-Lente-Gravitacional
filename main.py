import os
import platform
import sys

import numpy as np
from core.equacoes import SimuladorLente
from PyQt6.QtWidgets import QApplication
from render.ray_tracing import MotorRenderizacao
from ui.janela import JanelaSimulador


def configurar_plataforma_qt():
    """Prefere X11 no WSLg como alternativa ao backend Wayland."""
    if (
        sys.platform == "linux"
        and "microsoft" in platform.release().lower()
        and os.environ.get("DISPLAY")
    ):
        # Respeita escolhas explícitas, inclusive offscreen nos testes.
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")



def main():
    configurar_plataforma_qt()
    # Definição de Parâmetros Físicos Iniciais
    MASSA_GALAXIA = 2.0e42      # Em kg (~10^12 Massas Solares)
    Z_LENTE = 0.5               # Redshift da Lente
    Z_FONTE = 2.0               # Redshift da Fonte
    FOV_ARCSEC = 10.0           # Campo de visão em arco-segundos
    SIGMA_ARCSEC = 0.2          # Tamanho da fonte luminosa

    # Conversão de Sigma para radianos para o motor de renderização
    SIGMA_RAD = SIGMA_ARCSEC * (np.pi / (180.0 * 3600.0))

    # Fonte inicialmente alinhada para mostrar o anel de Einstein
    POS_INICIAL_X = 0.0 * (np.pi / (180.0 * 3600.0)) # alinhamento horizontal
    POS_INICIAL_Y = 0.0 * (np.pi / (180.0 * 3600.0))

    # Inicialização dos Módulos Core
    simulador = SimuladorLente(MASSA_GALAXIA, Z_LENTE, Z_FONTE)

    # Resolução interna de 800x800 para garantir FPS estável na CPU
    motor = MotorRenderizacao(largura=800, altura=800, fov_arco_segundos=FOV_ARCSEC)

    # Inicialização da UI
    app = QApplication(sys.argv)
    janela = JanelaSimulador(motor, simulador, POS_INICIAL_X, POS_INICIAL_Y, SIGMA_RAD)
    janela.showMaximized() # Tenta ocupar toda a tela (1920x1080)

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
