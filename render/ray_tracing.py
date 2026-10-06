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
        self.fov_radianos = fov_radianos
        # Textura fixa: mover os controles não faz o céu cintilar aleatoriamente.
        rng = np.random.default_rng(42)
        self.textura = rng.uniform(0.72, 1.18, (altura, largura)).astype(np.float32)
        self.fundo = np.empty((altura, largura, 3), dtype=np.float32)
        self.fundo[:] = (3, 24, 35)
        estrelas = rng.random((altura, largura)) > 0.9996
        self.fundo[estrelas] += rng.uniform(25, 95, (estrelas.sum(), 1))
        self.raio = np.hypot(self.theta_x, self.theta_y)


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

    def renderizar_telescopio(self, simulador: SimuladorLente, frame):
        """Coloriza o mesmo ray tracing e adiciona a luz da galáxia lente.

        A galáxia central e a textura são ilustrativas. A posição e a forma
        dos arcos vêm exclusivamente do frame calculado pela equação da lente.
        O campo de visão é fixo, permitindo comparar diferentes massas.
        """
        tamanho_lente = max(simulador.theta_E * 0.18, self.fov_radianos / 150)
        halo = np.exp(-0.5 * (self.raio / tamanho_lente) ** 2)
        nucleo = np.exp(-0.5 * (self.raio / (tamanho_lente * 0.22)) ** 2)
        luz_lente = halo * self.textura
        # Curva de exposição fixa para revelar as bordas tênues dos arcos.
        arcos = np.sqrt(frame.astype(np.float32) / 255.0) * self.textura
        imagem = self.fundo.copy()
        for canal, (cor_arco, cor_halo) in enumerate(zip((145, 205, 235), (57, 112, 109))):
            imagem[:, :, canal] += arcos * cor_arco + luz_lente * cor_halo + nucleo * 95
        return np.clip(imagem, 0, 255).astype(np.uint8)
