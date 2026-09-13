USE `modelagem`;

-- 1. Total consolidado da fato (esperado: exatamente 1.068.148 registros no 1º semestre)
SELECT COUNT(*) AS total_fato FROM fato_empenhos;

-- 2. Auditoria de integridade (deve retornar 0 para todas as colunas de chave e datas críticas)
SELECT 
    COUNT(*) - COUNT(id_fato) AS nulos_pk,
    COUNT(*) - COUNT(data_empenho) AS nulos_data,
    COUNT(*) - COUNT(codigo_unidade_gestora) AS nulos_ug,
    COUNT(*) - COUNT(co) AS nulos_co
FROM fato_empenhos;

-- 3. Consulta analítica de teste relacionando a Fato e as Dimensões
SELECT 
    f.numero_empenho,
    f.data_empenho,
    ug.descricao_unidade_gestora,
    ug.municipio,
    c.nome_credor,
    f.valor_empenhado,
    f.valor_pago
FROM fato_empenhos f
JOIN dim_unidade_gestora ug ON f.codigo_unidade_gestora = ug.codigo_unidade_gestora
JOIN dim_credor c ON f.cpf_cnpj = c.cpf_cnpj
ORDER BY f.data_empenho DESC
LIMIT 10;
