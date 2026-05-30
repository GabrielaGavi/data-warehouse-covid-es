# Respostas dos exercícios

## 1. Análise exploratória

O relatório de nulos foi implementado em `scripts/relatorio_nulos.py`. Ele lê o
CSV em fluxo, sem carregar o arquivo inteiro em memória, e gera
`docs/relatorio_nulos.csv`.

```python
import pandas as pd

arquivo = "MICRODADOS.csv"
chunks = pd.read_csv(arquivo, sep=";", encoding="latin-1", chunksize=100_000)

total_linhas = 0
nulos = None

for chunk in chunks:
    total_linhas += len(chunk)
    parcial = chunk.isna().sum() + chunk.astype(str).eq("").sum()
    nulos = parcial if nulos is None else nulos.add(parcial, fill_value=0)

relatorio = (nulos / total_linhas * 100).sort_values(ascending=False)
print(relatorio)
```

## 2. Modelo floco de neve para localidade

No modelo estrela, `dim_localidade` concentra município, bairro, UF, região e
macrorregião. Isso facilita as consultas e reduz joins.

No floco de neve, a localidade poderia ser normalizada assim:

```text
dim_bairro -> dim_municipio -> dim_regiao_es -> dim_macrorregiao_saude
```

| Critério | Estrela | Floco de neve |
| --- | --- | --- |
| Consulta | Mais simples | Mais joins |
| Performance | Melhor para OLAP | Pode ser pior |
| Redundância | Maior | Menor |
| Manutenção | Mais simples | Mais controlada |

## 3. Nova fato: `fato_exame`

Grão: um exame realizado.

```text
fato_exame(
  id_fato_exame,
  sk_data_coleta,
  sk_local,
  sk_perfil,
  sk_teste,
  tipo_exame,
  resultado_exame,
  qtd_exame
)
```

Dimensões conformadas: `dim_tempo`, `dim_localidade`,
`dim_perfil_paciente` e `dim_teste`.

## 4. Data mart

No SQLite, a materialização foi feita como tabela:

```sql
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
```

Para avaliar o plano:

```sql
EXPLAIN QUERY PLAN
SELECT *
FROM mart_covid_municipio_mes
WHERE municipio = 'Vitoria' AND ano_mes = '2021-03';
```

## 5. Dashboard

O dashboard foi implementado em `dashboard_streamlit.py`, substituindo Power BI
por Streamlit. Ele contém:

- série temporal de notificações;
- mapa de calor por município;
- pirâmide etária dos óbitos;
- top 5 comorbidades em óbitos.

Execução:

```bash
streamlit run dashboard_streamlit.py
```

## 6. SCD Tipo 2

Se a população do município variasse no tempo, `dim_localidade` teria colunas
históricas:

```text
data_inicio
data_fim
flag_atual
populacao_municipio
```

Quando a população mudasse, a linha antiga seria encerrada e uma nova linha
seria criada. A fato apontaria para a versão vigente na data da notificação.

## 7. Qualidade dos dados

As validações estão em `sql/consultas_validacao.sql` e verificam:

- membro desconhecido nas dimensões;
- chaves estrangeiras nulas;
- registros órfãos;
- contagem da fato igual à staging.
