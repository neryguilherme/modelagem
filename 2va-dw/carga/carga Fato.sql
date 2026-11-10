USE `dw_despesas`;

-- Limpa a tabela fato
TRUNCATE TABLE `dw_despesas`.`fatodespesa`;

-- Carga direta com resolução de chaves e agregação
INSERT INTO `dw_despesas`.`fatodespesa` (
    `dataKey`,
    `localKey`,
    `unidadeGestoraKey`,
    `credorKey`,
    `classificacaoKey`,
    `licitacaoKey`,
    `valorEmpenhado`,
    `valorLiquidado`,
    `valorPago`,
    `saldoAPagar`
)
SELECT 
    COALESCE(dt.keyData, 0) AS dataKey,
    COALESCE(loc.key, 0) AS localKey,
    COALESCE(ug_dim.key, 0) AS unidadeGestoraKey,
    COALESCE(c.key, 0) AS credorKey,
    COALESCE(cla.key, 0) AS classificacaoKey,
    COALESCE(lic.key, 0) AS licitacaoKey,
    SUM(COALESCE(d.valor_empenhado, 0.00)) AS valorEmpenhado,
    SUM(COALESCE(d.valor_liquidado, 0.00)) AS valorLiquidado,
    SUM(COALESCE(d.valor_pago, 0.00)) AS valorPago,
    SUM(COALESCE(d.valor_empenhado - d.valor_pago, 0.00)) AS saldoAPagar
FROM modelagem.despesa d
LEFT JOIN modelagem.unidade_gestora ug_origem 
    ON d.codigo_unidade_gestora = ug_origem.codigo_unidade_gestora
LEFT JOIN dw_despesas.dimdata dt 
    ON dt.data_id = CAST(d.data_empenho AS DATETIME)
LEFT JOIN dw_despesas.dimlocal loc 
    ON loc.id_municipio = ug_origem.id_municipio
LEFT JOIN dw_despesas.dimunidadegestora ug_dim 
    ON ug_dim.codigo_unidade_gestora = d.codigo_unidade_gestora
LEFT JOIN dw_despesas.dimcredor c 
    ON c.cpf_cnpj = d.cpf_cnpj
LEFT JOIN dw_despesas.dimlicitacao lic 
    ON lic.id_licitacao = d.id_licitacao
LEFT JOIN dw_despesas.dimclassificacaoorcamentaria cla 
    ON cla.codigo_funcao = d.codigo_funcao
    AND cla.codigo_programa = d.codigo_programa
    AND cla.codigo_acao = d.codigo_acao
    AND cla.codigo_categoria_economica = d.codigo_categoria_economica
    AND cla.codigo_natureza = d.codigo_natureza
    AND cla.codigo_modalidade_aplicacao = d.codigo_modalidade_aplicacao
    AND cla.codigo_elemento_despesa = d.codigo_elemento_despesa
    AND cla.codigo_fonte_recurso = d.codigo_fonte_recurso
GROUP BY 
    COALESCE(dt.keyData, 0),
    COALESCE(loc.key, 0),
    COALESCE(ug_dim.key, 0),
    COALESCE(c.key, 0),
    COALESCE(cla.key, 0),
    COALESCE(lic.key, 0);