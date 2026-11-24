"""
Consolida os 3 arquivos CSV do projeto em uma única Pasta de Trabalho do Excel (.xlsx)
com 3 abas prontas para importação direta no Power BI Desktop.
"""

import csv
import os
from datetime import date
from openpyxl import Workbook


def converter_valor(coluna, valor):
    if coluna in ("dias_processo", "ordem_etapa_maxima", "ordem_etapa", "nota_aderencia"):
        return int(valor)
    if coluna in ("data_inscricao", "data_fechamento"):
        return date.fromisoformat(valor)
    return valor


def adicionar_aba_csv(wb, nome_aba, caminho_csv):
    ws = wb.create_sheet(title=nome_aba)
    with open(caminho_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.reader(f)
        cabecalho = next(leitor)
        ws.append(cabecalho)
        for linha in leitor:
            linha_convertida = [
                converter_valor(col, val) for col, val in zip(cabecalho, linha)
            ]
            ws.append(linha_convertida)


def main():
    pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wb = Workbook()
    # Remove a aba padrão vazia criada pelo openpyxl
    wb.remove(wb.active)

    adicionar_aba_csv(
        wb,
        "candidaturas_funil",
        os.path.join(pasta_raiz, "data", "candidaturas_funil.csv"),
    )
    adicionar_aba_csv(
        wb,
        "historico_etapas",
        os.path.join(pasta_raiz, "data", "historico_etapas.csv"),
    )
    adicionar_aba_csv(
        wb,
        "triagem_ia_resultado",
        os.path.join(pasta_raiz, "output", "triagem_ia_resultado.csv"),
    )

    caminho_xlsx = os.path.join(pasta_raiz, "data", "base_talent_acquisition.xlsx")
    wb.save(caminho_xlsx)
    print(f"Planilha Excel gerada com sucesso em: {caminho_xlsx}")


if __name__ == "__main__":
    main()
