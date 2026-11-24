"""
Gerador de base fictícia de Talent Acquisition para estudo de indicadores no Power BI.
Gera duas tabelas relacionadas por id_candidatura (relação 1:N no Power BI):
  1. data/candidaturas_funil.csv -> 1 linha por candidatura (240 candidatos)
  2. data/historico_etapas.csv   -> 1 linha por etapa pela qual o candidato passou (funil acumulado real)
"""

import csv
import os
import random
from datetime import date, timedelta

# Semente fixa para gerar sempre a mesma base caso o script seja rodado novamente
random.seed(42)

VAGAS = [
    ("Estágio em Dados & BI", "Tecnologia", (14, 26)),
    ("Estágio em Talent Acquisition", "Recursos Humanos", (15, 28)),
    ("Analista de Suporte de TI Jr", "Tecnologia", (18, 34)),
    ("Desenvolvedor Backend Pleno", "Tecnologia", (25, 45)),
    ("Estágio em Projetos & Digital", "Projetos & Digital", (16, 29)),
    ("Analista de Qualidade & Processos Jr", "Operações & Engenharia", (20, 38)),
]

ORIGENS = [
    ("LinkedIn", 0.40, -1),
    ("Portal de Carreiras", 0.25, 0),
    ("Gupy / Job Boards", 0.17, 2),
    ("Indicação Interna", 0.10, -4),
    ("Feira Universitária", 0.08, -2),
]

# Quantidade de candidatos cuja jornada parou em cada etapa máxima:
# Total = 240 -> Passam p/ Triagem: 135 -> Entrevista RH: 77 -> Gestor: 41 -> Contratados: 18
NOMES_ETAPAS = {
    1: "1. Inscritos",
    2: "2. Triagem Curricular",
    3: "3. Entrevista RH",
    4: "4. Entrevista Gestor",
    5: "5. Contratados",
}

DISTRIBUICAO_PARADA = [
    (1, 105),
    (2, 58),
    (3, 36),
    (4, 23),
    (5, 18),
]


def escolher_origem():
    nomes = [o[0] for o in ORIGENS]
    pesos = [o[1] for o in ORIGENS]
    escolhida = random.choices(nomes, weights=pesos, k=1)[0]
    ajuste_dias = dict((o[0], o[2]) for o in ORIGENS)[escolhida]
    return escolhida, ajuste_dias


def gerar_bases():
    data_inicio_periodo = date(2026, 6, 1)
    intervalo_dias = 140  # Junho a Outubro de 2026
    candidaturas = []
    historico_etapas = []
    contador = 1

    etapas_maximas = []
    for ordem_max, qtd in DISTRIBUICAO_PARADA:
        etapas_maximas.extend([ordem_max] * qtd)

    random.shuffle(etapas_maximas)

    for ordem_max in etapas_maximas:
        id_candidatura = f"CAND-{contador:04d}"
        contador += 1

        # Candidatos de Indicação Interna costumam avançar mais no funil
        if ordem_max >= 4 and random.random() < 0.28:
            origem, ajuste_origem = "Indicação Interna", -4
        else:
            origem, ajuste_origem = escolher_origem()

        vaga, area, faixa_dias = random.choice(VAGAS)
        data_inscricao = data_inicio_periodo + timedelta(days=random.randint(0, intervalo_dias))

        if ordem_max == 5:
            status_final = "Contratado"
            dias_base = random.randint(faixa_dias[0], faixa_dias[1])
            dias_processo = max(10, dias_base + ajuste_origem)
        else:
            status_final = random.choices(
                ["Reprovado", "Banco de Talentos", "Desistência"],
                weights=[0.68, 0.20, 0.12],
                k=1,
            )[0]
            dias_processo = random.randint(2 * ordem_max, 7 * ordem_max + 5)

        data_fechamento = data_inscricao + timedelta(days=dias_processo)

        candidaturas.append({
            "id_candidatura": id_candidatura,
            "vaga": vaga,
            "area": area,
            "origem_candidato": origem,
            "data_inscricao": data_inscricao.isoformat(),
            "data_fechamento": data_fechamento.isoformat(),
            "dias_processo": dias_processo,
            "ordem_etapa_maxima": ordem_max,
            "ultima_etapa": NOMES_ETAPAS[ordem_max],
            "status_final": status_final,
        })

        # Registra todas as etapas pelas quais esse candidato efetivamente passou (1 até ordem_max)
        for etapa_num in range(1, ordem_max + 1):
            historico_etapas.append({
                "id_candidatura": id_candidatura,
                "ordem_etapa": etapa_num,
                "etapa_funil": NOMES_ETAPAS[etapa_num],
            })

    return candidaturas, historico_etapas


def salvar_csv(registros, caminho_saida, colunas):
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    with open(caminho_saida, mode="w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(registros)


if __name__ == "__main__":
    pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_cand = os.path.join(pasta_raiz, "data", "candidaturas_funil.csv")
    caminho_hist = os.path.join(pasta_raiz, "data", "historico_etapas.csv")

    candidaturas, historico = gerar_bases()

    salvar_csv(
        candidaturas,
        caminho_cand,
        [
            "id_candidatura",
            "vaga",
            "area",
            "origem_candidato",
            "data_inscricao",
            "data_fechamento",
            "dias_processo",
            "ordem_etapa_maxima",
            "ultima_etapa",
            "status_final",
        ],
    )
    salvar_csv(
        historico,
        caminho_hist,
        ["id_candidatura", "ordem_etapa", "etapa_funil"],
    )

    print(f"Candidaturas geradas: {len(candidaturas)} linhas -> {caminho_cand}")
    print(f"Histórico do funil gerado: {len(historico)} linhas -> {caminho_hist}")
