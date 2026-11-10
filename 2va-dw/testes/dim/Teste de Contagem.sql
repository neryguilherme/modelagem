SELECT '1. Credor' AS Dimensao,
       (SELECT COUNT(*) FROM modelagem.credor) AS Total_Origem_Relacional,
       (SELECT COUNT(*) FROM dw_despesas.dimcredor) AS Total_Destino_DW
UNION ALL
SELECT '2. Local (Município)',
       (SELECT COUNT(*) FROM modelagem.municipio),
       (SELECT COUNT(*) FROM dw_despesas.dimlocal)
UNION ALL
SELECT '3. Unidade Gestora',
       (SELECT COUNT(*) FROM modelagem.unidade_gestora),
       (SELECT COUNT(*) FROM dw_despesas.dimunidadegestora)
UNION ALL
SELECT '4. Licitação',
       (SELECT COUNT(*) FROM modelagem.licitacao),
       (SELECT COUNT(*) FROM dw_despesas.dimlicitacao)
UNION ALL
SELECT '5. Classificação Orçamentária',
       (SELECT COUNT(*) + 1 FROM (
           SELECT DISTINCT codigo_funcao, codigo_programa, codigo_acao, 
                           codigo_categoria_economica, codigo_natureza, 
                           codigo_modalidade_aplicacao, codigo_elemento_despesa, 
                           codigo_fonte_recurso 
           FROM modelagem.despesa
       ) AS comb),
       (SELECT COUNT(*) FROM dw_despesas.dimclassificacaoorcamentaria);
       