"""Geometria de raios de uma lente pontual, em coordenadas comóveis."""
from dataclasses import dataclass
import numpy as np

KPC_EM_METROS = 3.08567758e19


def imagens_pontuais(beta, theta_e, amostras_anel=12):
    """Soluções de beta = theta - theta_E² theta/|theta|²."""
    beta = np.asarray(beta, dtype=float)
    modulo = np.linalg.norm(beta)
    if modulo < 1e-15:
        angulos = np.linspace(0, 2 * np.pi, amostras_anel, endpoint=False)
        return theta_e * np.column_stack((np.cos(angulos), np.sin(angulos)))
    raiz = np.sqrt(modulo**2 + 4 * theta_e**2)
    externo = (modulo + raiz) / 2
    interno = -2 * theta_e**2 / (modulo + raiz)
    return np.outer((externo, interno), beta / modulo)


@dataclass
class GeometriaRaios:
    beta_efetivo: np.ndarray
    fonte: np.ndarray
    observador: np.ndarray
    fracao_lente: float
    raios: np.ndarray
    centrais: np.ndarray
    sigma: float
    theta_e: float


def calcular_geometria(simulador, fonte_x, fonte_y, sigma, observador_x=0, observador_y=0):
    """Observador em kpc comóveis; posições da fonte em radianos.

    As distâncias comóveis garantem a mesma equação angular usada no
    ray tracing. Cada raio contém fonte, impacto na lente e observador:
    (profundidade, posição transversal X, posição transversal Y).
    A profundidade vale 0 na fonte e 1 no observador.
    """
    chi_l = simulador.Dl * (1 + simulador.z_l)
    chi_s = simulador.Ds * (1 + simulador.z_s)
    fracao = chi_l / chi_s
    fonte = np.array((fonte_x, fonte_y), dtype=float)
    observador = np.array((observador_x, observador_y)) * KPC_EM_METROS / chi_s
    paralaxe = observador * (1 / fracao - 1)
    beta_efetivo = fonte + paralaxe

    angulos = np.linspace(0, 2 * np.pi, 8, endpoint=False)
    borda = fonte + sigma * np.column_stack((np.cos(angulos), np.sin(angulos)))
    pontos = np.vstack((fonte, borda))
    raios, centrais = [], []
    for indice, ponto in enumerate(pontos):
        for theta in imagens_pontuais(ponto + paralaxe, simulador.theta_E):
            impacto = (1 - fracao) * observador + fracao * theta
            raios.append(((0, *ponto), (1 - fracao, *impacto), (1, *observador)))
            centrais.append(indice == 0)
    return GeometriaRaios(
        beta_efetivo, fonte, observador, fracao, np.asarray(raios),
        np.asarray(centrais), sigma, simulador.theta_E,
    )