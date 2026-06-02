# Data Warehouse COVID-19 ES

Montando um Data Warehouse em modelo estrela com os microdados de COVID-19 do Espírito Santo.

A implementação usa Python + SQLite para carregar o `MICRODADOS.csv`, popular
as dimensões, carregar a tabela fato, gerar um data mart agregado e exibir um
dashboard em Streamlit.

## Como executar

Para criar o banco SQLite:

```bash
python scripts/etl_sqlite_dw_covid.py --csv MICRODADOS.csv --reset
```

O comando gera:

```text
dw_covid.sqlite
```
Para gerar o relatório de nulos:

```bash
python scripts/relatorio_nulos.py --csv MICRODADOS.csv
```

Para abrir o dashboard:

```bash
streamlit run dashboard_streamlit.py
```

## Arquivos

```text
scripts/etl_sqlite_dw_covid.py   ETL em Python
scripts/relatorio_nulos.py       Relatório de nulos do CSV
dashboard_streamlit.py           Dashboard Streamlit
sql/schema_sqlite.sql            Tabelas do DW
sql/consultas_validacao.sql      Validações
sql/consultas_analiticas.sql     Consultas analíticas
docs/respostas_exercicios.md     Respostas dos exercícios
docs/relatorio_nulos.csv         Percentual de nulos por coluna
```

## Modelo

Grão da fato: uma notificação de COVID-19 por linha.

Dimensões:

- `dim_tempo`
- `dim_localidade`
- `dim_perfil_paciente`
- `dim_classificacao`
- `dim_sintomas`
- `dim_comorbidade`
- `dim_teste`

Fato:

- `fato_notificacao_covid`

Medidas principais:

- `qtd_notificacao`
- `flag_confirmado`
- `flag_obito_covid`
- `flag_internado`
- `flag_cura`
- `idade_anos`
- `dias_notif_encerramento`
- `dias_notif_obito`

## Validação

O ETL compara a quantidade de linhas da staging com a fato ao final da carga.
Para rodar as validações manualmente:

```bash
sqlite3 dw_covid.sqlite ".read sql/consultas_validacao.sql"
```

O data mart gerado é a tabela:

```text
mart_covid_municipio_mes
```
