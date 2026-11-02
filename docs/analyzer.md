# Documentação do Módulo: `analyzer.py`

## Propósito
Este módulo é responsável por interagir com a API da Anthropic para analisar transcrições de vídeos longos (acompanhadas de timestamps) e identificar estrategicamente os melhores trechos para a criação de cortes virais voltados a plataformas como TikTok, Instagram Reels e YouTube Shorts.

## Como funciona
1. **Configuração do Cliente**: Verifica a presença da chave de API da Anthropic nas variáveis de ambiente (`ANTHROPIC_API_KEY`) e instancia o cliente oficial da biblioteca `anthropic`.
2. **Definição de Diretrizes (Prompt do Sistema)**: Utiliza um prompt estruturado que define o papel de um editor sênior de cortes virais. O prompt estabelece critérios rigorosos de seleção focados em abertura forte, autonomia do trecho, presença de payoff, duração ideal, variedade e seletividade.
3. **Envio da Transcrição**: A função principal `analisar_transcricao` recebe a transcrição formatada e opcionalmente um parâmetro de nicho. Ela monta a mensagem para o modelo considerando o contexto do canal e envia a requisição utilizando o modelo Claude configurado.
4. **Processamento da Resposta**: O texto retornado pelo modelo (esperado em formato JSON) é limpo de eventuais marcações de markdown e decodificado.
5. **Filtragem e Ordenação**: 
   - Converte os timestamps (`MM:SS`) em segundos.
   - Aplica uma validação de duração (descartando cortes menores que 15 segundos ou maiores que 140 segundos).
   - Extrai metadados como título, manchete, pontuação de viralização, motivo e gancho.
   - Ordena os cortes por pontuação de potencial viral (decrescente), limita a quantidade solicitada e reordena cronologicamente pelo tempo de início antes de retorná-los.

## Dependências
- `os`: Para acesso a variáveis de ambiente.
- `json`: Para manipulação e decodificação do JSON retornado pela API.
- `re`: Para limpeza de strings e remoção de marcações de markdown na resposta do modelo.
- `anthropic`: Biblioteca oficial da Anthropic para comunicação com o Claude.

## Pontos de configuração (o que costuma mudar)
- **`MODELO_CLAUDE`**: Define qual modelo do Claude será utilizado. É configurado prioritariamente pela variável de ambiente `ANTHROPIC_MODEL`, possuindo como padrão atual `"claude-sonnet-5-5"`.
- **`PROMPT_SISTEMA`**: As instruções e critérios de corte fornecidos ao modelo, que podem ser ajustados para refinar o comportamento de seleção, foco de retenção ou formato de saída esperado.
- **`max_tokens`**: O limite de tokens na chamada da API (`client.messages.create`), atualmente ajustado para `6000` para suportar respostas detalhadas.
- **Filtro de Duração**: Os limites de tempo (mínimo de 15 segundos e máximo de 140 segundos) aplicados na validação dos trechos retornados.

## Histórico de mudanças

| Data | Hash do commit | Autor | Descrição da alteração |
| :--- | :--- | :--- | :--- |
| Mon Nov 2 20:46:17 2026 -0300 | a8e2e9f | Gustavo Rockembach | Atualização das diretrizes e prompt do sistema para análise de legendas, inclusão opcional de nicho, adição dos campos 'manchete' e 'pontuacao', ajuste do modelo Claude para 'claude-sonnet-5-5' (com suporte à variável de ambiente `ANTHROPIC_MODEL`) e ordenação inteligente dos cortes por potencial viral. |