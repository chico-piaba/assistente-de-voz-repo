# Documentação do Projeto: Assistente de Voz para Cálculos

Este documento detalha o desenvolvimento de um assistente de voz em Python, desde a sua concepção até a implementação das funcionalidades de reconhecimento e síntese de fala.

## 1. Estrutura do Projeto

- **Objetivo:** Transformar um script de calculadora baseado em texto em um assistente de voz interativo.
- **Diretório do Projeto:** Para manter a organização, o novo projeto foi criado em `Junho/Assistente de Voz/`.
- **Arquivos Iniciais:**
  - `assistente.py`: O script principal do assistente de voz.
  - `requirements.txt`: Arquivo para gerenciar as dependências do Python.
  - `DOCUMENTACAO.md`: Este arquivo.

## 2. Gerenciamento de Dependências

O arquivo `requirements.txt` foi populado com as seguintes bibliotecas:

- `SpeechRecognition`: Para a funcionalidade de reconhecimento de fala (Speech-to-Text).
- `gTTS`: (Google Text-to-Speech) Para a funcionalidade de síntese de fala (Text-to-Speech).
- `pyaudio`: Biblioteca necessária para acessar o microfone.
- `pygame`: Utilizada para reproduzir os arquivos de áudio gerados.

### 2.1. Solução de Problemas na Instalação

Durante a configuração do ambiente, alguns desafios foram superados:

1.  **Erro na `playsound`:** A instalação da biblioteca `playsound` falhou. Ela foi substituída pela `pygame`, que é uma alternativa mais robusta e com melhor compatibilidade.
2.  **Dependência `portaudio`:** A instalação do `pyaudio` falhou devido à ausência da dependência de sistema `portaudio`. O problema foi resolvido instalando `portaudio` através do Homebrew (`brew install portaudio`).

## 3. Funcionalidades Implementadas

O script `assistente.py` atualmente possui as seguintes funcionalidades:

### 3.1. Síntese de Fala (`falar_resultado`)

- Utiliza a biblioteca `gTTS` para converter uma string de texto em um arquivo de áudio (`.mp3`).
- Utiliza a `pygame` para carregar e reproduzir o áudio, fornecendo uma resposta falada ao usuário.
- O arquivo de áudio temporário é removido após a reprodução para não ocupar espaço.

### 3.2. Reconhecimento de Fala (`ouvir_comando`)

- Utiliza a biblioteca `SpeechRecognition` em conjunto com a `pyaudio` para capturar áudio do microfone.
- Ajusta-se ao ruído ambiente para melhorar a precisão.
- Envia o áudio capturado para a API de reconhecimento de fala do Google.
- Retorna o texto transcrito em letras minúsculas.
- Inclui tratamento de erros para quando o áudio não é compreendido ou quando há problemas com o serviço de reconhecimento.

## 4. Estado Atual

O assistente está em um estado funcional de "ouvir e repetir". Ele é capaz de:
- Iniciar e saudar o usuário com uma mensagem de voz.
- Ouvir continuamente os comandos do usuário.
- Transcrever a fala do usuário para texto.
- Repetir o comando transcrito em voz alta.
- Encerrar a execução se o usuário disser "parar" ou "sair".

O próximo passo é integrar a lógica de cálculo para que o assistente possa interpretar e resolver operações matemáticas ditadas pelo usuário.

## 5. Evolução para Calculadora Avançada

O assistente foi significativamente aprimorado para se tornar uma calculadora mais robusta e inteligente.

### 5.1. Implementação de Logging

- **Objetivo:** Registrar todas as interações para análise de assertividade e depuração.
- **Implementação:** Foi utilizado o módulo `logging` do Python.
- **Arquivo de Log:** Todos os comandos de voz recebidos e os resultados processados são salvos em `Junho/Assistente de Voz/logs/operacoes.log`.

### 5.2. Motor de Cálculo com `eval()`

- **Problema:** A abordagem inicial de dividir strings não respeitava a ordem das operações matemáticas (PEMDAS).
- **Solução:** A lógica de cálculo foi refeita para usar a função `eval()`, que interpreta uma string como uma expressão Python.
- **Segurança:** Para evitar a execução de código malicioso, a string de entrada é rigorosamente validada para permitir apenas números, operadores matemáticos (`+`, `-`, `*`, `/`, `**`, `%`) e parênteses.

### 5.3. Expansão das Funções Matemáticas

O assistente agora suporta um conjunto maior de operações, incluindo:

- **Operações Aritméticas Complexas:** Respeita a ordem de precedência.
- **Potência e Quadrado:** Ex: "2 elevado a 8", "quadrado de 5".
- **Módulo:** Ex: "módulo de 10 por 3".
- **Raiz Quadrada:** Ex: "raiz quadrada de 81".
- **Logaritmos:** Logaritmo neperiano ("log de 10") e na base 10 ("logaritmo na base 10 de 100").
- **Funções Trigonométricas:** Seno, cosseno e tangente. O assistente converte automaticamente os valores de graus para radianos antes de realizar o cálculo.
