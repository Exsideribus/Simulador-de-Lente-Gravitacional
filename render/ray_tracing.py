import numpy as np
from core.equacoes import SimuladorLente
from render.gerador_fonte import perfil_gaussiano

class MotorRenderizacao:
    def __init__(self, largura, altura, fov_arco_segundos):
        '''
        inicializa a matriz do observador
        largura -> Resolução horizontal em pixels
        altura -> Resolução vertical em pixels
        fov_arco_segundos -> Campo de visão total do grid em arco-segundos
        '''

        self.altura = altura
        self.largura = largura

        # conversão geométrica: arsec -> radianos
        fov_radianos = fov_arco_segundos * (np.pi / (180.0 * 3600.0))

        # Criação dos eixos espaciais centralizados no zero
        x = np.linspace(-fov_radianos/2, fov_radianos/2, self.largura)
        y = np.linspace(-fov_radianos/2, fov_radianos/2, self.altura)

        self.theta_x, self.theta_y = np.meshgrid(x, y)

    def renderizar_frame(self, simulador: SimuladorLente, pos_fonte_x, pos_fonte_y, sigma_fonte):
        '''
        Executa o pipeline de ray-tracing para atualizar o frame de vídeo
        Retorna a matriz de pixels deformada
        '''

        # Inversão vetorial: Deforma a malha do observadora até o plano da fonte
        beta_x, beta_y = simulador.equacao_lente_inversa(self.theta_x, self.theta_y)

        # Amostragem de brilho: Calcula a intensidade luminosa nos pontos deformados
        imagem_renderizada = perfil_gaussiano(beta_x, beta_y, pos_fonte_x, pos_fonte_y, sigma_fonte)

        return imagem_renderizada