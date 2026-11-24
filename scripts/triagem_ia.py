"""
Triagem Inicial Assistida por IA (Gemini API) para apoio ao time de Talent Acquisition.
Lê os requisitos da vaga e os currículos anonimizados, consulta a API do Gemini com saída
estruturada em JSON e exporta o resultado para CSV (Excel / Power BI).
"""

import csv
import json
import os
from dotenv import load_dotenv
from google import genai

# Esquema JSON que obriga a IA a responder sempre com as mesmas colunas para o CSV
ESQUEMA_TRIAGEM = {
    "type": "object",
    "properties": {
        "nota_aderencia": {
            "type": "integer",
            "description": "Nota de 0 a 100 de aderência técnica e de requisitos da vaga.",
        },
        "classificacao": {
            "type": "string",
            "enum": ["Alta Aderência", "Média Aderência", "Baixa Aderência / Inelegível"],
        },
        "pontos_fortes": {
            "type": "string",
            "description": "Resumo objetivo das competências que atendem à vaga.",
        },
        "pontos_atencao": {
            "type": "string",
            "description": "Lacunas técnicas, conflito de horário ou impedimentos legais (ex: Lei do Estágio).",
        },
        "recomendacao_rh": {
            "type": "string",
            "enum": [
                "Avançar para Entrevista RH",
                "Validar Horário / Requisitos com Candidato",
                "Banco de Talentos / Não Elegível",
            ],
        },
    },
    "required": [
        "nota_aderencia",
        "classificacao",
        "pontos_fortes",
        "pontos_atencao",
        "recomendacao_rh",
    ],
}

INSTRUCAO_SISTEMA = (
    "Você é um assistente técnico de Talent Acquisition. "
    "Sua função é apoiar a triagem inicial comparando currículos anonimizados com os requisitos da vaga, "
    "sem tomar decisão final sozinho e evitando qualquer viés pessoal. "
    "Atenção especial às regras de estágio no Brasil (exige matrícula ativa em curso superior/técnico) "
    "e à compatibilidade de turno de estudo com o horário do estágio."
)


# ==============================================================================
# BLOCO 1: Carregamento de arquivos (vaga e currículos)
# ==============================================================================
def carregar_dados(pasta_raiz):
    caminho_vaga = os.path.join(pasta_raiz, "data", "vagas_requisitos.json")
    pasta_curriculos = os.path.join(pasta_raiz, "data", "curriculos_ficticios")

    with open(caminho_vaga, mode="r", encoding="utf-8") as f:
        vaga = json.load(f)

    curriculos = []
    for nome_arquivo in sorted(os.listdir(pasta_curriculos)):
        if nome_arquivo.endswith(".txt"):
            caminho_txt = os.path.join(pasta_curriculos, nome_arquivo)
            with open(caminho_txt, mode="r", encoding="utf-8") as f:
                codigo = os.path.splitext(nome_arquivo)[0]
                curriculos.append((codigo, f.read()))

    return vaga, curriculos


# ==============================================================================
# BLOCO 2: Consulta à API do Gemini com saída JSON estruturada e fallback
# ==============================================================================
MODELOS_TRIAGEM = ["gemini-3.5-flash-lite", "gemini-4-hydrogen"]


def avaliar_curriculo(cliente, vaga, codigo_candidato, texto_curriculo):
    prompt = f"""
Analise o currículo anonimizado abaixo para a vaga informada.

DADOS DA VAGA:
- Título: {vaga['titulo_vaga']}
- Modalidade e Horário: {vaga['modalidade']}
- Requisitos Obrigatórios: {', '.join(vaga['requisitos_obrigatorios'])}
- Requisitos Desejáveis: {', '.join(vaga['requisitos_desejaveis'])}

CURRÍCULO ({codigo_candidato}):
{texto_curriculo}
"""

    ultimo_erro = None
    for modelo in MODELOS_TRIAGEM:
        try:
            interacao = cliente.interactions.create(
                model=modelo,
                system_instruction=INSTRUCAO_SISTEMA,
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": ESQUEMA_TRIAGEM,
                },
            )
            dados_json = json.loads(interacao.output_text)
            dados_json["codigo_candidato"] = codigo_candidato
            dados_json["vaga_avaliada"] = vaga["titulo_vaga"]
            return dados_json
        except Exception as erro:
            ultimo_erro = erro
            continue

    raise RuntimeError(f"Falha ao avaliar {codigo_candidato} em todos os modelos: {ultimo_erro}")


# ==============================================================================
# BLOCO 3: Execução principal e exportação para CSV
# ==============================================================================
def main():
    pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(pasta_raiz, ".env"), override=True)

    chave_api = os.getenv("GEMINI_API_KEY", "").strip()
    if not chave_api or chave_api == "COLE_SUA_CHAVE_AQUI":
        print("ERRO: Abra o arquivo .env na pasta do projeto, cole sua GEMINI_API_KEY e salve!")
        return

    cliente = genai.Client(api_key=chave_api)
    vaga, curriculos = carregar_dados(pasta_raiz)

    print(f"Iniciando triagem assistida para: {vaga['titulo_vaga']}")
    print("-" * 70)

    resultados = []
    for codigo, texto in curriculos:
        print(f"Avaliando {codigo}...", end=" ", flush=True)
        avaliacao = avaliar_curriculo(cliente, vaga, codigo, texto)
        resultados.append(avaliacao)
        print(
            f"Nota: {avaliacao['nota_aderencia']}/100 | "
            f"{avaliacao['classificacao']} -> {avaliacao['recomendacao_rh']}"
        )

    # Ordena da maior nota para a menor para facilitar a leitura do recrutador
    resultados.sort(key=lambda r: r["nota_aderencia"], reverse=True)

    caminho_saida = os.path.join(pasta_raiz, "output", "triagem_ia_resultado.csv")
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)

    colunas = [
        "codigo_candidato",
        "vaga_avaliada",
        "nota_aderencia",
        "classificacao",
        "recomendacao_rh",
        "pontos_fortes",
        "pontos_atencao",
    ]
    with open(caminho_saida, mode="w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(resultados)

    print("-" * 70)
    print(f"Concluído! Resultado salvo em: {caminho_saida}")


if __name__ == "__main__":
    main()
