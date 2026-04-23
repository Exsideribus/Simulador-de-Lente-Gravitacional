from core.cosmologia import calcular_distancia
import numpy as np

# Constantes físicas no SI
G = 6.67430e-11 
C = 299792458

class SimuladorLente:
    def __init__(self, massa_lente, z_l, z_s):
        self.M = massa_lente
        self.Dl, self.Ds, self.Dls = calcular_distancia(z_l, z_s)
        self.theta_E = np.sqrt((4 * G * self.M / C**2) * (self.Dls / (self.Dl * self.Ds)))

    def equacao_lente_inversa(self, theta_x, theta_y):
        """
        Aplica a Equação da Lente vetorizada para um grid 2D de observação
        theta_x -> Matriz NumPy com coordenadas X do plano da imagem
        theta_y -> Matriz NumPy com coordenadas Y do plano da imagem
        return -> Matrizes beta_x, beta_y mapeadas no plano da fonte
        """
        # Distância radial de cada pixel até o centro (0,0)
        theta_norm = np.hypot(theta_x, theta_y)
        
        # Tratamento da singularidade central para evitar divisão por zero
        # Substitui 0 por um valor infinitamente pequeno
        theta_norm_seguro = np.where(theta_norm == 0, 1e-10, theta_norm)
        
        # Ângulo de deflexão escalar
        deflexao_mag = (self.theta_E**2) / theta_norm_seguro
        
        # Decomposição vetorial do ângulo de deflexão
        alpha_x = deflexao_mag * (theta_x / theta_norm_seguro)
        alpha_y = deflexao_mag * (theta_y / theta_norm_seguro)
        
        # Equação da Lente
        beta_x = theta_x - alpha_x
        beta_y = theta_y - alpha_y
        
        return beta_x, beta_y