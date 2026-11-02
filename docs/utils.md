# Documentação do Módulo: `utils.py`

## Propósito
O módulo `utils.py` centraliza funções auxiliares e utilitárias que são reutilizadas por diferentes módulos do projeto. Ele fornece ferramentas para manipulação e normalização de textos (slugificação) e para o pós-processamento e ajuste inteligente dos limites temporais de cortes de vídeo baseados na transcrição.

## Como funciona
O módulo executa operações utilitárias através de duas funções principais:
1. **`slugificar(texto, tamanho_max)`**: Converte um texto arbitrário em uma string segura para uso em nomes de arquivos e diretórios. O processo remove acentos, converte caracteres para minúsculas, elimina caracteres especiais e substitui espaços por hífens, respeitando um limite máximo de caracteres.
2. **`refinar_cortes(cortes, segmentos, tolerancia, folga_inicio, folga_fim, duracao_min, duracao_max)`**: Itera sobre uma lista de cortes propostos e alinha seus tempos de início e fim com as fronteiras reais das frases ou blocos da transcrição (segmentos). A função aplica margens de tolerância para encontrar o segmento mais próximo, adiciona pequenas folgas temporais para evitar o corte abrupto de sílabas e valida se a duração final do corte se enquadra nos limites aceitáveis, descartando aqueles que violarem as restrições de duração mínima ou máxima.

## Dependências
O módulo depende exclusivamente de bibliotecas nativas da linguagem Python:
- `re`: Utilizada para manipulação de expressões regulares na limpeza de strings e textos.
- `unicodedata`: Utilizada para a normalização de caracteres Unicode (remoção de acentos).

## Pontos de configuração (o que costuma mudar)
Os principais parâmetros que podem ser ajustados (geralmente via argumentos nas chamadas das funções) incluem:
- **`tamanho_max`**: O comprimento máximo gerado pela função `slugificar` (padrão: `60`).
- **`tolerancia`**: O limite máximo de tempo (em segundos) que a função de refinamento aceita para buscar uma fronteira de frase próxima (padrão: `6.0`).
- **`folga_inicio`** e **`folga_fim`**: Os tempos de margem adicionados antes do início e após o fim do corte para preservar a fluidez do áudio (padrões: `0.2` e `0.45` segundos, respectivamente).
- **`duracao_min`** e **`duracao_max`**: Os limites inferior e superior de duração (em segundos) para que um corte seja mantido após o refinamento (padrões: `20.0` e `130.0`).

## Histórico de mudanças

| Data | Hash do commit | Autor | Descrição da alteração |
| :--- | :--- | :--- | :--- |
| Mon Nov 2 20:46:17 2026 -0300 | a8e2e9f | Gustavo Rockembach | Adição da função `refinar_cortes` para ajuste de limites de início e fim de cortes com base nos segmentos da transcrição, incluindo aplicação de folgas e validação de duração. |