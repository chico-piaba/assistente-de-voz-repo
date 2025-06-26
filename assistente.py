# -*- coding: utf-8 -*-
"""
================================================
ARQUIVO PRINCIPAL DO BACKEND - ASSISTENTE DE VOZ
================================================

Este script Python utiliza o framework Flask para criar um servidor web que atua como o "cérebro" do assistente de voz.

Funcionalidades:
- Recebe comandos de voz (como arquivos de áudio) ou de texto.
- Utiliza a API de Speech-to-Text do Google para transcrever o áudio.
- Processa o texto para identificar e executar operações matemáticas.
- Retorna os resultados em um formato estruturado (JSON) para o frontend.
"""

# --- 1. IMPORTAÇÕES ---
# Módulos essenciais para o funcionamento do servidor, processamento de texto e matemática.
from flask import Flask, render_template, request, jsonify
from google.cloud import speech
import re
import math
import logging
import os

# --- 2. FUNÇÕES AUXILIARES ---
# Funções pequenas e reutilizáveis que ajudam a manter o código limpo.

def formatar_numero(n):
    """
    Formata um número para uma apresentação mais amigável.
    - Se o número for um inteiro (ex: 5.0), remove o '.0'.
    - Se for um número com muitas casas decimais, arredonda para 4 casas.
    """
    if isinstance(n, float):
        if n.is_integer():
            return int(n)
        return round(n, 4)
    return n

def criar_resposta(display, speech=None):
    """
    Cria o objeto de resposta padronizado para o frontend.
    Isso garante que a resposta do servidor tenha sempre a mesma estrutura.
    - display_text: O texto que será exibido na tela.
    - speech_text: O texto que será lido em voz alta (pode ser diferente para uma pronúncia melhor).
    """
    return {"display_text": display, "speech_text": speech if speech is not None else display}

# --- 3. CONFIGURAÇÃO INICIAL ---

# Configuração do logging para registrar eventos importantes em um arquivo.
# Ajuda a depurar problemas e entender como o assistente está sendo usado.
script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(script_dir, "logs")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "operacoes.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)

# Inicialização do aplicativo Flask.
app = Flask(__name__)

# Configuração das credenciais da API do Google Cloud Speech.
# O sistema procura pelo arquivo .json no mesmo diretório do script.
credentials_path = os.path.join(script_dir, "Python App Calc.json")
if not os.path.exists(credentials_path):
    raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {credentials_path}")
speech_client = speech.SpeechClient.from_service_account_file(credentials_path)


# --- 4. LÓGICA PRINCIPAL DE PROCESSAMENTO ---

def processar_comando(comando):
    """
    Esta é a função central do assistente. Ela recebe o comando como texto
    e tenta extrair uma operação matemática.
    """
    logging.info(f"Comando recebido: '{comando}'")
    comando = ' ' + comando.lower() + ' '  # Adicionar espaços para facilitar regex

    # ETAPA 1: TRADUÇÃO DE FUNÇÕES MATEMÁTICAS (COMANDOS ESPECIAIS)
    # Esta etapa substitui frases complexas por suas funções matemáticas equivalentes
    # em Python. Isso permite que múltiplas funções sejam usadas em um único comando.
    # Ex: "raiz de 4 + seno de 90" -> " math.sqrt(4) + math.sin(math.radians(90)) "
    substituicoes = [
        # A ordem é importante para evitar sobreposições (ex: "ao quadrado" antes de "quadrado de").
        (r'\s*raiz quadrada de\s*(\d+\.?\d*)', r' math.sqrt(\1) '),
        (r'\s*(\d+\.?\d*)\s*ao quadrado', r' (\1**2) '),
        (r'\s*quadrado de\s*(\d+\.?\d*)', r' (\1**2) '),
        (r'\s*(\d+\.?\d*)\s*ao cubo', r' (\1**3) '),
        (r'\s*cubo de\s*(\d+\.?\d*)', r' (\1**3) '),
        (r'\s*logaritmo na base 10 de\s*(\d+\.?\d*)', r' math.log10(\1) '),
        (r'\s*(?:logaritmo natural de|log de)\s*(\d+\.?\d*)', r' math.log(\1) '),
        (r'\s*seno de\s*(\d+\.?\d*)', r' math.sin(math.radians(\1)) '),
        (r'\s*cosseno de\s*(\d+\.?\d*)', r' math.cos(math.radians(\1)) '),
        (r'\s*tangente de\s*(\d+\.?\d*)', r' math.tan(math.radians(\1)) '),
        (r'\s*(\d+\.?\d*)\s*por cento de\s*(\d+\.?\d*)', r' ((\1/100)*\2) '),
    ]
    for pattern, replacement in substituicoes:
        comando = re.sub(pattern, replacement, comando)


    # ETAPA 2: MAPEAMENTO DE PALAVRAS PARA SÍMBOLOS
    # Dicionário que traduz palavras faladas (ex: "mais", "cinco") para
    # seus equivalentes matemáticos (ex: "+", "5").
    mapeamento = {
        # Números
        "zero": "0", "um": "1", "uma": "1", "dois": "2", "três": "3", "quatro": "4",
        "cinco": "5", "seis": "6", "sete": "7", "oito": "8", "nove": "9", "dez": "10",
        "onze": "11", "doze": "12", "treze": "13", "quatorze": "14", "quinze": "15",
        "dezesseis": "16", "dezessete": "17", "dezoito": "18", "dezenove": "19",
        "vinte": "20", "trinta": "30", "quarenta": "40", "cinquenta": "50",
        "sessenta": "60", "setenta": "70", "oitenta": "80", "noventa": "90",
        "cem": "100", "duzentos": "200", "trezentos": "300", "quatrocentos": "400",
        "quinhentos": "500", "seiscentos": "600", "setecentos": "700",
        "oitocentos": "800", "novecentos": "900", "mil": "1000",
        # Operadores
        "mais": "+", "somado com": "+", "adicionado a": "+",
        "menos": "-", "subtraído por": "-",
        "vezes": "*", "multiplicado por": "*",
        "dividido por": "/", "dividido": "/", "divide por": "/", "sobre": "/",
        "elevado a": "**", "elevado ao": "**", "x": "*",
        "módulo de": "%", "resto da divisão de": "%", "módulo": "%",
        # Símbolos
        "abre parênteses": "(", "abrir parênteses": "(", "parênteses": "(",
        "fecha parênteses": ")", "fechar parênteses": ")",
        "vírgula": ".", "ponto": ".",
    }

    # ETAPA 3: LIMPEZA E CONSTRUÇÃO DA EXPRESSÃO GENÉRICA
    # Se nenhum dos casos especiais acima foi encontrado, o código tenta montar
    # uma expressão matemática genérica para ser avaliada pelo Python.

    # Remove palavras de preenchimento (ex: "quanto é", "calcule") que não afetam o cálculo.
    palavras_de_preenchimento = [
        "quanto é", "calcule", "me diga", "qual é", "qual o resultado de",
        "o resultado de", "aqui a gente conta", "por favor", "por gentileza", "poderia calcular",
        "você pode me dizer"
    ]
    for p in palavras_de_preenchimento:
        # Usamos espaços para garantir que estamos substituindo a palavra inteira
        comando = comando.replace(f' {p} ', ' ')

    # Substitui as palavras restantes pelos seus símbolos (usando o dicionário).
    for palavra, simbolo in mapeamento.items():
        comando = comando.replace(f' {palavra} ', f' {simbolo} ')

    # Adiciona o operador de multiplicação ausente (multiplicação implícita).
    # Ex: "10(5)" -> "10 * (5)" ou ")(" -> ") * ("
    comando = re.sub(r'(\d)\s*\(', r'\1 * (', comando)
    comando = re.sub(r'\)\s*\(', r') * (', comando)


    # "Sanitiza" a expressão, removendo quaisquer caracteres que não sejam permitidos.
    # Esta regex corrige o bug que removia letras de funções (ex: 's' de 'sqrt').
    # A nova regex permite:
    # \w: Caracteres de palavra (letras, números, _)
    # .: Ponto literal (para 'math.sqrt')
    # \s: Espaço em branco
    # ()+-*/%: Símbolos matemáticos
    expr_limpa = re.sub(r'[^\w.\s()+\-*/%]', '', comando).strip()
    
    # Se não sobrar nada após a limpeza, o comando não era uma expressão válida.
    if not expr_limpa:
        return criar_resposta("Não consegui identificar uma operação matemática no seu comando.")

    # Nova verificação para expressões incompletas
    if expr_limpa.endswith(tuple("+-*/%**.")):
        return criar_resposta("Sua expressão matemática parece estar incompleta. Tente terminá-la.")


    # ETAPA 4: AVALIAÇÃO SEGURA DA EXPRESSÃO
    try:
        # Uma verificação mais limpa para ver se há algo para calcular.
        operadores = ['+', '-', '*', '/', '%', '**']
        if not any(op in expr_limpa for op in operadores) and "math" not in expr_limpa:
            if re.fullmatch(r'[\d.]+', expr_limpa):
                return criar_resposta(f"Você disse o número {expr_limpa}.")
            else:
                return criar_resposta("Não consegui identificar uma operação matemática válida.")

        # O `eval` é executado em um ambiente controlado (`contexto_eval`)
        # que não tem acesso a funções perigosas do sistema (__builtins__ = None).
        # Adicionamos 'math' ao contexto para que as funções math.sqrt, etc., funcionem.
        contexto_eval = {
            "__builtins__": None,
            "math": math
        }
        
        resultado = eval(expr_limpa, contexto_eval)
        
        # Cria textos separados para exibição (ex: "5 x 2") e para fala (ex: "5 vezes 2").
        # Simplificando a criação do display text para refletir a complexidade.
        display_expr = expr_limpa.replace('math.sqrt', '√').replace('math.log10', 'log10').replace('math.log', 'ln').replace('math.radians', '').replace('math.sin', 'sen').replace('math.cos', 'cos').replace('math.tan', 'tan').replace('**', '^').replace('*', 'x')

        # Para a fala, substitui todos os operadores por suas formas faladas.
        speech_expr = expr_limpa.replace('**', ' elevado a ')
        speech_expr = speech_expr.replace('*', ' vezes ')
        speech_expr = speech_expr.replace('/', ' dividido por ')
        speech_expr = speech_expr.replace('+', ' mais ')
        speech_expr = speech_expr.replace('-', ' menos ')
        speech_expr = speech_expr.replace('%', ' módulo ')
        # Limpando a fala das chamadas de função
        speech_expr = re.sub(r'math\.\w+\((.*?)\)', r'\1', speech_expr)

        display_text = f"O resultado de {display_expr} é {formatar_numero(resultado)}"
        speech_text = f"O resultado de {speech_expr} é {formatar_numero(resultado)}"
        
        logging.info(f"Expressão processada: '{expr_limpa}' -> Resultado: {resultado}")
        return criar_resposta(display_text, speech_text)

    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
        # Trata erros comuns de matemática e sintaxe.
        logging.error(f"Erro ao avaliar a expressão '{expr_limpa}' a partir de '{comando}': {e}")
        return criar_resposta("Não consegui calcular essa expressão. Verifique se está correta.")
    except Exception as e:
        # Captura qualquer outro erro inesperado.
        logging.error(f"Erro inesperado ao processar '{expr_limpa}': {e}")
        return criar_resposta("Ocorreu um erro inesperado ao tentar calcular.")

# --- 5. ROTAS DA APLICAÇÃO WEB (ENDPOINTS) ---
# Define os "caminhos" da API que o frontend pode chamar.

@app.route('/')
def index():
    """Serve a página principal (index.html)."""
    return render_template('index.html')

@app.route('/recognize', methods=['POST'])
def recognize_speech():
    """
    Recebe o áudio do microfone, envia para a API do Google STT (Speech-to-Text),
    e retorna o resultado do processamento do texto transcrito.
    """
    if 'audio_data' not in request.files:
        return jsonify({'error': 'Nenhum arquivo de áudio enviado'}), 400

    audio_file = request.files['audio_data']
    content = audio_file.read()

    # Configura o pedido para a API do Google
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code="pt-BR",
    )

    try:
        # Envia o áudio e recebe a transcrição
        response = speech_client.recognize(config=config, audio=audio)
        if not response.results:
            no_speech_text = "Não foi possível reconhecer a fala."
            return jsonify({'transcript': no_speech_text, 'result': criar_resposta(no_speech_text)})

        transcript = response.results[0].alternatives[0].transcript
        logging.info(f"Texto reconhecido pelo Google: '{transcript}'")
        
        # Envia o texto para a função de processamento
        result_obj = processar_comando(transcript)
        return jsonify({'result': result_obj, 'transcript': transcript})

    except Exception as e:
        logging.error(f"Erro na API do Google Speech: {e}")
        error_msg = f'Erro ao processar o áudio: {e}'
        return jsonify({'error': error_msg, 'result': criar_resposta(error_msg)}), 500

@app.route('/process', methods=['POST'])
def process_web_command():
    """Processa um comando que já vem como texto (do campo de input)."""
    data = request.get_json()
    command = data.get('command', '')
    
    if not command:
        return jsonify({'error': 'Comando vazio.', 'result': criar_resposta("Comando vazio.")}), 400
    
    # Envia o texto para a mesma função de processamento
    result_obj = processar_comando(command)
    return jsonify({'result': result_obj})

# --- 6. EXECUÇÃO DO SERVIDOR ---
if __name__ == "__main__":
    """Inicia o servidor Flask em modo de depuração."""
    app.run(debug=True, port=5001)
