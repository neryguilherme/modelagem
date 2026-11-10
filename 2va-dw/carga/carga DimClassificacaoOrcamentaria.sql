USE `dw_despesas`;

-- 1. Limpa a tabela
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE `dw_despesas`.`dimclassificacaoorcamentaria`;
SET FOREIGN_KEY_CHECKS = 1;

-- 2. Insere a Chave Zero exigida
-- 2. Insere a Chave Zero exigida
SET SESSION SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
INSERT INTO `dw_despesas`.`dimclassificacaoorcamentaria` (
    `key`, `codigo_funcao`, `nome_funcao`, `codigo_programa`, `nome_programa`,
    `codigo_acao`, `nome_acao`, `codigo_categoria_economica`, `nome_categoria_economica`,
    `codigo_natureza`, `nome_natureza_despesa`, `codigo_modalidade_aplicacao`, `nome_modalidade_aplicacao`,
    `codigo_elemento_despesa`, `nome_elemento_despesa`, `codigo_fonte_recurso`, `nome_fonte_recurso`,
    `date_from`, `date_to`, `version`
) VALUES (
    0, 0, 'Não Informado', 0, 'Não Informado',
    '0', 'Não Informado', 0, 'Não Informado',
    0, 'Não Informado', 0, 'Não Informado',
    0, 'Não Informado', 0, 'Não Informado',
    '1970-01-01 00:00:01', '2038-01-01 00:00:00', 1
);

-- 3. Insere as combinações orçamentárias únicas utilizadas nas despesas
INSERT INTO `dw_despesas`.`dimclassificacaoorcamentaria` (
    `codigo_funcao`, `nome_funcao`, `codigo_programa`, `nome_programa`,
    `codigo_acao`, `nome_acao`, `codigo_categoria_economica`, `nome_categoria_economica`,
    `codigo_natureza`, `nome_natureza_despesa`, `codigo_modalidade_aplicacao`, `nome_modalidade_aplicacao`,
    `codigo_elemento_despesa`, `nome_elemento_despesa`, `codigo_fonte_recurso`, `nome_fonte_recurso`,
    `date_from`, `date_to`, `version`
)
SELECT DISTINCT
    f.codigo_funcao, f.nome_funcao,
    p.codigo_programa, p.nome_programa,
    a.codigo_acao, a.nome_acao,
    ce.codigo_categoria_economica, ce.nome_categoria_economica,
    nd.codigo_natureza, nd.nome_natureza_despesa,
    ma.codigo_modalidade_aplicacao, ma.nome_modalidade_aplicacao,
    ed.codigo_elemento_despesa, ed.nome_elemento_despesa,
    fr.codigo_fonte_recurso, fr.nome_fonte_recurso,
    '1970-01-01 00:00:01', 
    '2038-01-01 00:00:00', 
    1
FROM `modelagem`.`despesa` d
INNER JOIN `modelagem`.`funcao` f ON d.codigo_funcao = f.codigo_funcao
INNER JOIN `modelagem`.`programa` p ON d.codigo_programa = p.codigo_programa
INNER JOIN `modelagem`.`acao` a ON d.codigo_acao = a.codigo_acao
INNER JOIN `modelagem`.`categoria_economica` ce ON d.codigo_categoria_economica = ce.codigo_categoria_economica
INNER JOIN `modelagem`.`natureza_despesa` nd ON d.codigo_natureza = nd.codigo_natureza
INNER JOIN `modelagem`.`modalidade_aplicacao` ma ON d.codigo_modalidade_aplicacao = ma.codigo_modalidade_aplicacao
INNER JOIN `modelagem`.`elemento_despesa` ed ON d.codigo_elemento_despesa = ed.codigo_elemento_despesa
INNER JOIN `modelagem`.`fonte_recurso` fr ON d.codigo_fonte_recurso = fr.codigo_fonte_recurso;