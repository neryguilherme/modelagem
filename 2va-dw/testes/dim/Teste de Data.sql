SELECT 
    COUNT(*) AS total_dias_carregados,
    MIN(data_id) AS data_inicial,
    MAX(data_id) AS data_final
FROM dw_despesas.dimdata;