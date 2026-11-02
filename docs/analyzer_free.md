# Documentação do Módulo: `analyzer_free.py`

## Propósito
O módulo `analyzer_free.py` fornece uma ferramenta de análise heurística gratuita e local para identificar trechos de alto potencial de engajamento (potenciais cortes virais) em transcrições de vídeos. Ele opera inteiramente sem o uso de APIs pagas externas (como a da Anthropic/Claude), servindo como uma alternativa para testar o pipeline completo de corte e edição antes de migrar para análises baseadas em Inteligência Artificial.

---

## Como funciona
O módulo processa uma lista de segmentos de transcrição através de uma série de etapas heurísticas:

1. **Geração de Janelas (`_gerar_janelas`)**: Varre a transcrição simulando janelas de tempo com durações predefinidas (30s, 45s, 60s, 90s, 120s) a partir de cada ponto de início.
2. **Pontuação Heurística (`_pontuar_texto`)**: Cada janela candidata recebe uma nota baseada em:
   - Presença e posição de palavras-gancho (peso maior se estiverem na abertura do trecho).
   - Reações emotivas, marcadores de humor e alongamentos textuais (ex: *"gooool"*).
   - Sinais de pontuação de impacto (`!` e `?`) e presença de números/estatísticas.
   - Avaliação do início do trecho (penalizando frases "penduradas" ou sem contexto inicial e bonificando perguntas).
   - Avaliação do final do trecho (verificação se conclui uma ideia).
   - Densidade de fala (palavras por segundo) e penalização/bonificação baseada na faixa de duração.
3. **Filtragem e Seleção**: 
   - Ordena os trechos por pontuação e aplica um **piso relativo** (rejeitando trechos com menos de 35% da pontuação do melhor trecho encontrado).
   - Elimina janelas sobrepostas para evitar repetição de conteúdo.
   - Ordena os cortes finalistas em ordem cronológica.
4. **Geração de Metadados do Corte**: Extrai manchetes dinâmicas com base nas frases mais fortes do trecho, define títulos, calcula a pontuação arredondada e gera justificativas e metadados padrão para redes sociais.

---

## Dependências
- **Biblioteca padrão do Python**: Utiliza o módulo `re` para expressões regulares e manipulação de padrões textuais.
- **Integração no Projeto**: É consumido pelo módulo principal (`main.py`) de forma intercambiável com a versão baseada em IA (`analyzer.py`).

---

## Pontos de configuração (o que costuma mudar)
- `PALAVRAS_GANCHO`: Lista base de expressões e palavras em português que indicam momentos de atenção ou ganchos.
- `NICHOS`: Dicionário contendo palavras-chave específicas por nicho (ex: `"esporte"`, `"musica"`), acionadas via parâmetro `--nicho` na execução.
- `REACOES`: Expressões emotivas genéricas valorizadas durante a pontuação.
- `PISO_RELATIVO`: Constante numérica (`0.35`) que define a fração mínima da pontuação do melhor trecho necessária para que um candidato seja aceito.
- `DURACAO_MIN` / `DURACAO_MAX` / `DURACOES_ALVO`: Limites e janelas de tempo testadas para a duração dos cortes (padrão entre 30 e 120 segundos).

---

## Histórico de mudanças

| Data | Hash do commit | Autor | Descrição da mudança |
| :--- | :--- | :--- | :--- |
| Mon Nov 2 20:46:17 2026 -0300 | a8e2e9f | Gustavo Rockembach | alterações de legenda |