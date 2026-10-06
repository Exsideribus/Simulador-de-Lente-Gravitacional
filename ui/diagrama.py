import math
import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient
from PyQt6.QtWidgets import QSizePolicy, QWidget
from ui.tema import TEMA_AZUL


class DiagramaRaios(QWidget):
    """Esquema vetorial: todos os vértices vêm da geometria da simulação."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.geometria = None
        self.tema = TEMA_AZUL
        self.escala_transversal = 1.2e7
        self.setMinimumSize(320, 250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName("Diagrama interativo dos raios de luz")
        rng = np.random.default_rng(7)
        self.estrelas = rng.uniform((25, 25), (835, 535), (65, 2))

    def definir_tema(self, tema):
        self.tema = tema
        self.update()

    def atualizar(self, geometria):
        self.geometria = geometria
        pontos = geometria.raios.reshape(-1, 3)
        max_y = max(np.max(np.abs(pontos[:, 2] + 0.24 * pontos[:, 1])), 1e-12)
        max_x = max(np.max(np.abs(pontos[:, 1])), 1e-12)
        self.escala_transversal = min(1.2e7, 135 / max_y, 65 / (0.48 * max_x))
        self.update()

    def projetar(self, ponto):
        profundidade, x, y = ponto
        escala = self.escala_transversal
        return QPointF(85 + 660 * profundidade + 0.48 * escala * x,
                       285 - escala * (y + 0.24 * x))

    def brilho(self, p, centro, rx, ry, cor):
        p.save()
        p.translate(centro)
        p.scale(rx, ry)
        gradiente = QRadialGradient(QPointF(0, 0), 1)
        gradiente.setColorAt(0, QColor(cor[0], cor[1], cor[2], 230))
        gradiente.setColorAt(0.25, QColor(cor[0], cor[1], cor[2], 125))
        gradiente.setColorAt(1, QColor(cor[0], cor[1], cor[2], 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gradiente)
        p.drawEllipse(QPointF(0, 0), 1, 1)
        p.restore()

    def texto(self, p, x, y, largura, texto, cor=None, tamanho=13):
        p.setPen(QColor(cor or self.tema["texto"]))
        p.setFont(QFont("Sans Serif", tamanho))
        p.drawText(QRectF(x, y, largura, 48),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, texto)

    def seta(self, p, inicio, fim, cor):
        direcao = fim - inicio
        comprimento = math.hypot(direcao.x(), direcao.y())
        if comprimento < 1:
            return
        ux, uy = direcao.x() / comprimento, direcao.y() / comprimento
        centro = inicio + direcao * 0.62
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cor)
        p.drawPolygon(QPolygonF([
            centro + QPointF(ux * 5, uy * 5),
            centro + QPointF(-ux * 5 - uy * 3, -uy * 5 + ux * 3),
            centro + QPointF(-ux * 5 + uy * 3, -uy * 5 - ux * 3),
        ]))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(self.tema["diagrama"]))
        escala = min(self.width() / 860, self.height() / 560)
        p.translate((self.width() - 860 * escala) / 2, (self.height() - 560 * escala) / 2)
        p.scale(escala, escala)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(*self.tema["estrelas"], 65))
        for x, y in self.estrelas:
            p.drawEllipse(QPointF(x, y), 1, 1)
        g = self.geometria
        if g is None:
            return

        fonte = self.projetar((0, *g.fonte))
        lente = self.projetar((1 - g.fracao_lente, 0, 0))
        observador = self.projetar((1, *g.observador))
        p.setPen(QPen(QColor(self.tema["eixo"]), 1, Qt.PenStyle.DashLine))
        p.drawLine(QPointF(50, 285), QPointF(800, 285))
        p.drawLine(QPointF(lente.x(), 155), QPointF(lente.x(), 415))

        # Bordas de uma fonte extensa e raios centrais do mesmo modelo.
        for raio, central in zip(g.raios, g.centrais):
            pontos = [self.projetar(ponto) for ponto in raio]
            cor = QColor(*self.tema["raios"], 210 if central else 58)
            p.setPen(QPen(cor, 2.0 if central else 1.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPolyline(QPolygonF(pontos))
            if central:
                self.seta(p, pontos[0], pontos[1], cor)
                self.seta(p, pontos[1], pontos[2], cor)

        tamanho = 22 + g.sigma * 1.4e7
        self.brilho(p, fonte, tamanho * 0.46, tamanho, self.tema["fonte"])
        # Pequenos braços espirais vetoriais da fonte.
        p.setPen(QPen(QColor(*self.tema["espiral"], 180), 1.2))
        for fase in (0, math.pi):
            caminho = QPainterPath()
            for i, angulo in enumerate(np.linspace(0.2, 4 * math.pi, 90)):
                r = tamanho * 0.78 * angulo / (4 * math.pi)
                ponto = fonte + QPointF(0.42 * r * math.cos(angulo + fase),
                                       r * math.sin(angulo + fase))
                caminho.moveTo(ponto) if i == 0 else caminho.lineTo(ponto)
            p.drawPath(caminho)

        raio_lente = 28 + min(g.theta_e * 2.6e6, 50)
        self.brilho(p, lente, raio_lente * 0.65, raio_lente, self.tema["lente"])
        self.brilho(p, lente, 9, 13, self.tema["nucleo"])

        # O telescópio se desloca com o observador e aponta para a lente.
        p.save()
        p.translate(observador)
        angulo = math.degrees(math.atan2(lente.y() - observador.y(),
                                        lente.x() - observador.x())) - 180
        p.rotate(angulo)
        p.setPen(QPen(QColor(self.tema["contorno"]), 2))
        p.setBrush(QColor(self.tema["corpo"]))
        p.drawRoundedRect(QRectF(-14, -14, 42, 28), 5, 5)
        p.setBrush(QColor(self.tema["vidro"]))
        p.drawEllipse(QRectF(-20, -17, 13, 34))
        p.setBrush(QColor(self.tema["interior"]))
        p.drawEllipse(QRectF(-18, -12, 8, 24))
        p.setPen(QPen(QColor(self.tema["suporte"]), 3))
        p.drawLine(QPointF(12, 14), QPointF(4, 34))
        p.drawLine(QPointF(12, 14), QPointF(28, 34))
        p.restore()

        self.texto(p, 8, 66, 175, "GALÁXIA DISTANTE", self.tema["destaque"], 12)
        self.texto(p, lente.x() - 110, 66, 220, "GALÁXIA LENTE", self.tema["destaque"], 12)
        self.texto(p, 663, 66, 188, "OBSERVADOR", self.tema["destaque"], 12)
        self.texto(p, 8, 94, 175, "Fonte de luz", tamanho=11)
        self.texto(p, lente.x() - 100, 94, 200, "A gravidade desvia a luz", tamanho=11)
        self.texto(p, 663, 94, 188, "Telescópio", tamanho=11)
