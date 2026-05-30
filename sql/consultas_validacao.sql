-- 1) FKs obrigatórias não podem ficar nulas.
SELECT 'fato_sem_tempo_notificacao' AS teste, COUNT(*) AS qtd
FROM fato_notificacao_covid
WHERE sk_data_notificacao IS NULL
UNION ALL
SELECT 'fato_sem_local', COUNT(*)
FROM fato_notificacao_covid
WHERE sk_local IS NULL
UNION ALL
SELECT 'fato_sem_perfil', COUNT(*)
FROM fato_notificacao_covid
WHERE sk_perfil IS NULL
UNION ALL
SELECT 'fato_sem_classificacao', COUNT(*)
FROM fato_notificacao_covid
WHERE sk_class IS NULL;

-- 2) A quantidade da fato deve bater com a staging.
SELECT
    (SELECT COUNT(*) FROM stg_notificacao_raw) AS origem,
    (SELECT COUNT(*) FROM fato_notificacao_covid) AS carregado;

-- 3) Cardinalidade das dimensões.
SELECT 'dim_tempo' AS dimensao, COUNT(*) AS linhas FROM dim_tempo
UNION ALL SELECT 'dim_localidade', COUNT(*) FROM dim_localidade
UNION ALL SELECT 'dim_perfil_paciente', COUNT(*) FROM dim_perfil_paciente
UNION ALL SELECT 'dim_classificacao', COUNT(*) FROM dim_classificacao
UNION ALL SELECT 'dim_sintomas', COUNT(*) FROM dim_sintomas
UNION ALL SELECT 'dim_comorbidade', COUNT(*) FROM dim_comorbidade
UNION ALL SELECT 'dim_teste', COUNT(*) FROM dim_teste;

-- 4) Teste de órfãos: precisa retornar zero em todas as linhas.
SELECT 'tempo_notificacao_orfao' AS teste, COUNT(*) AS qtd
FROM fato_notificacao_covid f
LEFT JOIN dim_tempo d ON d.sk_tempo = f.sk_data_notificacao
WHERE d.sk_tempo IS NULL
UNION ALL
SELECT 'local_orfao', COUNT(*)
FROM fato_notificacao_covid f
LEFT JOIN dim_localidade d ON d.sk_local = f.sk_local
WHERE d.sk_local IS NULL
UNION ALL
SELECT 'perfil_orfao', COUNT(*)
FROM fato_notificacao_covid f
LEFT JOIN dim_perfil_paciente d ON d.sk_perfil = f.sk_perfil
WHERE d.sk_perfil IS NULL
UNION ALL
SELECT 'classificacao_orfa', COUNT(*)
FROM fato_notificacao_covid f
LEFT JOIN dim_classificacao d ON d.sk_class = f.sk_class
WHERE d.sk_class IS NULL;
