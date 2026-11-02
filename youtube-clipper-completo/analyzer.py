"""
analyzer.py
Envia a transcrição (com timestamps) para o Claude analisar estrategicamente
e devolver os melhores trechos para cortes de redes sociais.
"""
import os
import json
import re
from anthropic import Anthropic

# Pode trocar sem mexer no código: defina a variável de ambiente ANTHROPIC_MODEL
MODELO_CLAUDE = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

PROMPT_SISTEMA = """Você é um editor sênior de cortes virais para TikTok, Instagram Reels e \
YouTube Shorts. Você recebe a transcrição de um vídeo longo (com o minuto:segundo em que cada \
frase COMEÇA) e escolhe os trechos que mais provavelmente vão ser assistidos até o fim, \
compartilhados e comentados.

O que faz um corte render:
- ABERTURA: os primeiros 3 segundos precisam prender. Comece NO INÍCIO de uma frase forte \
(pergunta, afirmação ousada, promessa, momento de tensão). Nunca comece em "e", "mas", "então", \
"aí", em saudações, apresentações, introduções ou propaganda.
- AUTONOMIA: o trecho faz sentido sozinho, sem o resto do vídeo.
- PICO: tem um momento claro de payoff (humor, revelação, dado surpreendente, reação forte, \
virada, opinião polêmica, história emocional, conselho prático).
- FINAL: termina logo após o payoff, em uma frase completa. Não arraste o final com conversa \
morna; corte onde a emoção está no auge.
- DURAÇÃO: prefira 30 a 60 segundos (cortes curtos retêm mais). Use até 90 segundos só quando a \
história realmente precisar. Nunca menos de 25 nem mais de 120.
- VARIEDADE: escolha trechos de partes diferentes do vídeo e de tipos diferentes de momento.
- Seja seletivo: é melhor devolver menos cortes bons do que completar a quantidade com trechos \
fracos.

Para cada corte, escreva também:
- "manchete": texto curto (3 a 8 palavras) que aparece em letras grandes nos primeiros segundos \
do vídeo. Deve criar curiosidade ou tensão SEM mentir e SEM entregar o final. Estilo de manchete \
de portal esportivo/entretenimento. Em português, sem emojis, sem aspas.
- "pontuacao": nota de 1 a 10 do potencial viral.

Use os timestamps exatamente como aparecem na transcrição (o início de uma frase para "inicio"; \
o início da ÚLTIMA frase do corte para "fim", e o sistema ajusta o final dela).

Responda APENAS com um JSON válido (sem markdown, sem texto antes ou depois), no formato:
{
  "cortes": [
    {
      "inicio": "MM:SS",
      "fim": "MM:SS",
      "titulo": "título curto para o nome do arquivo",
      "manchete": "MANCHETE CURTA E CHAMATIVA",
      "motivo": "por que esse trecho tem potencial viral (1-2 frases)",
      "gancho": "a frase exata falada nos primeiros segundos",
      "pontuacao": 8,
      "plataformas_sugeridas": ["tiktok", "instagram", "shorts"]
    }
  ]
}
"""


def _mmss_para_segundos(t: str) -> float:
    partes = t.strip().split(":")
    partes = [float(p) for p in partes]
    while len(partes) < 3:
        partes.insert(0, 0)
    h, m, s = partes
    return h * 3600 + m * 60 + s


def analisar_transcricao(transcricao_formatada: str, quantidade_cortes: int = 6,
                          nicho: str = "") -> list:
    """
    Chama a API da Anthropic para identificar os melhores trechos.
    Retorna lista de dicts: inicio_seg, fim_seg, titulo, motivo, gancho, plataformas.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Defina a variável de ambiente ANTHROPIC_API_KEY com sua chave da API da Anthropic."
        )

    client = Anthropic(api_key=api_key)

    contexto_nicho = f"Contexto do canal/assunto: {nicho}. Escolha momentos que o público desse nicho mais valoriza.\n\n" if nicho else ""
    prompt_usuario = f"""Aqui está a transcrição do vídeo com timestamps:

{transcricao_formatada}

{contexto_nicho}Identifique até {quantidade_cortes} melhores trechos para cortes virais, seguindo os \
critérios do sistema. Priorize qualidade e variedade; devolva menos que {quantidade_cortes} se não \
houver trechos realmente fortes."""

    resposta = client.messages.create(
        model=MODELO_CLAUDE,
        max_tokens=6000,
        system=PROMPT_SISTEMA,
        messages=[{"role": "user", "content": prompt_usuario}],
    )

    texto = "".join(bloco.text for bloco in resposta.content if bloco.type == "text")

    # Remove possíveis cercas de markdown, por segurança
    texto = re.sub(r"^```json\s*|\s*```$", "", texto.strip())

    dados = json.loads(texto)
    cortes = []
    for c in dados.get("cortes", []):
        inicio_seg = _mmss_para_segundos(c["inicio"])
        fim_seg = _mmss_para_segundos(c["fim"])
        duracao = fim_seg - inicio_seg
        if duracao < 15 or duracao > 140:
            # descarta cortes fora da faixa pedida (com pequena margem)
            continue
        cortes.append({
            "inicio_seg": inicio_seg,
            "fim_seg": fim_seg,
            "titulo": c.get("titulo", "corte"),
            "manchete": c.get("manchete", "") or c.get("gancho", ""),
            "pontuacao": c.get("pontuacao", 0),
            "motivo": c.get("motivo", ""),
            "gancho": c.get("gancho", ""),
            "plataformas": c.get("plataformas_sugeridas", ["tiktok", "instagram", "shorts"]),
        })

    cortes.sort(key=lambda c: c["pontuacao"], reverse=True)
    cortes = cortes[:quantidade_cortes]
    cortes.sort(key=lambda c: c["inicio_seg"])
    print(f"[OK] {len(cortes)} cortes identificados pela análise estratégica.")
    return cortes
