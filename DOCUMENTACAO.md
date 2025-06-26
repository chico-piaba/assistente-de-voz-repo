# Documentação do Projeto: Assistente de Voz para Cálculos

Este documento detalha a arquitetura e o funcionamento de um assistente de voz para cálculos matemáticos, implementado em Python com o microframework Flask.

## 1. Visão Geral e Estrutura

- **Objetivo:** Criar um serviço de backend capaz de receber comandos de voz ou texto, interpretar operações matemáticas complexas e retornar o resultado de forma estruturada.
- **Tecnologias Principais:**
  - **Python:** Linguagem de programação.
  - **Flask:** Microframework para criação do servidor web (API).
  - **Google Cloud Speech-to-Text:** API para transcrição de áudio em texto.
- **Estrutura de Diretórios:**
  - `assistente.py`: Script principal contendo toda a lógica do servidor Flask.
  - `templates/index.html`: Interface web básica para interação e testes.
  - `logs/operacoes.log`: Arquivo de log para registro de todas as operações.
  - `requirements.txt`: Lista de dependências do projeto.
  - `"Python App Calc.json"`: Arquivo de credenciais para a API do Google (não versionado).

## 2. Dependências

O arquivo `requirements.txt` gerencia as seguintes bibliotecas:
- `Flask`: Para criar e gerenciar o servidor web.
- `google-cloud-speech`: Cliente oficial para a API de Speech-to-Text do Google.

## 3. Configuração Inicial

Antes de processar qualquer comando, o script `assistente.py` realiza as seguintes configurações:

1.  **Logging:** Configura o módulo `logging` para registrar todas as interações e possíveis erros no arquivo `logs/operacoes.log`. Isso é crucial para depuração e análise de uso.
2.  **Flask App:** Inicializa a aplicação Flask.
3.  **Google Speech Client:** Carrega as credenciais do arquivo `"Python App Calc.json"` e inicializa o cliente da API do Google, que será usado para a transcrição de áudio.

## 4. Endpoints da API

A aplicação expõe três rotas (endpoints) principais para interação:

- **`GET /`**: Renderiza a página `index.html`, que serve como uma interface de usuário simples para testar o assistente.
- **`POST /recognize`**:
  - Recebe um arquivo de áudio (`audio_data`).
  - Envia este áudio para a API do Google Speech-to-Text para transcrição.
  - Passa o texto transcrito para a função `processar_comando`.
  - Retorna a resposta estruturada em formato JSON.
- **`POST /process`**:
  - Recebe um comando de texto (`command_text`).
  - Passa o texto diretamente para a função `processar_comando`.
  - Retorna a resposta estruturada em formato JSON.

## 5. Lógica de Processamento de Comandos

O coração do assistente reside na função `processar_comando(comando)`. Ela executa uma sequência de etapas para transformar a linguagem natural em uma expressão matemática calculável.

### Etapa 1: Pré-processamento e Traduções Iniciais
- O comando recebido é convertido para minúsculas e cercado por espaços para facilitar a busca com expressões regulares.
- **Tradução de Funções:** Utiliza expressões regulares para identificar e substituir comandos de funções matemáticas complexas (ex: "raiz quadrada de 64") por suas chamadas de função Python equivalentes (ex: `math.sqrt(64)`). A ordem das substituições é importante para evitar conflitos.

### Etapa 2: Mapeamento de Palavras para Símbolos
- Um dicionário (`mapeamento`) é usado para traduzir palavras faladas (ex: "cinco", "mais", "vezes") para seus correspondentes numéricos e operadores (`5`, `+`, `*`).

### Etapa 3: Limpeza e Montagem da Expressão
- **Remoção de "Stop Words":** Palavras de preenchimento que não têm valor matemático (ex: "calcule", "quanto é") são removidas.
- **Substituição Final:** O comando é varrido novamente para substituir as palavras restantes pelos símbolos do dicionário de mapeamento.
- **Multiplicação Implícita:** O código adiciona o operador de multiplicação (`*`) em contextos onde ele é omitido na fala, como em "10(5)" ou ")(".
- **Sanitização:** A expressão resultante é limpa para permitir apenas caracteres seguros: letras, números, ponto, parênteses e os operadores matemáticos básicos.

### Etapa 4: Avaliação Segura e Resposta
- **Validação:** O sistema verifica se a expressão não está vazia ou incompleta.
- **Cálculo com `eval()`:** A expressão limpa é avaliada usando a função `eval()`. Para mitigar riscos de segurança, `eval()` é executada em um contexto restrito (`contexto_eval`) que só permite acesso às funções do módulo `math`, bloqueando o acesso a funções de sistema perigosas.
- **Formatação da Resposta:** Em caso de sucesso, o resultado é formatado. Uma função auxiliar `criar_resposta` gera um objeto JSON com duas versões do texto:
  - `display_text`: Uma versão visualmente limpa da operação para ser exibida na tela (ex: "√64 + sen(90)").
  - `speech_text`: Uma versão textual para ser lida em voz alta (ex: "raiz quadrada de 64 mais seno de 90").
- **Tratamento de Erros:** Qualquer exceção durante a avaliação (divisão por zero, sintaxe inválida, etc.) é capturada, registrada no log, e uma mensagem de erro amigável é retornada ao usuário.

## 6. Arquitetura e Fluxo de Dados

O fluxo de uma requisição de voz pode ser resumido da seguinte forma:

1.  **Frontend (Cliente):** O usuário clica para gravar, o navegador captura o áudio do microfone.
2.  **Requisição:** O áudio gravado é enviado via `POST` para o endpoint `/recognize`.
3.  **Backend (Flask):**
    a. O endpoint `/recognize` recebe o áudio.
    b. Envia o áudio para a **API Google Speech-to-Text**.
    c. O Google retorna o texto transcrito.
    d. O texto é passado para a função `processar_comando`.
    e. `processar_comando` executa todas as etapas de tradução, limpeza e cálculo.
    f. A função `eval()` calcula o resultado final de forma segura.
    g. Uma resposta JSON estruturada é criada.
4.  **Resposta:** O backend retorna o JSON para o frontend.
5.  **Frontend (Cliente):** A interface de usuário exibe o `display_text` e, opcionalmente, utiliza uma API de Text-to-Speech do navegador para ler o `speech_text`.
