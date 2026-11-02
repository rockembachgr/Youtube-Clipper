# Documentação do Módulo: `youtube-clipper-completo/main.py`

## Propósito
O arquivo `main.py` atua como o script orquestrador principal de todo o pipeline da aplicação. O seu propósito é unificar e coordenar os diferentes módulos do sistema — download do vídeo, transcrição por IA, análise estratégica de trechos virais (local ou via API), refinamento de limites de corte, processamento físico e estilização dos clipes (incluindo legendas dinâmicas, layout, marcas d'água e handles) e geração do relatório final em formato JSON.

---

## Como funciona
O script opera de forma sequencial através de uma interface de linha de comando baseada em `argparse`:

1. **Configuração de Argumentos (`argparse`):** Lê as opções informadas pelo usuário, tais como a URL do vídeo do YouTube, modelo Whisper, quantidade de cortes, escolha de análise (`local` ou `api`), estilo de legenda/manchete, nicho do conteúdo e opções visuais.
2. **Download do Vídeo:** Utiliza o módulo `downloader` para baixar o vídeo de origem e recuperar o seu título. Uma pasta específica para o vídeo é criada com base no título slugificado.
3. **Transcrição:** Processa o áudio do vídeo utilizando o `faster-whisper` para extrair os segmentos e palavras cronometradas, salvando uma cópia em texto (`transcricao.txt`) na pasta de saída.
4. **Análise Estratégica:** 
   - Realiza a varredura do texto utilizando heurísticas locais (`analyzer_free`) ou o modelo do Claude (`analyzer`), dependendo do parâmetro `--analise`, filtrando com base no parâmetro `--nicho`.
   - Aplica a função `refinar_cortes` para ajustar as fronteiras de início e fim dos clipes, evitando cortes abruptos no meio das frases.
5. **Corte e Estilização (`cutter`):** Recorta fisicamente os trechos mapeados do vídeo, aplicando opções de layout (verticalização, blur ou zoom preenchido), queima de legendas estilizadas, adição de marca d'água e handles personalizados.
6. **Relatório Final:** Compila metadados detalhados de cada corte gerado (incluindo manchetes, pontuações, ganchos e legendas de postagem) e exporta um arquivo `relatorio_cortes.json`.

---

## Dependências
O módulo importa e depende diretamente dos seguintes componentes internos do projeto e bibliotecas padrão:
- **`argparse`**: Para o tratamento de argumentos passados via linha de comando.
- **`json`**: Para a serialização do relatório final de cortes.
- **`os`**: Para manipulação de caminhos e criação de diretórios no sistema de arquivos.
- **`downloader`**: Função `baixar_video`.
- **`transcriber`**: Funções `transcrever` e `formatar_transcricao_para_analise`.
- **`analyzer_free`**: Função `analisar_transcricao_local`.
- **`cutter`**: Função `cortar_video`.
- **`postagem`**: Função `gerar_legenda_post`.
- **`utils`**: Funções `slugificar` e `refinar_cortes`.
- **`captions`**: Dicionário `ESTILOS` e constante `ESTILO_PADRAO`.
- **`analyzer`** *(Importação tardia/condicional)*: Função `analisar_transcricao` (ativada apenas se `--analise api` for selecionado).

---

## Pontos de configuração (o que costuma mudar)
As principais opções que podem ser ajustadas via linha de comando na execução do script incluem:
- **`url`**: O link de acesso ao vídeo do YouTube a ser processado.
- **`--modelo-whisper`**: O tamanho do modelo de transcrição (ex: `small`, `base`).
- **`--qtd-cortes`**: O número de clipes desejados (padrão: `12`).
- **`--analise`**: O motor de escolha dos trechos, podendo ser `local` (gratuito por heurísticas) ou `api` (via Claude).
- **`--nicho`**: O contexto do conteúdo para otimizar a seleção (`geral`, `esporte`, `musica` ou texto livre para a API).
- **`--estilo`**: O design visual das legendas dinâmicas e manchetes de abertura (ex: `impacto`, `moderno`, `comic`).
- **`--layout`**: O formato de exibição do vídeo cortado (`preenchido` ou `blur`).
- **`--rapido`**: Flag para priorizar a velocidade de processamento reduzindo o modelo Whisper e o preset de renderização do FFmpeg.
- **`--sem-legenda`**, **`--sem-marca-dagua`**, **`--sem-handle`**: Flags para desativar elementos visuais específicos sobrepostos ao vídeo.

---

## Histórico de mudanças

| Data | Hash do commit | Autor | Descrição da mudança |
| :--- | :--- | :--- | :--- |
| Mon Nov 2 20:46:17 2026 -0300 | a8e2e9f | Gustavo Rockembach | Adicionado suporte a novos parâmetros de linha de comando (`--estilo` e `--nicho`), integração com a função `refinar_cortes` para ajuste de limites de fala, repasse do estilo para o renderizador de cortes e inclusão de metadades de manchete e pontuação no relatório final em JSON. |