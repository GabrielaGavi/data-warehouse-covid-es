PRAGMA foreign_keys = OFF;

DROP VIEW IF EXISTS vw_confirmados_municipio_mes;
DROP VIEW IF EXISTS vw_letalidade_faixa_etaria;
DROP TABLE IF EXISTS mart_covid_municipio_mes;
DROP TABLE IF EXISTS fato_notificacao_covid;
DROP TABLE IF EXISTS dim_teste;
DROP TABLE IF EXISTS dim_comorbidade;
DROP TABLE IF EXISTS dim_sintomas;
DROP TABLE IF EXISTS dim_classificacao;
DROP TABLE IF EXISTS dim_perfil_paciente;
DROP TABLE IF EXISTS dim_localidade;
DROP TABLE IF EXISTS dim_tempo;
DROP TABLE IF EXISTS stg_notificacao_raw;

PRAGMA foreign_keys = ON;

CREATE TABLE stg_notificacao_raw (
    id_stg INTEGER PRIMARY KEY AUTOINCREMENT,
    data_notificacao TEXT,
    data_cadastro TEXT,
    data_diagnostico TEXT,
    data_coleta_rt_pcr TEXT,
    data_coleta_teste_rap TEXT,
    data_coleta_sorologia TEXT,
    data_coleta_sorolog_igg TEXT,
    data_encerramento TEXT,
    data_obito TEXT,
    classificacao TEXT,
    evolucao TEXT,
    criterio_confirmacao TEXT,
    status_notificacao TEXT,
    municipio TEXT,
    bairro TEXT,
    faixa_etaria TEXT,
    idade_na_notificacao TEXT,
    sexo TEXT,
    raca_cor TEXT,
    escolaridade TEXT,
    gestante TEXT,
    febre TEXT,
    dif_respiratoria TEXT,
    tosse TEXT,
    coriza TEXT,
    dor_garganta TEXT,
    diarreia TEXT,
    cefaleia TEXT,
    com_pulmao TEXT,
    com_cardio TEXT,
    com_renal TEXT,
    com_diabetes TEXT,
    com_tabagismo TEXT,
    com_obesidade TEXT,
    ficou_internado TEXT,
    viagem_brasil TEXT,
    viagem_internacional TEXT,
    profissional_saude TEXT,
    possui_deficiencia TEXT,
    morador_rua TEXT,
    resultado_rt_pcr TEXT,
    resultado_teste_rap TEXT,
    resultado_sorologia TEXT,
    resultado_sorol_igg TEXT,
    tipo_teste_rapido TEXT
);

CREATE TABLE dim_tempo (
    sk_tempo INTEGER PRIMARY KEY,
    data TEXT UNIQUE,
    dia INTEGER,
    mes INTEGER,
    ano INTEGER,
    trimestre INTEGER,
    nome_mes TEXT NOT NULL,
    dia_semana TEXT NOT NULL,
    ano_mes TEXT NOT NULL,
    eh_fim_de_semana INTEGER NOT NULL CHECK (eh_fim_de_semana IN (0, 1)),
    semana_epidemiologica INTEGER
);

INSERT INTO dim_tempo (
    sk_tempo, data, dia, mes, ano, trimestre, nome_mes, dia_semana,
    ano_mes, eh_fim_de_semana, semana_epidemiologica
) VALUES (
    -1, NULL, NULL, NULL, NULL, NULL, 'Desconhecido', 'Desconhecido',
    'N/D', 0, NULL
);

CREATE TABLE dim_localidade (
    sk_local INTEGER PRIMARY KEY AUTOINCREMENT,
    municipio TEXT NOT NULL,
    bairro TEXT NOT NULL,
    uf TEXT NOT NULL DEFAULT 'ES',
    regiao_es TEXT NOT NULL,
    macrorregiao TEXT NOT NULL,
    UNIQUE (municipio, bairro)
);

INSERT INTO dim_localidade (
    sk_local, municipio, bairro, uf, regiao_es, macrorregiao
) VALUES (
    -1, 'Desconhecido', 'Desconhecido', 'ES', 'Desconhecida', 'Desconhecida'
);

CREATE TABLE dim_perfil_paciente (
    sk_perfil INTEGER PRIMARY KEY AUTOINCREMENT,
    sexo TEXT NOT NULL,
    faixa_etaria TEXT NOT NULL,
    raca_cor TEXT NOT NULL,
    escolaridade TEXT NOT NULL,
    gestante TEXT NOT NULL,
    profissional_saude TEXT NOT NULL,
    morador_rua TEXT NOT NULL,
    possui_deficiencia TEXT NOT NULL,
    UNIQUE (
        sexo, faixa_etaria, raca_cor, escolaridade, gestante,
        profissional_saude, morador_rua, possui_deficiencia
    )
);

INSERT INTO dim_perfil_paciente (
    sk_perfil, sexo, faixa_etaria, raca_cor, escolaridade,
    gestante, profissional_saude, morador_rua, possui_deficiencia
) VALUES (
    -1, 'Desconhecido', 'Desconhecida', 'Desconhecida', 'Desconhecida',
    'Desconhecido', 'Desconhecido', 'Desconhecido', 'Desconhecido'
);

CREATE TABLE dim_classificacao (
    sk_class INTEGER PRIMARY KEY AUTOINCREMENT,
    classificacao TEXT NOT NULL,
    evolucao TEXT NOT NULL,
    criterio_confirmacao TEXT NOT NULL,
    status_notificacao TEXT NOT NULL,
    UNIQUE (classificacao, evolucao, criterio_confirmacao, status_notificacao)
);

INSERT INTO dim_classificacao (
    sk_class, classificacao, evolucao, criterio_confirmacao, status_notificacao
) VALUES (
    -1, 'Desconhecida', 'Desconhecida', 'Desconhecido', 'Desconhecido'
);

CREATE TABLE dim_sintomas (
    sk_sint INTEGER PRIMARY KEY AUTOINCREMENT,
    febre TEXT NOT NULL,
    dif_respiratoria TEXT NOT NULL,
    tosse TEXT NOT NULL,
    coriza TEXT NOT NULL,
    dor_garganta TEXT NOT NULL,
    diarreia TEXT NOT NULL,
    cefaleia TEXT NOT NULL,
    UNIQUE (febre, dif_respiratoria, tosse, coriza, dor_garganta, diarreia, cefaleia)
);

INSERT INTO dim_sintomas (
    sk_sint, febre, dif_respiratoria, tosse, coriza, dor_garganta, diarreia, cefaleia
) VALUES (
    -1, 'Desconhecido', 'Desconhecido', 'Desconhecido', 'Desconhecido',
    'Desconhecido', 'Desconhecido', 'Desconhecido'
);

CREATE TABLE dim_comorbidade (
    sk_como INTEGER PRIMARY KEY AUTOINCREMENT,
    com_pulmao TEXT NOT NULL,
    com_cardio TEXT NOT NULL,
    com_renal TEXT NOT NULL,
    com_diabetes TEXT NOT NULL,
    com_tabagismo TEXT NOT NULL,
    com_obesidade TEXT NOT NULL,
    UNIQUE (com_pulmao, com_cardio, com_renal, com_diabetes, com_tabagismo, com_obesidade)
);

INSERT INTO dim_comorbidade (
    sk_como, com_pulmao, com_cardio, com_renal, com_diabetes, com_tabagismo, com_obesidade
) VALUES (
    -1, 'Desconhecido', 'Desconhecido', 'Desconhecido',
    'Desconhecido', 'Desconhecido', 'Desconhecido'
);

CREATE TABLE dim_teste (
    sk_teste INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_teste_rapido TEXT NOT NULL,
    resultado_rt_pcr TEXT NOT NULL,
    resultado_teste_rap TEXT NOT NULL,
    resultado_sorologia TEXT NOT NULL,
    resultado_sorol_igg TEXT NOT NULL,
    UNIQUE (
        tipo_teste_rapido, resultado_rt_pcr, resultado_teste_rap,
        resultado_sorologia, resultado_sorol_igg
    )
);

INSERT INTO dim_teste (
    sk_teste, tipo_teste_rapido, resultado_rt_pcr, resultado_teste_rap,
    resultado_sorologia, resultado_sorol_igg
) VALUES (
    -1, 'Desconhecido', 'Desconhecido', 'Desconhecido',
    'Desconhecido', 'Desconhecido'
);

CREATE TABLE fato_notificacao_covid (
    id_fato INTEGER PRIMARY KEY AUTOINCREMENT,
    sk_data_notificacao INTEGER NOT NULL,
    sk_data_cadastro INTEGER NOT NULL,
    sk_data_diagnostico INTEGER NOT NULL,
    sk_data_coleta INTEGER NOT NULL,
    sk_data_encerramento INTEGER NOT NULL,
    sk_data_obito INTEGER NOT NULL,
    sk_local INTEGER NOT NULL,
    sk_perfil INTEGER NOT NULL,
    sk_class INTEGER NOT NULL,
    sk_sint INTEGER NOT NULL,
    sk_como INTEGER NOT NULL,
    sk_teste INTEGER NOT NULL,
    qtd_notificacao INTEGER NOT NULL DEFAULT 1 CHECK (qtd_notificacao = 1),
    flag_confirmado INTEGER NOT NULL CHECK (flag_confirmado IN (0, 1)),
    flag_obito_covid INTEGER NOT NULL CHECK (flag_obito_covid IN (0, 1)),
    flag_internado INTEGER NOT NULL CHECK (flag_internado IN (0, 1)),
    flag_cura INTEGER NOT NULL CHECK (flag_cura IN (0, 1)),
    idade_anos INTEGER,
    dias_notif_encerramento INTEGER,
    dias_notif_obito INTEGER,
    FOREIGN KEY (sk_data_notificacao) REFERENCES dim_tempo (sk_tempo),
    FOREIGN KEY (sk_data_cadastro) REFERENCES dim_tempo (sk_tempo),
    FOREIGN KEY (sk_data_diagnostico) REFERENCES dim_tempo (sk_tempo),
    FOREIGN KEY (sk_data_coleta) REFERENCES dim_tempo (sk_tempo),
    FOREIGN KEY (sk_data_encerramento) REFERENCES dim_tempo (sk_tempo),
    FOREIGN KEY (sk_data_obito) REFERENCES dim_tempo (sk_tempo),
    FOREIGN KEY (sk_local) REFERENCES dim_localidade (sk_local),
    FOREIGN KEY (sk_perfil) REFERENCES dim_perfil_paciente (sk_perfil),
    FOREIGN KEY (sk_class) REFERENCES dim_classificacao (sk_class),
    FOREIGN KEY (sk_sint) REFERENCES dim_sintomas (sk_sint),
    FOREIGN KEY (sk_como) REFERENCES dim_comorbidade (sk_como),
    FOREIGN KEY (sk_teste) REFERENCES dim_teste (sk_teste)
);

CREATE INDEX idx_fato_data_notificacao ON fato_notificacao_covid (sk_data_notificacao);
CREATE INDEX idx_fato_local ON fato_notificacao_covid (sk_local);
CREATE INDEX idx_fato_class ON fato_notificacao_covid (sk_class);
CREATE INDEX idx_fato_perfil ON fato_notificacao_covid (sk_perfil);
CREATE INDEX idx_fato_sintomas ON fato_notificacao_covid (sk_sint);
CREATE INDEX idx_fato_comorbidade ON fato_notificacao_covid (sk_como);

CREATE VIEW vw_confirmados_municipio_mes AS
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

CREATE VIEW vw_letalidade_faixa_etaria AS
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
GROUP BY p.faixa_etaria;
