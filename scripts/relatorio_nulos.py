#!/usr/bin/env python3
"""Gera relatório de valores ausentes do MICRODADOS.csv."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


VALORES_NULOS = {"", "nan", "none", "null"}


def eh_nulo(valor: object) -> bool:
    if valor is None:
        return True
    return str(valor).strip().lower() in VALORES_NULOS


def gerar_relatorio(
    csv_path: Path,
    output_path: Path,
    encoding: str,
    delimiter: str,
) -> None:
    total_linhas = 0
    nulos: dict[str, int] = {}

    with csv_path.open("r", encoding=encoding, newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=delimiter)
        if not leitor.fieldnames:
            raise ValueError("CSV sem cabeçalho.")

        colunas = list(leitor.fieldnames)
        nulos = {coluna: 0 for coluna in colunas}

        for linha in leitor:
            total_linhas += 1
            for coluna in colunas:
                if eh_nulo(linha.get(coluna)):
                    nulos[coluna] += 1

            if total_linhas % 500_000 == 0:
                print(f"Processadas {total_linhas:,} linhas".replace(",", "."))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(["coluna", "total_nulos", "percentual_nulos"])
        for coluna in sorted(colunas, key=lambda nome: nulos[nome], reverse=True):
            percentual = 100 * nulos[coluna] / total_linhas if total_linhas else 0
            escritor.writerow([coluna, nulos[coluna], f"{percentual:.4f}"])

    print(f"Relatório gerado em: {output_path}")
    print(f"Total de linhas analisadas: {total_linhas:,}".replace(",", "."))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera percentual de nulos por coluna.")
    parser.add_argument("--csv", default="MICRODADOS.csv", help="Caminho do CSV de entrada.")
    parser.add_argument(
        "--out",
        default="docs/relatorio_nulos.csv",
        help="Arquivo CSV de saída do relatório.",
    )
    parser.add_argument("--encoding", default="latin-1", help="Encoding do CSV.")
    parser.add_argument("--delimiter", default=";", help="Separador do CSV.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        gerar_relatorio(
            Path(args.csv).resolve(),
            Path(args.out).resolve(),
            args.encoding,
            args.delimiter,
        )
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
