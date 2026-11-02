"""
utils.py
Funções pequenas e utilitárias, reutilizadas por mais de um módulo do projeto.
"""
import re
import unicodedata


def slugificar(texto: str, tamanho_max: int = 60) -> str:
    """
    Converte um texto livre (ex: título de vídeo ou de corte) em um nome de
    pasta/arquivo seguro: minúsculas, sem acentos/símbolos, espaços viram hífen.
    Ex: "Título com Ação!" -> "titulo-com-acao"
    """
    texto = texto.strip().lower()
    # remove acentos (á -> a, ç -> c, ã -> a, etc.) em vez de simplesmente apagar a letra
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"\s+", "-", texto)
    texto = re.sub(r"-{2,}", "-", texto).strip("-")
    return texto[:tamanho_max] or "video"


def refinar_cortes(cortes: list, segmentos: list, tolerancia: float = 6.0,
                    folga_inicio: float = 0.2, folga_fim: float = 0.45,
                    duracao_min: float = 20.0, duracao_max: float = 130.0) -> list:
    """
    Ajusta o início/fim de cada corte para as fronteiras reais das frases da
    transcrição. Evita o defeito mais comum de cortes automáticos: começar no
    meio de uma palavra/frase ou terminar antes da piada/conclusão.

    - início: vai para o começo do segmento mais próximo (dentro da tolerância)
    - fim: vai para o final do segmento mais próximo (dentro da tolerância)
    - pequena folga antes/depois, para não "comer" a primeira/última sílaba
    Descarta cortes que ficarem fora da faixa de duração válida.
    """
    if not segmentos:
        return cortes

    refinados = []
    for c in cortes:
        ini, fim = c["inicio_seg"], c["fim_seg"]

        inicios = [s["inicio"] for s in segmentos if abs(s["inicio"] - ini) <= tolerancia]
        fins = [s["fim"] for s in segmentos if abs(s["fim"] - fim) <= tolerancia]
        if inicios:
            ini = min(inicios, key=lambda t: abs(t - ini))
        if fins:
            fim = min(fins, key=lambda t: abs(t - fim))

        ini = max(0.0, ini - folga_inicio)
        fim = fim + folga_fim

        if duracao_min <= (fim - ini) <= duracao_max:
            refinados.append({**c, "inicio_seg": ini, "fim_seg": fim})
        else:
            print(f"[AVISO] Corte descartado após ajuste de limites (duração {fim - ini:.0f}s): "
                  f"{c.get('titulo', '')}")
    return refinados
