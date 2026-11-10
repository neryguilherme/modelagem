SELECT 'dimcredor' AS Tabela, COUNT(*) AS Linhas_Invalidas_Ou_Nulas
FROM dw_despesas.dimcredor 
WHERE cpf_cnpj IS NULL OR nome_credor IS NULL OR date_from IS NULL OR date_to IS NULL OR version IS NULL
UNION ALL
SELECT 'dimlocal', COUNT(*) 
FROM dw_despesas.dimlocal 
WHERE id_municipio IS NULL OR nome_municipio IS NULL OR date_from IS NULL OR date_to IS NULL OR version IS NULL
UNION ALL
SELECT 'dimunidadegestora', COUNT(*) 
FROM dw_despesas.dimunidadegestora 
WHERE codigo_unidade_gestora IS NULL OR nome_unidade_gestora IS NULL OR date_from IS NULL OR date_to IS NULL OR version IS NULL
UNION ALL
SELECT 'dimlicitacao', COUNT(*) 
FROM dw_despesas.dimlicitacao 
WHERE id_licitacao IS NULL OR numero_licitacao IS NULL OR modalidade_licitacao IS NULL OR date_from IS NULL OR date_to IS NULL OR version IS NULL
UNION ALL
SELECT 'dimclassificacaoorcamentaria', COUNT(*) 
FROM dw_despesas.dimclassificacaoorcamentaria 
WHERE date_from IS NULL OR date_to IS NULL OR version IS NULL;