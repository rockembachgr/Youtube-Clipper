# Módulo: `youtube-clipper-completo/captions.py`

## Propósito
O módulo `captions.py` é responsável por gerar arquivos de legenda no formato `.ass` (Advanced SubStation Alpha) para os cortes de vídeo gerados no sistema. Ele compõe três elementos visuais principais em cada clipe:
1. **Faixa de abertura ("manchete no rodapé")**: Exibe uma manchete curta nos primeiros segundos do vídeo sobreposta a uma faixa gráfica (desenhada pelo `cutter.py`), com redimensionamento dinâmico de fonte de acordo com o comprimento do texto.
2. **Legenda dinâmica palavra-a-palavra**: Exibe transcrições sincronizadas divididas em blocos, destacando visualmente a palavra exata que está sendo falada no momento. Começa a ser exibida somente após o encerramento da faixa de abertura.
3. **Handle da conta (`@usuario`)**: Posicionado de forma discreta no canto superior direito do vídeo, logo abaixo da logo do canal, visível durante toda a duração do clipe.

---

## Como funciona
O fluxo de execução do módulo baseia-se em receber dados de transcrição (palavras com marcações de tempo), aplicar regras de estilo configuradas e montar a estrutura de um arquivo `.ass`:

1. **Seleção de Estilos (`obter_estilo`)**: Consulta o preset visual desejado (como `impacto`, `moderno` ou `comic`) contendo parâmetros tipográficos, cores em formato ASS (`&HAABBGGRR`), bordas e escalas.
2. **Filtragem e Deslocamento de Tempos**: Isola as palavras compreendidas dentro do intervalo do corte (`[inicio_corte, fim_corte]`), reajustando os timestamps para iniciarem em `0` (relativo ao clipe) e ignorando palavras que colidam com a duração da manchete inicial.
3. **Agrupamento de Palavras (`_agrupar_palavras`)**: Organiza a transcrição em blocos controlados (respeitando limites máximos de palavras, duração e pontuações finais de frases como `.`, `!` e `?`).
4. **Ajuste da Manchete (`_ajustar_manchete`)**: Processa o texto da abertura, calculando de forma automatizada o maior tamanho de fonte viável para que o texto caiba perfeitamente na área designada em até duas linhas (com quebras balanceadas).
5. **Geração do Arquivo (`gerar_ass_para_corte`)**: Escreve o cabeçalho do formato ASS, os estilos definidos e os blocos de eventos (`[Events]`) contendo as diretrizes de animação, posicionamento (`\pos`, `\an5`) e destaque de cores (`\c`).

---

## Dependências
- **`os`**: Manipulação de caminhos e diretórios do sistema operacional.
- **`textwrap`**: Utilizado para o tratamento de quebras automáticas de texto em linhas restritas.

---

## Pontos de configuração (o que costuma mudar)
- **Presets de Estilo (`ESTILOS` / `ESTILO_PADRAO`)**: Dicionário central que define a identidade visual das legendas e manchetes (fontes, tamanhos, cores de texto e destaque, bordas, sombras e espaçamentos). O estilo padrão atual é `"impacto"`.
- **Durações e Limites**:
  - `DURACAO_MAX_BLOCO` e `RODAPE_DURACAO`: Controlam o tempo máximo de permanência dos blocos na tela (padrão de `3.2` segundos).
  - `ALTURA_FAIXA_PADRAO`: Altura padrão da área da manchete (`220` pixels), devendo corresponder às configurações no módulo `cutter.py`.
- **Handle e Logos**: Parâmetros como `HANDLE_FONTE`, `HANDLE_TAMANHO_FONTE` e proporções de largura (`LOGO_LARGURA_PROPORCAO`, `LOGO_MARGEM`, `HANDLE_GAP_ABAIXO_LOGO`) para garantir o alinhamento com a marca d'água do canal.

---

## Histórico de mudanças

| Data | Autor | Commit | Descrição da mudança |
| :--- | :--- | :--- | :--- |
| Mon Nov 2 20:46:17 2026 -0300 | Gustavo Rockembach | a8e2e9f | alterações de legenda |