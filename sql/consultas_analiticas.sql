-- Q1: casos confirmados por município e mês.
SELECT
    l.municipio,
    t.ano_mes,
    SUM(f.flag_confirmado) AS confirmados,
    SUM(f.qtd_notificacao) AS notificacoes_total
FROM fato_notificacao_covid f
JOIN dim_localidade l ON l.sk_local = f.sk_local
JOIN dim_tempo t ON t.sk_tempo = f.sk_data_notificacao
WHERE t.ano IN (2021, 2022)
GROUP BY l.municipio, t.ano_mes
ORDER BY confirmados DESC
LIMIT 20;

-- Q2: letalidade por faixa etária.
SELECT
    p.faixa_etaria,
    SUM(f.flag_confirmado) AS confirmados,
    SUM(f.flag_obito_covid) AS obitos,
    ROUND(
        100.0 * SUM(f.flag_obito_covid) / NULLIF(SUM(f.flag_confirmado), 0),
        2
    ) AS letalidade_pct
FROM fato_notificacao_covid f
JOIN dim_perfil_paciente p ON p.sk_perfil = f.sk_perfil
GROUP BY p.faixa_etaria
ORDER BY letalidade_pct DESC;

-- Q3: sintomas mais associados à internação.
SELECT
    s.febre,
    s.tosse,
    s.dif_respiratoria,
    SUM(f.flag_internado) AS internacoes,
    SUM(f.qtd_notificacao) AS casos
FROM fato_notificacao_covid f
JOIN dim_sintomas s ON s.sk_sint = f.sk_sint
GROUP BY s.febre, s.tosse, s.dif_respiratoria
HAVING SUM(f.qtd_notificacao) > 1000
ORDER BY internacoes DESC
LIMIT 10;

-- Q4: tempo médio entre notificação e encerramento por município.
SELECT
    l.municipio,
    ROUND(AVG(f.dias_notif_encerramento), 1) AS dias_medio,
    COUNT(*) AS casos
FROM fato_notificacao_covid f
JOIN dim_localidade l ON l.sk_local = f.sk_local
WHERE f.dias_notif_encerramento IS NOT NULL
  AND f.dias_notif_encerramento BETWEEN 0 AND 180
GROUP BY l.municipio
HAVING COUNT(*) > 500
ORDER BY dias_medio DESC;

-- Q5: impacto de comorbidades na letalidade.
SELECT
    c.com_cardio,
    c.com_diabetes,
    c.com_obesidade,
    SUM(f.flag_confirmado) AS confirmados,
    SUM(f.flag_obito_covid) AS obitos,
    ROUND(
        100.0 * SUM(f.flag_obito_covid) / NULLIF(SUM(f.flag_confirmado), 0),
        2
    ) AS letalidade_pct
FROM fato_notificacao_covid f
JOIN dim_comorbidade c ON c.sk_como = f.sk_como
GROUP BY c.com_cardio, c.com_diabetes, c.com_obesidade
ORDER BY letalidade_pct DESC
LIMIT 15;

-- Data mart materializado no SQLite: tabela pré-agregada por município e mês.
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
