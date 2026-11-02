"""
analyzer_free.py
Versão GRATUITA do analisador — não usa nenhuma API paga. Identifica trechos
prováveis de viralizar usando heurísticas de texto sobre a transcrição:
palavras-gancho, pontuação de impacto, números/estatísticas, marcadores de
humor/surpresa e densidade de fala.

É bem menos preciso que a análise feita pelo Claude (analyzer.py), porque não
"entende" o conteúdo de verdade — só reconhece padrões de superfície no texto.
Serve para testar o pipeline todo sem custo, antes de migrar para a versão com IA.
"""
import re

# Palavras/expressões que costumam indicar um "gancho" ou pico de valor em PT-BR.
# Ajuste esta lista livremente conforme o nicho do canal.
PALAVRAS_GANCHO = [
    "você não vai acreditar", "ninguém te conta", "segredo", "verdade",
    "erro que", "isso mudou", "descobri", "aprendi", "grande sacada",
    "olha só", "presta atenção", "atenção", "importante", "cuidado",
    "a real é", "juro", "sério", "inacreditável", "impressionante",
    "revelou", "revelação", "chocante", "polêmico", "polêmica", "controverso",
    "dica", "truque", "método", "passo a passo", "nunca",
    "ninguém fala", "pouca gente sabe", "número", "estatística", "dados mostram",
    "por que", "como assim", "resultado", "consegui", "mudou minha vida",
]

MARCADORES_HUMOR = ["kkk", "haha", "rs ", " rs", "engraçado", "hilário", "morri"]

# Palavras extras por nicho (use --nicho no main.py). "geral" usa só a lista acima.
NICHOS = {
    "geral": [],
    "esporte": [
        "golaço", "que lance", "pênalti", "expulso", "expulsão", "virada", "decisão",
        "campeão", "título", "absurdo", "bizarro", "impossível", "olha isso", "meu deus",
        "tá louco", "acabou", "var", "polêmica", "assistência", "goleada", "goleado",
        "defesa", "milagre", "falha", "erro", "craque", "show",
    ],
    "musica": [
        "riff", "solo", "show", "turnê", "banda", "álbum", "palco", "guitarra",
        "bateria", "ao vivo", "clássico", "lenda", "briga", "separou", "polêmica",
        "história", "bastidor", "gravação", "primeira vez", "nunca contei",
    ],
}

# Reações emotivas genéricas (valem para qualquer nicho)
REACOES = ["meu deus", "caramba", "nossa", "absurdo", "loucura", "incrível", "inacreditável",
           "não acredito", "como assim", "olha isso", "que isso", "acabou", "surreal"]

# Alongamentos típicos de emoção: "gooool", "nããão", "puuutz"
ALONGAMENTO = re.compile(r"(\w)\1{2,}", re.IGNORECASE)

# Frases que começam "no meio de um pensamento" -> corte fraco (falta contexto)
ABERTURAS_FRACAS = ("e ", "mas ", "então ", "aí ", "porque ", "que ", "tipo ", "né ", "assim ",
                    "ou ", "só que ", "daí ")

PONTUACAO_IMPACTO = re.compile(r"[!?]")
NUMEROS = re.compile(r"\b\d+([.,]\d+)?\s*(%|por cento|mil|milh(ão|ões)|reais|r\$)?\b", re.IGNORECASE)

PISO_RELATIVO = 0.35   # fração mínima da nota do melhor trecho
DURACAO_MIN = 30
DURACAO_MAX = 120
DURACOES_ALVO = [30, 45, 60, 90, 120]  # janelas testadas a partir de cada ponto de início


def _pontuar_texto(texto: str, duracao: float = 45.0, nicho: str = "geral") -> float:
    """
    Pontuação heurística de um trecho (quanto maior, mais promissor). Considera:
      - palavras-gancho (peso maior se estiverem na ABERTURA, onde prendem de verdade)
      - reações emotivas, humor, exclamações, perguntas, números, alongamentos ("gooool")
      - começo forte (pergunta/gancho) x começo fraco (continuação de frase)
      - final com pontuação conclusiva (termina a ideia)
      - densidade de fala (trechos com pouca fala costumam ser parados/musicais)
      - duração: cortes de 30-60s retêm melhor que os de 2 minutos
    """
    texto_lower = texto.lower()
    palavras_lista = texto_lower.split()
    abertura = " ".join(palavras_lista[:10])
    listas = PALAVRAS_GANCHO + NICHOS.get(nicho, [])

    pontos = 0.0

    for palavra in listas:
        if palavra in abertura:
            pontos += 4.0
        elif palavra in texto_lower:
            pontos += 1.0

    for reacao in REACOES:
        if reacao in texto_lower:
            pontos += 1.2

    for marcador in MARCADORES_HUMOR:
        if marcador in texto_lower:
            pontos += 1.5

    pontos += len(ALONGAMENTO.findall(texto)) * 1.0
    pontos += texto.count("!") * 0.6
    pontos += texto.count("?") * 0.5
    pontos += len(NUMEROS.findall(texto)) * 1.0

    # começo: pergunta logo de cara é gancho; começo "pendurado" é penalizado
    primeira_frase = re.split(r"(?<=[.!?])\s+", texto.strip())[0] if texto.strip() else ""
    if primeira_frase.endswith("?"):
        pontos += 3.0
    if texto_lower.startswith(ABERTURAS_FRACAS):
        pontos -= 3.0

    # final: termina a ideia?
    pontos += 2.0 if texto.strip().endswith((".", "!", "?")) else -2.0

    # normaliza pelo tamanho (raiz) para não favorecer só trechos longos
    palavras_totais = max(len(palavras_lista), 1)
    pontos = pontos / (palavras_totais ** 0.35)

    # densidade de fala (palavras por segundo): muito baixa = trecho parado
    densidade = palavras_totais / max(duracao, 1.0)
    if densidade < 1.2:
        pontos *= 0.6
    elif densidade > 2.0:
        pontos *= 1.1

    # duração ideal
    if duracao <= 60:
        pontos *= 1.15
    elif duracao > 90:
        pontos *= 0.8

    return pontos


def _gerar_janelas(segmentos: list, nicho: str = "geral") -> list:
    """
    Gera janelas candidatas (início, fim, texto, pontuação) percorrendo os
    segmentos da transcrição e testando durações de 30s a 120s a partir de
    cada ponto de início.
    """
    janelas = []
    n = len(segmentos)

    for i in range(n):
        inicio = segmentos[i]["inicio"]
        for duracao_alvo in DURACOES_ALVO:
            fim_alvo = inicio + duracao_alvo
            j = i
            texto_partes = []
            while j < n and segmentos[j]["inicio"] < fim_alvo:
                texto_partes.append(segmentos[j]["texto"])
                j += 1
            if j == i:
                continue
            fim_real = segmentos[j - 1]["fim"]
            duracao_real = fim_real - inicio
            if duracao_real < DURACAO_MIN or duracao_real > DURACAO_MAX:
                continue

            texto = " ".join(texto_partes).strip()
            if not texto:
                continue

            pontuacao = _pontuar_texto(texto, duracao_real, nicho)
            janelas.append({
                "inicio_seg": inicio,
                "fim_seg": fim_real,
                "texto": texto,
                "pontuacao": pontuacao,
            })

    return janelas


def _sobrepoe(a: dict, b: dict, margem: float = 5.0) -> bool:
    return not (a["fim_seg"] + margem <= b["inicio_seg"] or b["fim_seg"] + margem <= a["inicio_seg"])


def _frases(texto: str) -> list:
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+", texto.strip()) if f.strip()]


def _pontuar_frase(frase: str, nicho: str) -> float:
    f = frase.lower()
    pts = sum(2.0 for w in PALAVRAS_GANCHO + NICHOS.get(nicho, []) if w in f)
    pts += sum(1.5 for r in REACOES if r in f)
    pts += frase.count("!") * 1.0 + frase.count("?") * 1.0
    pts += len(NUMEROS.findall(frase)) * 1.0
    pts += len(ALONGAMENTO.findall(frase)) * 1.0
    n = len(f.split())
    if n < 3:
        pts -= 3          # frase curta demais não vira manchete
    if n > 14:
        pts -= (n - 14) * 0.5
    return pts


def _manchete_a_partir_do_texto(texto: str, nicho: str = "geral", max_palavras: int = 9) -> str:
    """
    Escolhe a frase mais forte do trecho (não necessariamente a primeira) e
    encurta para caber bem na faixa de abertura.
    """
    frases = _frases(texto) or [texto]
    # prefere frases da primeira metade do trecho (manchete deve antecipar, não spoilar o final)
    metade = max(len(frases) // 2 + 1, 1)
    candidatas = frases[:metade]
    melhor = max(candidatas, key=lambda f: _pontuar_frase(f, nicho))
    palavras = melhor.split()
    if len(palavras) > 12:           # frases até 12 palavras entram inteiras
        palavras = palavras[:max_palavras]
        # não termina em palavra de ligação/número solto ("de", "aos", "47"...)
        while len(palavras) > 4 and (len(palavras[-1]) <= 3 or palavras[-1].isdigit()):
            palavras.pop()
        manchete = " ".join(palavras).rstrip(",;:") + "..."
    else:
        manchete = " ".join(palavras).rstrip(",;:")
    return manchete.strip(" .") if not manchete.endswith(("...", "!", "?")) else manchete


def _titulo_a_partir_do_texto(texto: str) -> str:
    palavras = texto.strip().split()
    titulo = " ".join(palavras[:8])
    if len(palavras) > 8:
        titulo += "..."
    return titulo.capitalize()


def _gancho_a_partir_do_texto(texto: str) -> str:
    """Primeira frase falada do trecho (o que é dito nos primeiros segundos)."""
    partes = re.split(r"(?<=[.!?])\s+", texto.strip())
    return partes[0] if partes else texto[:80]


def analisar_transcricao_local(segmentos: list, quantidade_cortes: int = 6,
                                nicho: str = "geral") -> list:
    """
    Versão gratuita: não chama nenhuma API. Retorna a mesma estrutura que a
    versão com Claude (analyzer.py), para ser usada de forma intercambiável
    no main.py.
    """
    print(f"[..] Analisando trechos localmente (modo GRATUITO, sem API, nicho: {nicho})...")

    janelas = _gerar_janelas(segmentos, nicho)
    if not janelas:
        print("[AVISO] Nenhuma janela candidata encontrada (vídeo muito curto?).")
        return []

    janelas.sort(key=lambda w: w["pontuacao"], reverse=True)

    # Só aceita trechos com pelo menos 35% da pontuação do melhor: é melhor gerar
    # menos cortes do que completar a cota com trechos mornos.
    piso = janelas[0]["pontuacao"] * PISO_RELATIVO
    escolhidas = []
    for janela in janelas:
        if janela["pontuacao"] < piso:
            break
        if any(_sobrepoe(janela, e) for e in escolhidas):
            continue
        escolhidas.append(janela)
        if len(escolhidas) >= quantidade_cortes:
            break

    # ordena por ordem cronológica no vídeo final, fica mais fácil de revisar
    escolhidas.sort(key=lambda w: w["inicio_seg"])

    cortes = []
    for e in escolhidas:
        manchete = _manchete_a_partir_do_texto(e["texto"], nicho)
        cortes.append({
            "inicio_seg": e["inicio_seg"],
            "fim_seg": e["fim_seg"],
            "titulo": manchete.capitalize() or _titulo_a_partir_do_texto(e["texto"]),
            "manchete": manchete,
            "pontuacao": round(e["pontuacao"], 2),
            "motivo": (
                f"Selecionado por heurística local (pontuação {e['pontuacao']:.2f}) — "
                "detectou palavras-gancho, pontuação de impacto e/ou números no trecho."
            ),
            "gancho": _gancho_a_partir_do_texto(e["texto"]),
            "plataformas": ["tiktok", "instagram", "shorts"],
        })

    print(f"[OK] {len(cortes)} cortes identificados (modo gratuito).")
    return cortes
