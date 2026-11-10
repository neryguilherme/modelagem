SELECT 'dimcredor' AS Tabela, `key`, cpf_cnpj AS Chave_Natural, nome_credor AS Descricao, date_from, date_to, version 
FROM dw_despesas.dimcredor WHERE `key` = 0
UNION ALL
SELECT 'dimlocal', `key`, CAST(id_municipio AS CHAR), nome_municipio, date_from, date_to, version 
FROM dw_despesas.dimlocal WHERE `key` = 0
UNION ALL
SELECT 'dimunidadegestora', `key`, CAST(codigo_unidade_gestora AS CHAR), nome_unidade_gestora, date_from, date_to, version 
FROM dw_despesas.dimunidadegestora WHERE `key` = 0
UNION ALL
SELECT 'dimlicitacao', `key`, CAST(id_licitacao AS CHAR), modalidade_licitacao, date_from, date_to, version 
FROM dw_despesas.dimlicitacao WHERE `key` = 0
UNION ALL
SELECT 'dimclassificacaoorcamentaria', `key`, CAST(codigo_funcao AS CHAR), nome_funcao, date_from, date_to, version 
FROM dw_despesas.dimclassificacaoorcamentaria WHERE `key` = 0;