"""
captions.py
Gera legendas no formato .ass (Advanced SubStation Alpha) para os cortes:

  1. Faixa de abertura ("manchete no rodapé"): uma faixa vermelha sólida,
     largura total da tela, com uma manchete curta, fixa nos primeiros segundos
     do clipe. Funciona como uma "capa" que prende atenção mesmo com o som
     desligado. O retângulo vermelho é desenhado pelo cutter.py via ffmpeg;
     aqui só geramos o texto por cima dele. O tamanho da fonte se ajusta
     sozinho ao tamanho da manchete (curta = letra grande, longa = menor).
  2. Legenda dinâmica palavra-a-palavra, com a palavra falada no momento
     destacada em outra cor. Só aparece DEPOIS que a faixa de abertura sai.
  3. Handle da conta (@usuario): texto pequeno, no canto superior direito,
     logo abaixo da logo do canal (que é desenhada pelo cutter.py).

FONTES: os arquivos .ttf ficam em assets/fonts/ e são passados ao ffmpeg
(fontsdir), então NÃO precisam estar instalados no Windows. Sem isso o ffmpeg
troca silenciosamente a fonte por uma genérica e o visual perde o impacto.

ESTILOS: escolha com --estilo no main.py (impacto, moderno, comic). Para
criar o seu, copie um bloco de ESTILOS e ajuste.
"""
import os
import textwrap

PASTA_FONTES_PADRAO = os.path.join("assets", "fonts")

# --- Presets de estilo --------------------------------------------------------
# Cores em formato ASS: &HAABBGGRR (AA=00 opaco). Ex: amarelo = &H0000F0FF
ESTILOS = {
    # Condensada e pesada, estilo "corte de podcast / esporte". Letra bem grande.
    "impacto": dict(
        fonte="Anton", negrito=0, tamanho=150,
        cor_texto="&H00FFFFFF", cor_destaque="&H0000F0FF", cor_borda="&H00000000",
        borda=9, sombra=4, escala_ativa=112, margem_inferior=400,
        max_palavras=3, ratio_largura=0.416,
        rodape_fonte="Anton", rodape_negrito=0, rodape_tamanho_max=135, rodape_tamanho_min=70,
        rodape_borda=4,
    ),
    # Larga e arredondada, limpa e moderna. Destaque em verde-limão.
    "moderno": dict(
        fonte="Poppins Black", negrito=0, tamanho=118,
        cor_texto="&H00FFFFFF", cor_destaque="&H0000FF9C", cor_borda="&H00000000",
        borda=8, sombra=3, escala_ativa=100, margem_inferior=400,
        max_palavras=3, ratio_largura=0.583,
        rodape_fonte="Poppins Black", rodape_negrito=0, rodape_tamanho_max=88, rodape_tamanho_min=52,
        rodape_borda=4,
    ),
    # Divertida, estilo quadrinhos. Boa para humor, reação e esporte.
    "comic": dict(
        fonte="Bangers", negrito=0, tamanho=135,
        cor_texto="&H00FFFFFF", cor_destaque="&H003C9BFF", cor_borda="&H00000000",
        borda=9, sombra=4, escala_ativa=112, margem_inferior=400,
        max_palavras=3, ratio_largura=0.369,
        rodape_fonte="Bangers", rodape_negrito=0, rodape_tamanho_max=130, rodape_tamanho_min=70,
        rodape_borda=4,
    ),
}
ESTILO_PADRAO = "impacto"

DURACAO_MAX_BLOCO = 3.2        # segundos

# --- Faixa de abertura (rodapé) ----------------------------------------------
RODAPE_COR_TEXTO = "&H00FFFFFF"
RODAPE_COR_BORDA = "&H00000000"
RODAPE_MARGEM_LATERAL = 55
RODAPE_DURACAO = 3.2                   # segundos que a faixa fica na tela
ALTURA_FAIXA_PADRAO = 220              # deve bater com ALTURA_FAIXA_RODAPE no cutter.py
RODAPE_FATOR_LINHA = 1.05              # espaço ocupado por linha, em múltiplos do tamanho da fonte

# --- Handle da conta (@usuario) ----------------------------------------------
HANDLE_FONTE = "Arial Black"
HANDLE_TAMANHO_FONTE = 34
HANDLE_COR_TEXTO = "&H55FFFFFF"     # branco, mais apagado (00=opaco, FF=invisível)
HANDLE_COR_BORDA = "&H60000000"
HANDLE_ESPESSURA_BORDA = 3
LOGO_LARGURA_PROPORCAO = 0.19       # deve bater com LARGURA_LOGO_PROPORCAO no cutter.py
LOGO_MARGEM = 28                    # deve bater com MARGEM_LOGO no cutter.py
HANDLE_GAP_ABAIXO_LOGO = 16


def obter_estilo(nome: str) -> dict:
    return ESTILOS.get((nome or ESTILO_PADRAO).lower(), ESTILOS[ESTILO_PADRAO])


def calcular_duracao_rodape(duracao_corte: float, tem_rodape: bool) -> float:
    """Quanto tempo a faixa de abertura fica na tela (0 se não houver manchete)."""
    if not tem_rodape:
        return 0.0
    return min(RODAPE_DURACAO, duracao_corte)


def _formatar_tempo_ass(segundos: float) -> str:
    if segundos < 0:
        segundos = 0
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = segundos % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _agrupar_palavras(palavras: list, max_palavras: int) -> list:
    """Agrupa palavras em pequenos blocos (2-3 palavras) para exibir por vez na tela.
    Também fecha o bloco quando a palavra termina uma frase (. ! ?), para a
    legenda não misturar o fim de uma frase com o começo da próxima."""
    blocos = []
    bloco_atual = []
    inicio_bloco = None

    for p in palavras:
        if not bloco_atual:
            bloco_atual = [p]
            inicio_bloco = p["inicio"]
            continue

        duracao_se_adicionar = p["fim"] - inicio_bloco
        anterior_fechou_frase = bloco_atual[-1]["palavra"].rstrip().endswith((".", "!", "?"))
        if (len(bloco_atual) >= max_palavras or duracao_se_adicionar > DURACAO_MAX_BLOCO
                or anterior_fechou_frase):
            blocos.append(bloco_atual)
            bloco_atual = [p]
            inicio_bloco = p["inicio"]
        else:
            bloco_atual.append(p)

    if bloco_atual:
        blocos.append(bloco_atual)

    return blocos


def _limpar_palavra(p: str) -> str:
    """Caixa alta, sem pontuação de frase (legenda de corte fica mais limpa sem
    vírgulas e pontos soltos). Mantém ! e ? porque dão ênfase."""
    p = p.strip().upper()
    return p.strip(".,;:…\"“”").replace("{", "(").replace("}", ")")


def _texto_do_bloco(bloco: list, indice_ativo: int, est: dict) -> str:
    partes = []
    esc = est["escala_ativa"]
    for i, p in enumerate(bloco):
        palavra = _limpar_palavra(p["palavra"])
        if not palavra:
            continue
        if i == indice_ativo:
            partes.append(
                f"{{\\c{est['cor_destaque']}&\\fscx{esc}\\fscy{esc}}}"
                f"{palavra}"
                f"{{\\c{est['cor_texto']}&\\fscx100\\fscy100}}"
            )
        else:
            partes.append(palavra)
    return " ".join(partes)


def _escapar_texto_ass(texto: str) -> str:
    return texto.replace("{", "(").replace("}", ")")


def _quebrar_balanceado(texto: str, chars_por_linha: int) -> list:
    """Quebra em até 2 linhas de tamanho parecido (evita 'E' ou 'DE' soltos no fim da linha)."""
    palavras = texto.split()
    if len(texto) <= chars_por_linha or len(palavras) < 2:
        return textwrap.wrap(texto, width=chars_por_linha) or [texto]
    melhor, menor_dif = None, None
    for i in range(1, len(palavras)):
        a, b = " ".join(palavras[:i]), " ".join(palavras[i:])
        if len(a) > chars_por_linha or len(b) > chars_por_linha:
            continue
        # não termina a 1ª linha em palavra curta ("E", "DE", "O"...)
        penal = 6 if len(palavras[i - 1]) <= 2 else 0
        dif = abs(len(a) - len(b)) + penal
        if menor_dif is None or dif < menor_dif:
            melhor, menor_dif = [a, b], dif
    return melhor or textwrap.wrap(texto, width=chars_por_linha)


def _ajustar_manchete(texto: str, est: dict, largura: int, altura_faixa: int):
    """
    Escolhe o MAIOR tamanho de fonte em que a manchete cabe na faixa (em até 2
    linhas). Manchete curta -> letra grande; longa -> letra menor.
    Retorna (texto_com_quebras_ass, tamanho_da_fonte).
    """
    texto = _escapar_texto_ass(texto.strip().upper())
    largura_util = largura - 2 * RODAPE_MARGEM_LATERAL
    altura_util = altura_faixa - 24
    tam_max, tam_min = est["rodape_tamanho_max"], est["rodape_tamanho_min"]

    for tam in range(tam_max, tam_min - 1, -4):
        chars_por_linha = max(int(largura_util / (tam * est["ratio_largura"])), 6)
        linhas = _quebrar_balanceado(texto, chars_por_linha)
        if len(linhas) <= 2 and len(linhas) * tam * RODAPE_FATOR_LINHA <= altura_util:
            return "\\N".join(linhas), tam

    # não coube nem no menor tamanho: usa o menor e corta com reticências
    chars_por_linha = max(int(largura_util / (tam_min * est["ratio_largura"])), 6)
    linhas = textwrap.wrap(texto, width=chars_por_linha, max_lines=2, placeholder="...")
    return "\\N".join(linhas), tam_min


def gerar_ass_para_corte(palavras: list, inicio_corte: float, fim_corte: float,
                          caminho_saida: str, largura: int = 1080, altura: int = 1920,
                          texto_headline: str = None, texto_handle: str = None,
                          margem_rodape_extra: int = 0, estilo: str = ESTILO_PADRAO,
                          altura_faixa: int = ALTURA_FAIXA_PADRAO):
    """
    Filtra as palavras dentro da janela [inicio_corte, fim_corte], desloca os
    timestamps para começar em 0 (tempo relativo ao clipe) e escreve um .ass com:
      - o texto da faixa de abertura (manchete), se `texto_headline` for informado
      - a legenda dinâmica, palavra a palavra — só a partir do fim da faixa
      - o handle da conta (@usuario), se `texto_handle` for informado

    margem_rodape_extra: distância entre a base do quadro e a base da faixa
        vermelha (0 no layout "preenchido"; maior que 0 no "blur").
    estilo: nome de um preset de ESTILOS.

    Retorna o caminho do arquivo gerado, ou None se não havia nada pra mostrar.
    """
    est = obter_estilo(estilo)
    duracao_corte = fim_corte - inicio_corte
    duracao_rodape = calcular_duracao_rodape(duracao_corte, bool(texto_headline))

    margem_superior_handle = int(largura * LOGO_LARGURA_PROPORCAO) + LOGO_MARGEM + HANDLE_GAP_ABAIXO_LOGO

    palavras_do_corte = [
        {"inicio": p["inicio"] - inicio_corte, "fim": p["fim"] - inicio_corte, "palavra": p["palavra"]}
        for p in palavras
        if p["inicio"] >= inicio_corte and p["fim"] <= fim_corte + 0.05
        and (p["inicio"] - inicio_corte) >= duracao_rodape
    ]

    if not palavras_do_corte and not texto_headline and not texto_handle:
        return None

    cabecalho = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {largura}
PlayResY: {altura}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Legenda,{est['fonte']},{est['tamanho']},{est['cor_texto']},{est['cor_destaque']},{est['cor_borda']},&H80000000,{est['negrito'] and -1 or 0},0,0,0,100,100,1,0,1,{est['borda']},{est['sombra']},2,60,60,{est['margem_inferior']},1
Style: Rodape,{est['rodape_fonte']},{est['rodape_tamanho_max']},{RODAPE_COR_TEXTO},{RODAPE_COR_TEXTO},{RODAPE_COR_BORDA},&H00000000,{est['rodape_negrito'] and -1 or 0},0,0,0,100,100,1,0,1,{est['rodape_borda']},0,5,{RODAPE_MARGEM_LATERAL},{RODAPE_MARGEM_LATERAL},0,1
Style: Handle,{HANDLE_FONTE},{HANDLE_TAMANHO_FONTE},{HANDLE_COR_TEXTO},{HANDLE_COR_TEXTO},{HANDLE_COR_BORDA},&H00000000,-1,0,0,0,100,100,0,0,1,{HANDLE_ESPESSURA_BORDA},0,9,{LOGO_MARGEM},{LOGO_MARGEM},{margem_superior_handle},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    linhas_eventos = []

    # --- Manchete da faixa de abertura (a faixa vermelha vem do cutter.py) ---
    if texto_headline and duracao_rodape > 0:
        texto_formatado, tam = _ajustar_manchete(texto_headline, est, largura, altura_faixa)
        # \an5 + \pos: centraliza o bloco de texto exatamente no meio da faixa
        y_centro = altura - max(margem_rodape_extra, 0) - altura_faixa // 2
        linhas_eventos.append(
            f"Dialogue: 1,{_formatar_tempo_ass(0)},{_formatar_tempo_ass(duracao_rodape)},"
            f"Rodape,,0,0,0,,{{\\an5\\pos({largura // 2},{y_centro})\\fs{tam}}}{texto_formatado}"
        )

    # --- Handle da conta (canto superior direito, do início ao fim do clipe) ---
    if texto_handle:
        texto_formatado = _escapar_texto_ass(texto_handle.strip())
        linhas_eventos.append(
            f"Dialogue: 1,{_formatar_tempo_ass(0)},{_formatar_tempo_ass(duracao_corte)},"
            f"Handle,,0,0,0,,{texto_formatado}"
        )

    # --- Legenda dinâmica palavra-a-palavra (a partir do fim da faixa) ---
    blocos = _agrupar_palavras(palavras_do_corte, est["max_palavras"])
    for bloco in blocos:
        for i, palavra_ativa in enumerate(bloco):
            inicio_evento = palavra_ativa["inicio"]
            fim_evento = bloco[i + 1]["inicio"] if i + 1 < len(bloco) else palavra_ativa["fim"]
            if fim_evento <= inicio_evento:
                fim_evento = inicio_evento + 0.1
            texto = _texto_do_bloco(bloco, i, est)
            if not texto:
                continue
            linhas_eventos.append(
                f"Dialogue: 0,{_formatar_tempo_ass(inicio_evento)},{_formatar_tempo_ass(fim_evento)},"
                f"Legenda,,0,0,0,,{texto}"
            )

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(cabecalho)
        f.write("\n".join(linhas_eventos))

    return caminho_saida


def escapar_caminho_ffmpeg(caminho: str) -> str:
    """
    Formata um caminho de arquivo para uso dentro de um filtro do ffmpeg
    (filtergraph), que exige barras normais e escapa os dois-pontos do
    caminho (problema comum no Windows, ex: C:\\pasta\\arquivo.ass).
    """
    caminho_abs = os.path.abspath(caminho)
    caminho_abs = caminho_abs.replace("\\", "/")
    caminho_abs = caminho_abs.replace(":", "\\:")
    return caminho_abs
