import numpy as np

def perfil_gaussiano(beta_x, beta_y, centro_x, centro_y, sigma, intensidade_max=255):
    '''
    Gera o perfil de luminosidade da fonte (Gaussiana 2D)
    beta_x -> Matriz X do plano da fonte (pós-deflexão)
    beta_y -> Matriz Y do plano da fonte (pós-deflexão)
    centro_x -> Coordenada X real da fonte
    centro_y -> Coordenada Y real da fonte
    sigman -> Tamanho da fonte
    return -> Matriz 2D com os valores de pixel (0 a intensidade_max)
    '''

    r_quadrado = (beta_x - centro_x) ** 2 + (beta_y - centro_y)**2

    # Predefine underflow em valores muito distantes do centro
    expoente = np.clip(-r_quadrado / (2 * sigma**2), -500, 0)

    intensidade = intensidade_max * np.exp(expoente)
    return intensidade.astype(np.uint8)