# Assistente de Voz para Cálculos: Documentação do Projeto

## 1. Visão Geral do Projeto

Este documento detalha a arquitetura, as funcionalidades e a evolução de um aplicativo web de assistente de voz para cálculos matemáticos. O projeto transforma um simples comando de voz ou texto em uma operação matemática, que é calculada e cujo resultado é exibido e falado ao usuário.

O objetivo era criar uma ferramenta que fosse não apenas funcional, mas também inteligente, flexível e com uma experiência de usuário agradável.

---

## 2. Arquitetura: Cliente-Servidor

O projeto é construído sobre um modelo cliente-servidor, desacoplando a interface do usuário da lógica de processamento.

### 2.1. Backend (O "Cérebro" - Python + Flask)

O servidor é responsável por toda a lógica pesada e inteligência da aplicação.

-   **Tecnologia**: `Python` com o micro-framework `Flask`.
-   **Responsabilidades**:
    1.  **API Endpoints**: Fornece "caminhos" (`/recognize` para áudio, `/process` para texto) que o frontend pode chamar.
    2.  **Transcrição de Áudio**: Recebe o arquivo de áudio, envia para a **API Speech-to-Text do Google** e obtém o texto correspondente.
    3.  **Processamento de Linguagem Natural (PLN)**:
        -   Utiliza um extenso dicionário (`mapeamento`) para traduzir palavras (ex: "cinco", "vezes") para seus símbolos matemáticos ("5", "*").
        -   Identifica e trata comandos especiais (ex: "raiz quadrada de", "porcento de") usando expressões regulares (`regex`).
    4.  **Lógica de Cálculo**: Monta uma expressão matemática segura a partir do texto e a resolve usando a função `eval()` em um ambiente controlado para evitar riscos de segurança.
    5.  **Formatação da Resposta**: Devolve o resultado em um formato JSON estruturado, com um texto para exibição e outro otimizado para a fala.

### 2.2. Frontend (A "Interface" - HTML, CSS, JS)

O frontend é tudo o que o usuário vê e com o que ele interage no navegador.

-   **Tecnologia**: `HTML` para a estrutura, `CSS` para o estilo e `JavaScript` para a interatividade.
-   **Responsabilidades**:
    1.  **Interface do Usuário (UI)**: Apresenta os botões, campos de texto e cards de resultado de forma limpa e organizada.
    2.  **Captura de Entrada**:
        -   **Voz**: Usa a API do navegador (`MediaRecorder`) para gravar o áudio do microfone.
        -   **Texto**: Oferece um campo de `input` para digitação direta.
    3.  **Comunicação com o Backend**: Envia os dados (áudio ou texto) para a API do Flask e aguarda a resposta.
    4.  **Feedback Visual**: Informa ao usuário o que está acontecendo através de animações (botão pulsando ao gravar, "spinner" ao processar).
    5.  **Síntese de Fala (Text-to-Speech)**: Usa a API do navegador (`SpeechSynthesis`) para ler o resultado em voz alta, com uma lógica para selecionar a melhor voz em português disponível.
    6.  **Qualidade de Vida**: Implementa funcionalidades extras como "Repetir" e "Editar" para uma melhor experiência.

---

## 3. Fluxo de um Comando de Voz

1.  **Usuário**: Clica no botão "Ouvir Comando".
2.  **Frontend (JS)**: O botão ativa a animação de "pulsar". A API `MediaRecorder` começa a gravar o áudio do microfone.
3.  **Usuário**: Diz "quanto é cinquenta por cento de duzentos".
4.  **Frontend (JS)**: O usuário para a gravação. O áudio é empacotado em um `Blob` e enviado via `fetch` para o endpoint `/recognize` do backend. A UI exibe a animação de "carregando".
5.  **Backend (Python/Flask)**: Recebe o áudio.
6.  **Backend (Python/Flask)**: Envia o áudio para a API do **Google Cloud Speech**.
7.  **Google API**: Retorna o texto transcrito: `"quanto é cinquenta por cento de duzentos"`.
8.  **Backend (Python/Flask)**: A função `processar_comando` é ativada:
    -   Ela identifica o padrão especial `"(\d+) por cento de (\d+)"`.
    -   Extrai "50" e "200".
    -   Calcula `(50 / 100) * 200 = 100`.
    -   Formata a resposta:
        -   `display_text`: "50 por cento de 200 é 100"
        -   `speech_text`: "cinquenta por cento de duzentos é cem"
9.  **Backend (Python/Flask)**: Envia a resposta em formato JSON para o frontend.
10. **Frontend (JS)**: Recebe o JSON.
    -   Exibe o `display_text` no card de resultado.
    -   Usa a `SpeechSynthesis` para falar o `speech_text`.
    -   Exibe os botões de "Repetir" e "Editar".

---

## 4. Conclusão e Evolução

O projeto evoluiu de um simples script de linha de comando para um aplicativo web completo e robusto. As principais etapas dessa evolução foram:

-   **Da Linha de Comando para a Web**: Adoção do Flask para criar uma API.
-   **Da Fala Local para a Nuvem**: Substituição de bibliotecas locais de reconhecimento pela API do Google, garantindo maior precisão.
-   **Da Lógica Simples à Inteligência**: Expansão massiva do dicionário e uso de expressões regulares para entender uma gama muito maior de comandos.
-   **Da Interface Básica à Experiência do Usuário**: Refinamento do frontend com feedback visual, múltiplas formas de entrada e funcionalidades de conveniência.

Este projeto demonstra um ciclo completo de desenvolvimento de um aplicativo web interativo, unindo tecnologias de backend, frontend e serviços de nuvem de terceiros. 