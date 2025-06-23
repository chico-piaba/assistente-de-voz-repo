from flask import Flask, render_template, request, jsonify
from google.cloud import speech
import re
import math
import logging
import os

# --- Configuração ---
script_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# --- Configuração das Credenciais do Google ---
# Constrói o caminho para o arquivo de credenciais
credentials_path = os.path.join(script_dir, "Python App Calc.json")

# Verifica se o arquivo de credenciais existe
if not os.path.exists(credentials_path):
    raise FileNotFoundError(f"Arquivo de credenciais não encontrado em: {credentials_path}. "
                            "Certifique-se de que o arquivo 'Python App Calc.json' está no mesmo diretório do script.")

# Configura o cliente do Google Cloud Speech com o arquivo de credenciais
speech_client = speech.SpeechClient.from_service_account_file(credentials_path)

# Configuração do logging
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

# --- Lógica de Cálculo (Função Principal) ---
def processar_comando(comando):
    """Processa o comando para encontrar e executar uma operação matemática de forma mais robusta."""
    logging.info(f"Comando recebido: '{comando}'")
    comando = comando.lower()

    # 1. Mapeamento de palavras para números e operadores
    mapeamento = {
        "zero": "0", "um": "1", "uma": "1", "dois": "2", "três": "3", "quatro": "4",
        "cinco": "5", "seis": "6", "sete": "7", "oito": "8", "nove": "9", "dez": "10",
        "mais": "+", "menos": "-", "vezes": "*", "multiplicado por": "*",
        "dividido por": "/", "elevado a": "**",
        "abre parênteses": "(", "fecha parênteses": ")",
        "vírgula": ".", "ponto": ".",
    }

    # 2. Tratamento de Casos Especiais e Funções (com mais contexto)
    # Raiz quadrada
    match_raiz = re.search(r'raiz quadrada de (\d+\.?\d*)', comando)
    if match_raiz:
        n = float(match_raiz.group(1))
        resultado = math.sqrt(n)
        return f"A raiz quadrada de {n} é {resultado}"

    # Potência (quadrado, cubo, etc.)
    match_potencia = re.search(r'(\d+\.?\d*) elevado a (\d+\.?\d*)', comando)
    if match_potencia:
        base = float(match_potencia.group(1))
        expoente = float(match_potencia.group(2))
        resultado = base ** expoente
        return f"{base} elevado a {expoente} é {resultado}"
    
    match_quadrado = re.search(r'quadrado de (\d+\.?\d*)', comando)
    if match_quadrado:
        n = float(match_quadrado.group(1))
        return f"O quadrado de {n} é {n**2}"

    # 3. Limpeza e Construção da Expressão
    # Remove palavras de preenchimento que não afetam o cálculo
    palavras_de_preenchimento = ["quanto é", "calcule", "me diga", "o resultado de", "aqui a gente conta"]
    for p in palavras_de_preenchimento:
        comando = comando.replace(p, "")

    # Substitui palavras por números/símbolos
    for palavra, simbolo in mapeamento.items():
        comando = comando.replace(palavra, simbolo)

    # Remove todos os caracteres que não são parte de uma expressão matemática segura
    # Permite: números, operadores, parênteses e ponto decimal.
    expr_limpa = re.sub(r'[^\d\s()+\-*/.%]', '', comando).strip()
    
    # Se depois da limpeza, não sobrar nada, é porque não era uma expressão
    if not expr_limpa:
        return "Não consegui identificar uma operação matemática no seu comando."

    # 4. Avaliação Segura da Expressão
    try:
        # Verifica se há alguma operação a ser feita
        if not any(op in expr_limpa for op in "+-*/%**"):
            # Se for apenas um número, retorna ele mesmo
            if re.fullmatch(r'[\d.]+', expr_limpa):
                return f"Você disse o número {expr_limpa}."
            else:
                return "Não consegui identificar uma operação matemática válida."

        # Define um ambiente seguro para o eval
        contexto_eval = {
            "__builtins__": None,
            "math": math # Se precisar de funções como pi, etc. no futuro
        }
        
        # Avalia a expressão
        resultado = eval(expr_limpa, contexto_eval)
        
        # Log e retorno
        logging.info(f"Expressão processada: '{expr_limpa}' -> Resultado: {resultado}")
        return f"O resultado de {expr_limpa} é {resultado}"

    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
        logging.error(f"Erro ao avaliar a expressão '{expr_limpa}' a partir de '{comando}': {e}")
        return "Não consegui calcular essa expressão. Verifique se está correta."
    except Exception as e:
        logging.error(f"Erro inesperado ao processar '{comando}': {e}")
        return "Ocorreu um erro inesperado ao tentar calcular."

# --- Rotas da Aplicação Web ---
@app.route('/')
def index():
    """Serve a página principal."""
    return render_template('index.html')

@app.route('/recognize', methods=['POST'])
def recognize_speech():
    """Recebe o áudio, envia para o Google STT e retorna o resultado do comando."""
    if 'audio_data' not in request.files:
        return jsonify({'error': 'Nenhum arquivo de áudio enviado'}), 400

    audio_file = request.files['audio_data']
    content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000, # O MediaRecorder geralmente usa 48000Hz com Opus
        language_code="pt-BR",
    )

    try:
        response = speech_client.recognize(config=config, audio=audio)
        if not response.results:
            return jsonify({'transcript': 'Não foi possível reconhecer a fala.', 'result': ''})

        transcript = response.results[0].alternatives[0].transcript
        logging.info(f"Texto reconhecido pelo Google: '{transcript}'")
        
        result_text = processar_comando(transcript)
        return jsonify({'result': result_text, 'transcript': transcript})

    except Exception as e:
        logging.error(f"Erro na API do Google Speech: {e}")
        return jsonify({'error': f'Erro ao processar o áudio: {e}'}), 500

@app.route('/process', methods=['POST'])
def process_web_command():
    """Processa o comando recebido do frontend."""
    data = request.get_json()
    command = data.get('command', '')
    
    if not command:
        return jsonify({'error': 'Comando vazio.'}), 400
    
    result_text = processar_comando(command)
    return jsonify({'result': result_text})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
