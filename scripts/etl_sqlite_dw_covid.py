#!/usr/bin/env python3
"""ETL SQLite para o DW de notificações de COVID-19 do ES.

Uso:
    python scripts/etl_sqlite_dw_covid.py --csv MICRODADOS.csv --reset
"""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
import unicodedata
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "sql" / "schema_sqlite.sql"

STAGING_COLUMNS = [
    "data_notificacao",
    "data_cadastro",
    "data_diagnostico",
    "data_coleta_rt_pcr",
    "data_coleta_teste_rap",
    "data_coleta_sorologia",
    "data_coleta_sorolog_igg",
    "data_encerramento",
    "data_obito",
    "classificacao",
    "evolucao",
    "criterio_confirmacao",
    "status_notificacao",
    "municipio",
    "bairro",
    "faixa_etaria",
    "idade_na_notificacao",
    "sexo",
    "raca_cor",
    "escolaridade",
    "gestante",
    "febre",
    "dif_respiratoria",
    "tosse",
    "coriza",
    "dor_garganta",
    "diarreia",
    "cefaleia",
    "com_pulmao",
    "com_cardio",
    "com_renal",
    "com_diabetes",
    "com_tabagismo",
    "com_obesidade",
    "ficou_internado",
    "viagem_brasil",
    "viagem_internacional",
    "profissional_saude",
    "possui_deficiencia",
    "morador_rua",
    "resultado_rt_pcr",
    "resultado_teste_rap",
    "resultado_sorologia",
    "resultado_sorol_igg",
    "tipo_teste_rapido",
]

DATE_COLUMNS = [
    "data_notificacao",
    "data_cadastro",
    "data_diagnostico",
    "data_coleta_rt_pcr",
    "data_coleta_teste_rap",
    "data_coleta_sorologia",
    "data_coleta_sorolog_igg",
    "data_encerramento",
    "data_obito",
]

MES_NOMES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Marco",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

DIA_SEMANA_NOMES = {
    1: "Segunda",
    2: "Terca",
    3: "Quarta",
    4: "Quinta",
    5: "Sexta",
    6: "Sabado",
    7: "Domingo",
}


def keyize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")


HEADER_ALIASES = {
    keyize("DataNotificacao"): "data_notificacao",
    keyize("DataCadastro"): "data_cadastro",
    keyize("DataDiagnostico"): "data_diagnostico",
    keyize("DataColeta_RT_PCR"): "data_coleta_rt_pcr",
    keyize("DataColetaRTPCR"): "data_coleta_rt_pcr",
    keyize("DataColetaTesteRapido"): "data_coleta_teste_rap",
    keyize("DataColetaTesteRap"): "data_coleta_teste_rap",
    keyize("DataColetaSorologia"): "data_coleta_sorologia",
    keyize("DataColetaSorologiaIGG"): "data_coleta_sorolog_igg",
    keyize("DataColetaSorologIGG"): "data_coleta_sorolog_igg",
    keyize("DataEncerramento"): "data_encerramento",
    keyize("DataObito"): "data_obito",
    keyize("Classificacao"): "classificacao",
    keyize("Evolucao"): "evolucao",
    keyize("CriterioConfirmacao"): "criterio_confirmacao",
    keyize("StatusNotificacao"): "status_notificacao",
    keyize("Municipio"): "municipio",
    keyize("Bairro"): "bairro",
    keyize("FaixaEtaria"): "faixa_etaria",
    keyize("IdadeNaDataNotificacao"): "idade_na_notificacao",
    keyize("Sexo"): "sexo",
    keyize("RacaCor"): "raca_cor",
    keyize("Escolaridade"): "escolaridade",
    keyize("Gestante"): "gestante",
    keyize("Febre"): "febre",
    keyize("DificuldadeRespiratoria"): "dif_respiratoria",
    keyize("DifRespiratoria"): "dif_respiratoria",
    keyize("Tosse"): "tosse",
    keyize("Coriza"): "coriza",
    keyize("DorGarganta"): "dor_garganta",
    keyize("Diarreia"): "diarreia",
    keyize("Cefaleia"): "cefaleia",
    keyize("ComorbidadePulmao"): "com_pulmao",
    keyize("ComorbidadeCardio"): "com_cardio",
    keyize("ComorbidadeRenal"): "com_renal",
    keyize("ComorbidadeDiabetes"): "com_diabetes",
    keyize("ComorbidadeTabagismo"): "com_tabagismo",
    keyize("ComorbidadeObesidade"): "com_obesidade",
    keyize("FicouInternado"): "ficou_internado",
    keyize("ViagemBrasil"): "viagem_brasil",
    keyize("ViagemInternacional"): "viagem_internacional",
    keyize("ProfissionalSaude"): "profissional_saude",
    keyize("PossuiDeficiencia"): "possui_deficiencia",
    keyize("MoradorDeRua"): "morador_rua",
    keyize("ResultadoRT_PCR"): "resultado_rt_pcr",
    keyize("ResultadoRTPCR"): "resultado_rt_pcr",
    keyize("ResultadoTesteRapido"): "resultado_teste_rap",
    keyize("ResultadoTesteRap"): "resultado_teste_rap",
    keyize("ResultadoSorologia"): "resultado_sorologia",
    keyize("ResultadoSorologia_IGG"): "resultado_sorol_igg",
    keyize("ResultadoSorologiaIGG"): "resultado_sorol_igg",
    keyize("ResultadoSorolIGG"): "resultado_sorol_igg",
    keyize("TipoTesteRapido"): "tipo_teste_rapido",
}

for column in STAGING_COLUMNS:
    HEADER_ALIASES[keyize(column)] = column


def norm_text(value: object, default: str = "Desconhecido") -> str:
    text = "" if value is None else str(value).strip()
    return text if text else default


def clean_raw(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_date(value: object) -> date | None:
    text = clean_raw(value)
    if not text:
        return None

    text = text.split(" ")[0].split("T")[0]
    formats = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d")
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def sk_from_date(value: object) -> int:
    parsed = parse_date(value)
    return int(parsed.strftime("%Y%m%d")) if parsed else -1


def first_valid_date(values: Iterable[object]) -> date | None:
    for value in values:
        parsed = parse_date(value)
        if parsed:
            return parsed
    return None


def days_between(start: object, end: object) -> int | None:
    start_date = parse_date(start)
    end_date = parse_date(end)
    if not start_date or not end_date:
        return None
    return (end_date - start_date).days


def parse_age(value: object) -> int | None:
    text = clean_raw(value)
    if not text:
        return None
    match = re.search(r"-?\d+", text)
    if not match:
        return None
    age = int(match.group(0))
    return age if 0 <= age <= 130 else None


def flag_equals(value: object, expected: str) -> int:
    return int(keyize(clean_raw(value)) == keyize(expected))


def canonical_row(raw_row: dict[str, str], header_map: dict[str, str]) -> dict[str, str]:
    row = {column: "" for column in STAGING_COLUMNS}
    for original, value in raw_row.items():
        canonical = header_map.get(original)
        if canonical:
            row[canonical] = clean_raw(value)
    return row


def open_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def table_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def build_header_map(fieldnames: list[str] | None) -> dict[str, str]:
    if not fieldnames:
        raise ValueError("CSV sem cabeçalho.")

    header_map: dict[str, str] = {}
    for field in fieldnames:
        canonical = HEADER_ALIASES.get(keyize(field))
        if canonical:
            header_map[field] = canonical

    missing = sorted(set(STAGING_COLUMNS) - set(header_map.values()))
    if missing:
        print(
            "Aviso: colunas não encontradas no CSV e serão tratadas como vazias: "
            + ", ".join(missing),
            file=sys.stderr,
        )
    return header_map


def localidade_key(row: dict[str, str]) -> tuple[str, str]:
    return (
        norm_text(row["municipio"], "Desconhecido"),
        norm_text(row["bairro"], "Desconhecido"),
    )


def perfil_key(row: dict[str, str]) -> tuple[str, ...]:
    return (
        norm_text(row["sexo"], "Desconhecido"),
        norm_text(row["faixa_etaria"], "Desconhecida"),
        norm_text(row["raca_cor"], "Desconhecida"),
        norm_text(row["escolaridade"], "Desconhecida"),
        norm_text(row["gestante"], "Desconhecido"),
        norm_text(row["profissional_saude"], "Desconhecido"),
        norm_text(row["morador_rua"], "Desconhecido"),
        norm_text(row["possui_deficiencia"], "Desconhecido"),
    )


def classificacao_key(row: dict[str, str]) -> tuple[str, ...]:
    return (
        norm_text(row["classificacao"], "Desconhecida"),
        norm_text(row["evolucao"], "Desconhecida"),
        norm_text(row["criterio_confirmacao"], "Desconhecido"),
        norm_text(row["status_notificacao"], "Desconhecido"),
    )


def sintomas_key(row: dict[str, str]) -> tuple[str, ...]:
    return (
        norm_text(row["febre"], "Desconhecido"),
        norm_text(row["dif_respiratoria"], "Desconhecido"),
        norm_text(row["tosse"], "Desconhecido"),
        norm_text(row["coriza"], "Desconhecido"),
        norm_text(row["dor_garganta"], "Desconhecido"),
        norm_text(row["diarreia"], "Desconhecido"),
        norm_text(row["cefaleia"], "Desconhecido"),
    )


def comorbidade_key(row: dict[str, str]) -> tuple[str, ...]:
    return (
        norm_text(row["com_pulmao"], "Desconhecido"),
        norm_text(row["com_cardio"], "Desconhecido"),
        norm_text(row["com_renal"], "Desconhecido"),
        norm_text(row["com_diabetes"], "Desconhecido"),
        norm_text(row["com_tabagismo"], "Desconhecido"),
        norm_text(row["com_obesidade"], "Desconhecido"),
    )


def teste_key(row: dict[str, str]) -> tuple[str, ...]:
    return (
        norm_text(row["tipo_teste_rapido"], "Desconhecido"),
        norm_text(row["resultado_rt_pcr"], "Desconhecido"),
        norm_text(row["resultado_teste_rap"], "Desconhecido"),
        norm_text(row["resultado_sorologia"], "Desconhecido"),
        norm_text(row["resultado_sorol_igg"], "Desconhecido"),
    )


def insert_many(
    conn: sqlite3.Connection,
    table: str,
    columns: list[str],
    rows: Iterable[tuple[object, ...]],
) -> None:
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(columns)
    conn.executemany(
        f"INSERT OR IGNORE INTO {table} ({column_sql}) VALUES ({placeholders})",
        rows,
    )


def load_staging_and_collect_dimensions(
    conn: sqlite3.Connection,
    csv_path: Path,
    encoding: str,
    delimiter: str,
    batch_size: int,
) -> dict[str, set[tuple[object, ...]]]:
    collections: dict[str, set[tuple[object, ...]]] = {
        "localidade": set(),
        "perfil": set(),
        "classificacao": set(),
        "sintomas": set(),
        "comorbidade": set(),
        "teste": set(),
        "datas": set(),
    }

    placeholders = ", ".join("?" for _ in STAGING_COLUMNS)
    insert_sql = (
        f"INSERT INTO stg_notificacao_raw ({', '.join(STAGING_COLUMNS)}) "
        f"VALUES ({placeholders})"
    )

    total = 0
    batch: list[tuple[str, ...]] = []
    with csv_path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        header_map = build_header_map(reader.fieldnames)
        for raw_row in reader:
            row = canonical_row(raw_row, header_map)
            batch.append(tuple(row[column] for column in STAGING_COLUMNS))

            collections["localidade"].add(localidade_key(row))
            collections["perfil"].add(perfil_key(row))
            collections["classificacao"].add(classificacao_key(row))
            collections["sintomas"].add(sintomas_key(row))
            collections["comorbidade"].add(comorbidade_key(row))
            collections["teste"].add(teste_key(row))
            for column in DATE_COLUMNS:
                parsed = parse_date(row[column])
                if parsed:
                    collections["datas"].add((parsed,))

            if len(batch) >= batch_size:
                conn.executemany(insert_sql, batch)
                total += len(batch)
                print(f"Staging: {total:,} linhas carregadas".replace(",", "."))
                batch.clear()

        if batch:
            conn.executemany(insert_sql, batch)
            total += len(batch)
            print(f"Staging: {total:,} linhas carregadas".replace(",", "."))

    return collections


def date_dimension_row(day: date) -> tuple[object, ...]:
    iso_year, iso_week, _ = day.isocalendar()
    return (
        int(day.strftime("%Y%m%d")),
        day.isoformat(),
        day.day,
        day.month,
        day.year,
        ((day.month - 1) // 3) + 1,
        MES_NOMES[day.month],
        DIA_SEMANA_NOMES[day.isoweekday()],
        day.strftime("%Y-%m"),
        1 if day.isoweekday() >= 6 else 0,
        iso_week if iso_year == day.year else iso_week,
    )


def populate_time_dimension(conn: sqlite3.Connection, extra_dates: set[tuple[object, ...]]) -> None:
    rows: list[tuple[object, ...]] = []
    start = date(2020, 1, 1).toordinal()
    end = date(2026, 12, 31).toordinal()
    for ordinal in range(start, end + 1):
        rows.append(date_dimension_row(date.fromordinal(ordinal)))

    for (extra_date,) in extra_dates:
        if isinstance(extra_date, date):
            rows.append(date_dimension_row(extra_date))

    insert_many(
        conn,
        "dim_tempo",
        [
            "sk_tempo",
            "data",
            "dia",
            "mes",
            "ano",
            "trimestre",
            "nome_mes",
            "dia_semana",
            "ano_mes",
            "eh_fim_de_semana",
            "semana_epidemiologica",
        ],
        rows,
    )


def populate_dimensions(conn: sqlite3.Connection, collections: dict[str, set[tuple[object, ...]]]) -> None:
    populate_time_dimension(conn, collections["datas"])

    insert_many(
        conn,
        "dim_localidade",
        ["municipio", "bairro", "uf", "regiao_es", "macrorregiao"],
        [(municipio, bairro, "ES", "Desconhecida", "Desconhecida") for municipio, bairro in collections["localidade"]],
    )
    insert_many(
        conn,
        "dim_perfil_paciente",
        [
            "sexo",
            "faixa_etaria",
            "raca_cor",
            "escolaridade",
            "gestante",
            "profissional_saude",
            "morador_rua",
            "possui_deficiencia",
        ],
        collections["perfil"],
    )
    insert_many(
        conn,
        "dim_classificacao",
        ["classificacao", "evolucao", "criterio_confirmacao", "status_notificacao"],
        collections["classificacao"],
    )
    insert_many(
        conn,
        "dim_sintomas",
        ["febre", "dif_respiratoria", "tosse", "coriza", "dor_garganta", "diarreia", "cefaleia"],
        collections["sintomas"],
    )
    insert_many(
        conn,
        "dim_comorbidade",
        ["com_pulmao", "com_cardio", "com_renal", "com_diabetes", "com_tabagismo", "com_obesidade"],
        collections["comorbidade"],
    )
    insert_many(
        conn,
        "dim_teste",
        [
            "tipo_teste_rapido",
            "resultado_rt_pcr",
            "resultado_teste_rap",
            "resultado_sorologia",
            "resultado_sorol_igg",
        ],
        collections["teste"],
    )


def cache_dimension(
    conn: sqlite3.Connection,
    table: str,
    key_columns: list[str],
    sk_column: str,
) -> dict[tuple[object, ...], int]:
    column_sql = ", ".join([sk_column, *key_columns])
    rows = conn.execute(f"SELECT {column_sql} FROM {table}").fetchall()
    return {tuple(row[1:]): int(row[0]) for row in rows}


def row_from_sqlite(columns: list[str], values: sqlite3.Row) -> dict[str, str]:
    return {column: clean_raw(values[column]) for column in columns}


def load_fact(conn: sqlite3.Connection, batch_size: int) -> None:
    conn.row_factory = sqlite3.Row
    source = conn.cursor()

    local_cache = cache_dimension(conn, "dim_localidade", ["municipio", "bairro"], "sk_local")
    perfil_cache = cache_dimension(
        conn,
        "dim_perfil_paciente",
        [
            "sexo",
            "faixa_etaria",
            "raca_cor",
            "escolaridade",
            "gestante",
            "profissional_saude",
            "morador_rua",
            "possui_deficiencia",
        ],
        "sk_perfil",
    )
    class_cache = cache_dimension(
        conn,
        "dim_classificacao",
        ["classificacao", "evolucao", "criterio_confirmacao", "status_notificacao"],
        "sk_class",
    )
    sint_cache = cache_dimension(
        conn,
        "dim_sintomas",
        ["febre", "dif_respiratoria", "tosse", "coriza", "dor_garganta", "diarreia", "cefaleia"],
        "sk_sint",
    )
    como_cache = cache_dimension(
        conn,
        "dim_comorbidade",
        ["com_pulmao", "com_cardio", "com_renal", "com_diabetes", "com_tabagismo", "com_obesidade"],
        "sk_como",
    )
    teste_cache = cache_dimension(
        conn,
        "dim_teste",
        ["tipo_teste_rapido", "resultado_rt_pcr", "resultado_teste_rap", "resultado_sorologia", "resultado_sorol_igg"],
        "sk_teste",
    )

    fact_columns = [
        "sk_data_notificacao",
        "sk_data_cadastro",
        "sk_data_diagnostico",
        "sk_data_coleta",
        "sk_data_encerramento",
        "sk_data_obito",
        "sk_local",
        "sk_perfil",
        "sk_class",
        "sk_sint",
        "sk_como",
        "sk_teste",
        "qtd_notificacao",
        "flag_confirmado",
        "flag_obito_covid",
        "flag_internado",
        "flag_cura",
        "idade_anos",
        "dias_notif_encerramento",
        "dias_notif_obito",
    ]
    insert_sql = (
        f"INSERT INTO fato_notificacao_covid ({', '.join(fact_columns)}) "
        f"VALUES ({', '.join('?' for _ in fact_columns)})"
    )

    total = 0
    batch: list[tuple[object, ...]] = []
    select_sql = f"SELECT {', '.join(STAGING_COLUMNS)} FROM stg_notificacao_raw ORDER BY id_stg"
    for values in source.execute(select_sql):
        row = row_from_sqlite(STAGING_COLUMNS, values)
        data_coleta = first_valid_date(
            [
                row["data_coleta_rt_pcr"],
                row["data_coleta_teste_rap"],
                row["data_coleta_sorologia"],
                row["data_coleta_sorolog_igg"],
            ]
        )

        batch.append(
            (
                sk_from_date(row["data_notificacao"]),
                sk_from_date(row["data_cadastro"]),
                sk_from_date(row["data_diagnostico"]),
                int(data_coleta.strftime("%Y%m%d")) if data_coleta else -1,
                sk_from_date(row["data_encerramento"]),
                sk_from_date(row["data_obito"]),
                local_cache.get(localidade_key(row), -1),
                perfil_cache.get(perfil_key(row), -1),
                class_cache.get(classificacao_key(row), -1),
                sint_cache.get(sintomas_key(row), -1),
                como_cache.get(comorbidade_key(row), -1),
                teste_cache.get(teste_key(row), -1),
                1,
                flag_equals(row["classificacao"], "Confirmados"),
                flag_equals(row["evolucao"], "Obito pelo COVID-19"),
                flag_equals(row["ficou_internado"], "Sim"),
                flag_equals(row["evolucao"], "Cura"),
                parse_age(row["idade_na_notificacao"]),
                days_between(row["data_notificacao"], row["data_encerramento"]),
                days_between(row["data_notificacao"], row["data_obito"]),
            )
        )

        if len(batch) >= batch_size:
            conn.executemany(insert_sql, batch)
            total += len(batch)
            print(f"Fato: {total:,} linhas carregadas".replace(",", "."))
            batch.clear()

    if batch:
        conn.executemany(insert_sql, batch)
        total += len(batch)
        print(f"Fato: {total:,} linhas carregadas".replace(",", "."))


def refresh_mart(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS mart_covid_municipio_mes;
        CREATE TABLE mart_covid_municipio_mes AS
        SELECT
            l.municipio,
            t.ano_mes,
            SUM(f.flag_confirmado) AS confirmados,
            SUM(f.flag_obito_covid) AS obitos,
            SUM(f.flag_internado) AS internacoes,
            SUM(f.qtd_notificacao) AS notificacoes_total
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        GROUP BY l.municipio, t.ano_mes;

        CREATE INDEX IF NOT EXISTS idx_mart_covid_municipio_mes
        ON mart_covid_municipio_mes (municipio, ano_mes);
        """
    )


def validate_counts(conn: sqlite3.Connection) -> None:
    origem = table_count(conn, "stg_notificacao_raw")
    fato = table_count(conn, "fato_notificacao_covid")
    print(f"Validação: staging={origem:,} fato={fato:,}".replace(",", "."))
    if origem != fato:
        raise RuntimeError("Falha de validação: contagem da fato diferente da staging.")


def run(args: argparse.Namespace) -> None:
    csv_path = Path(args.csv).resolve()
    db_path = Path(args.db).resolve()
    db_existed = db_path.exists()

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {csv_path}")

    conn = open_connection(db_path)
    try:
        if args.reset or not db_existed:
            print("Criando schema SQLite...")
            init_schema(conn)
        elif table_count(conn, "stg_notificacao_raw") > 0:
            raise RuntimeError(
                "O banco já contém dados. Use --reset para recriar tudo antes da carga."
            )

        with conn:
            print("Carregando staging e coletando dimensões...")
            collections = load_staging_and_collect_dimensions(
                conn,
                csv_path,
                args.encoding,
                args.delimiter,
                args.batch_size,
            )

        with conn:
            print("Populando dimensões...")
            populate_dimensions(conn, collections)

        with conn:
            print("Carregando tabela fato...")
            load_fact(conn, args.batch_size)

        with conn:
            print("Atualizando data mart...")
            refresh_mart(conn)

        validate_counts(conn)
        print(f"DW carregado com sucesso em: {db_path}")
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Carrega MICRODADOS.csv em um DW SQLite.")
    parser.add_argument("--csv", required=True, help="Caminho para o MICRODADOS.csv.")
    parser.add_argument("--db", default="dw_covid.sqlite", help="Arquivo SQLite de saída.")
    parser.add_argument("--encoding", default="latin-1", help="Encoding do CSV. Padrão: latin-1.")
    parser.add_argument("--delimiter", default=";", help="Separador do CSV. Padrão: ponto e vírgula.")
    parser.add_argument("--batch-size", type=int, default=10_000, help="Tamanho dos lotes de INSERT.")
    parser.add_argument("--reset", action="store_true", help="Recria todas as tabelas antes da carga.")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        run(parse_args())
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
