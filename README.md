# Simulador de Lente Gravitacional

Simulador interativo em Python, PyQt6 e NumPy.

- **À esquerda:** imagem recebida pelo telescópio. O botão **Ver em infravermelho** alterna entre o anel azul e a intensidade na paleta inferno; o mesmo botão permite voltar.
- **À direita:** esquema em perspectiva da galáxia fonte, da lente, dos raios e do telescópio.
- **Controles:** posição e tamanho da fonte, massa da lente e posição transversal do observador.
- **Alinhar · formar anel:** centraliza fonte e observador, preservando a massa e a paleta selecionada.

As alterações atualizam a imagem e os raios juntos. A troca de paleta não modifica os parâmetros nem o campo de visão. O simulador inicia com os objetos alinhados.

## Modelo

A imagem usa a equação inversa da lente pontual. Os raios do esquema são as soluções analíticas dessa mesma equação para o centro e uma amostra do contorno da fonte. O observador se desloca em kpc comóveis; sua paralaxe altera a posição angular efetiva da fonte. As distâncias comóveis são calculadas a partir das distâncias de diâmetro angular e dos redshifts existentes.

O esquema amplia as direções transversais para tornar o desvio visível e ajusta essa ampliação quando necessário para manter os raios no painel. Cores, textura e luminosidade da galáxia central são ilustrativas. **Infravermelho** é o nome do modo de falsa cor solicitado: não há um modelo espectral de infravermelho.

## Executar

No ambiente Python com as dependências de `requeriments.txt` instaladas:

```sh
python main.py
```

No WSL com `DISPLAY` disponível, a inicialização prefere o backend X11 (`xcb`). Uma escolha explícita de `QT_QPA_PLATFORM` é preservada. Essa configuração não corrige falhas do serviço de exibição WSLg.

## Testes

```sh
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

Os testes verificam o raio do anel, as soluções da equação da lente, as conexões dos raios, a paralaxe, todos os controles, a alternância de paleta e a seleção do backend.