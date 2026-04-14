import numpy as np

# Constantes físicas 
G = 6.67430e-11 # Constante Gravitacional [6, 7]
C = 299792458    # Velocidade da luz [6, 8]

class simuladorLente:
    def __init__(self, massa_lente, dist_lente, dist_fonte):
        """
        :param massa_lente: Massa do objeto defletor (kg)
        :param dist_lente: Distância observador-lente (Dl) [9-11]
        :param dist_fonte: Distância observador-fonte (Ds) [10, 11]
        """
        self.M = massa_lente
        self.Dl = dist_lente
        self.Ds = dist_fonte
        self.Dls = dist_fonte - dist_lente # Distância lente-fonte [3, 9]
        
        # 1. Cálculo do Raio de Einstein [12-15]
        # escala fundamental do efeito de lenteamento.
        self.theta_E = np.sqrt((4 * G * self.M / C**2) * (self.Dls / (self.Dl * self.Ds)))

    def equacao_lente_inversa(self, theta_vec):
        """
        Aplica a Equação da Lente: beta = theta - alpha(theta) [3, 16-18]
        Para uma massa pontual (campo esfericamente simétrico).
        """
        theta_norm = np.linalg.norm(theta_vec)
        if theta_norm == 0:
            return np.array()
        
        # Ângulo de deflexão reduzido alpha = (theta_E^2 / |theta|) [19-21]
        deflexao = (self.theta_E**2 / theta_norm) * (theta_vec / theta_norm)
        
        # Posição na fonte 
        beta_vec = theta_vec - deflexao
        return beta_vec