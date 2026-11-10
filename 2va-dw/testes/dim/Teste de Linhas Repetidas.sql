SELECT 'dimcredor' AS Tabela, COUNT(*) - COUNT(DISTINCT cpf_cnpj) AS Duplicatas FROM dw_despesas.dimcredor
UNION ALL
SELECT 'dimlocal', COUNT(*) - COUNT(DISTINCT id_municipio) FROM dw_despesas.dimlocal
UNION ALL
SELECT 'dimunidadegestora', COUNT(*) - COUNT(DISTINCT codigo_unidade_gestora) FROM dw_despesas.dimunidadegestora
UNION ALL
SELECT 'dimlicitacao', COUNT(*) - COUNT(DISTINCT id_licitacao) FROM dw_despesas.dimlicitacao
UNION ALL
SELECT 'dimclassificacao', COUNT(*) - COUNT(DISTINCT CONCAT_WS('-', codigo_funcao, codigo_programa, codigo_acao, codigo_categoria_economica, codigo_natureza, codigo_modalidade_aplicacao, codigo_elemento_despesa, codigo_fonte_recurso)) FROM dw_despesas.dimclassificacaoorcamentaria;