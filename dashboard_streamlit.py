#!/usr/bin/env python3
"""Dashboard Streamlit para o DW COVID-19 ES."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


DB_PATH = Path("dw_covid.sqlite")


st.set_page_config(
    page_title="DW COVID-19 ES",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def consultar(sql: str, params: tuple[object, ...] = ()) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def banco_disponivel() -> bool:
    return DB_PATH.exists()


st.title("Data Warehouse COVID-19 ES")

if not banco_disponivel():
    st.error("Banco `dw_covid.sqlite` não encontrado.")
    st.code("python scripts/etl_sqlite_dw_covid.py --csv MICRODADOS.csv --reset")
    st.stop()

municipios = consultar(
    """
    SELECT DISTINCT municipio
    FROM dim_localidade
    WHERE sk_local <> -1
    ORDER BY municipio
    """
)["municipio"].tolist()

anos = consultar(
    """
    SELECT DISTINCT ano
    FROM dim_tempo
    WHERE ano IS NOT NULL
    ORDER BY ano
    """
)["ano"].tolist()

col_filtro_1, col_filtro_2 = st.columns([2, 1])
with col_filtro_1:
    municipio = st.selectbox("Município", ["Todos", *municipios])
with col_filtro_2:
    ano = st.selectbox("Ano", ["Todos", *anos])

where = ["1 = 1"]
params: list[object] = []
if municipio != "Todos":
    where.append("l.municipio = ?")
    params.append(municipio)
if ano != "Todos":
    where.append("t.ano = ?")
    params.append(ano)
where_sql = " AND ".join(where)

indicadores = consultar(
    f"""
    SELECT
        SUM(f.qtd_notificacao) AS notificacoes,
        SUM(f.flag_confirmado) AS confirmados,
        SUM(f.flag_obito_covid) AS obitos,
        SUM(f.flag_internado) AS internacoes
    FROM fato_notificacao_covid f
    JOIN dim_localidade l ON l.sk_local = f.sk_local
    JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
    WHERE {where_sql}
    """,
    tuple(params),
).fillna(0)

notificacoes = int(indicadores.loc[0, "notificacoes"])
confirmados = int(indicadores.loc[0, "confirmados"])
obitos = int(indicadores.loc[0, "obitos"])
internacoes = int(indicadores.loc[0, "internacoes"])
letalidade = 100 * obitos / confirmados if confirmados else 0

kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = st.columns(5)
kpi_1.metric("Notificações", f"{notificacoes:,}".replace(",", "."))
kpi_2.metric("Confirmados", f"{confirmados:,}".replace(",", "."))
kpi_3.metric("Óbitos", f"{obitos:,}".replace(",", "."))
kpi_4.metric("Internações", f"{internacoes:,}".replace(",", "."))
kpi_5.metric("Letalidade", f"{letalidade:.2f}%")

tab_temporal, tab_municipios, tab_perfil, tab_comorbidades = st.tabs(
    ["Série temporal", "Municípios", "Pirâmide etária", "Comorbidades"]
)

with tab_temporal:
    serie = consultar(
        f"""
        SELECT
            t.ano_mes,
            SUM(f.qtd_notificacao) AS notificacoes,
            SUM(f.flag_confirmado) AS confirmados,
            SUM(f.flag_obito_covid) AS obitos
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        WHERE {where_sql}
          AND t.ano_mes <> 'N/D'
        GROUP BY t.ano_mes
        ORDER BY t.ano_mes
        """,
        tuple(params),
    )
    st.line_chart(serie, x="ano_mes", y=["notificacoes", "confirmados", "obitos"])
    st.dataframe(serie, use_container_width=True, hide_index=True)

with tab_municipios:
    ranking = consultar(
        """
        SELECT
            l.municipio,
            SUM(f.flag_confirmado) AS confirmados,
            SUM(f.flag_obito_covid) AS obitos,
            SUM(f.flag_internado) AS internacoes,
            SUM(f.qtd_notificacao) AS notificacoes
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        WHERE l.sk_local <> -1
        GROUP BY l.municipio
        ORDER BY confirmados DESC
        LIMIT 20
        """
    )
    heatmap = consultar(
        """
        WITH top_municipios AS (
            SELECT
                l.municipio,
                SUM(f.flag_confirmado) AS confirmados
            FROM fato_notificacao_covid f
            JOIN dim_localidade l ON l.sk_local = f.sk_local
            WHERE l.sk_local <> -1
            GROUP BY l.municipio
            ORDER BY confirmados DESC
            LIMIT 20
        )
        SELECT
            l.municipio,
            t.ano_mes,
            SUM(f.flag_confirmado) AS confirmados
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        JOIN top_municipios tm ON tm.municipio = l.municipio
        WHERE t.ano_mes <> 'N/D'
        GROUP BY l.municipio, t.ano_mes
        ORDER BY t.ano_mes, l.municipio
        """
    )
    grafico_heatmap = (
        alt.Chart(heatmap)
        .mark_rect()
        .encode(
            x=alt.X("ano_mes:N", title="Mês"),
            y=alt.Y("municipio:N", title="Município", sort="-x"),
            color=alt.Color("confirmados:Q", title="Confirmados"),
            tooltip=["municipio", "ano_mes", "confirmados"],
        )
        .properties(height=520)
    )
    st.altair_chart(grafico_heatmap, use_container_width=True)
    st.subheader("Ranking de municípios")
    st.dataframe(ranking, use_container_width=True, hide_index=True)

with tab_perfil:
    perfil_params = list(params)
    piramide = consultar(
        f"""
        SELECT
            p.faixa_etaria,
            p.sexo,
            SUM(f.flag_obito_covid) AS obitos
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        JOIN dim_perfil_paciente p ON p.sk_perfil = f.sk_perfil
        WHERE {where_sql}
        GROUP BY p.faixa_etaria, p.sexo
        ORDER BY p.faixa_etaria, p.sexo
        """,
        tuple(perfil_params),
    )
    piramide["sexo_plot"] = piramide["sexo"].str.upper().str[0]
    piramide = piramide[piramide["sexo_plot"].isin(["F", "M"])].copy()
    piramide["obitos_plot"] = piramide.apply(
        lambda linha: -linha["obitos"] if linha["sexo_plot"] == "M" else linha["obitos"],
        axis=1,
    )
    grafico_piramide = (
        alt.Chart(piramide)
        .mark_bar()
        .encode(
            y=alt.Y("faixa_etaria:N", title="Faixa etária", sort=None),
            x=alt.X("obitos_plot:Q", title="Óbitos"),
            color=alt.Color("sexo_plot:N", title="Sexo"),
            tooltip=["faixa_etaria", "sexo", "obitos"],
        )
        .properties(height=460)
    )
    st.altair_chart(grafico_piramide, use_container_width=True)
    st.dataframe(piramide[["faixa_etaria", "sexo", "obitos"]], use_container_width=True, hide_index=True)

with tab_comorbidades:
    comorbidades = consultar(
        f"""
        SELECT 'Cardio' AS comorbidade, c.com_cardio AS valor, SUM(f.flag_obito_covid) AS obitos
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        JOIN dim_comorbidade c ON c.sk_como = f.sk_como
        WHERE {where_sql}
        GROUP BY c.com_cardio
        UNION ALL
        SELECT 'Diabetes', c.com_diabetes, SUM(f.flag_obito_covid)
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        JOIN dim_comorbidade c ON c.sk_como = f.sk_como
        WHERE {where_sql}
        GROUP BY c.com_diabetes
        UNION ALL
        SELECT 'Obesidade', c.com_obesidade, SUM(f.flag_obito_covid)
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        JOIN dim_comorbidade c ON c.sk_como = f.sk_como
        WHERE {where_sql}
        GROUP BY c.com_obesidade
        UNION ALL
        SELECT 'Pulmão', c.com_pulmao, SUM(f.flag_obito_covid)
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        JOIN dim_comorbidade c ON c.sk_como = f.sk_como
        WHERE {where_sql}
        GROUP BY c.com_pulmao
        UNION ALL
        SELECT 'Renal', c.com_renal, SUM(f.flag_obito_covid)
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        JOIN dim_comorbidade c ON c.sk_como = f.sk_como
        WHERE {where_sql}
        GROUP BY c.com_renal
        UNION ALL
        SELECT 'Tabagismo', c.com_tabagismo, SUM(f.flag_obito_covid)
        FROM fato_notificacao_covid f
        JOIN dim_localidade l ON l.sk_local = f.sk_local
        JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
        JOIN dim_comorbidade c ON c.sk_como = f.sk_como
        WHERE {where_sql}
        GROUP BY c.com_tabagismo
        """,
        tuple(params * 6),
    )
    top = (
        comorbidades[comorbidades["valor"].str.lower().eq("sim")]
        .groupby("comorbidade", as_index=False)["obitos"]
        .sum()
        .sort_values("obitos", ascending=False)
        .head(5)
    )
    st.bar_chart(top, x="comorbidade", y="obitos")
    st.dataframe(top, use_container_width=True, hide_index=True)
