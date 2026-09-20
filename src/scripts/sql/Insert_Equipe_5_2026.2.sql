-- =============================================================================
-- SCRIPT DE CARGA E NORMALIZAÇÃO (DML): Equipe 5 (2026.2)
-- Modelo Relacional (OLTP / 3FN) - Execução Orçamentária
-- Base de Dados: Despesas TCE-PB 2025 (Filtro: 1º Semestre)
-- =============================================================================

SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;
SET SQL_MODE = '';
SET SQL_SAFE_UPDATES = 0;
SET autocommit = 0;

USE `modelagem`;

-- -----------------------------------------------------------------------------
-- 1. Criação da Tabela Temporária de Staging
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `temp_despesas`;

CREATE TABLE `temp_despesas` (
    `municipio` VARCHAR(255),
    `codigo_unidade_gestora` VARCHAR(50),
    `descricao_unidade_gestora` TEXT,
    `numero_empenho` VARCHAR(50),
    `data_empenho` VARCHAR(50),
    `mes` VARCHAR(50),
    `cpf_cnpj` VARCHAR(255),
    `nome_credor` TEXT,
    `valor_empenhado` VARCHAR(50),
    `valor_liquidado` VARCHAR(50),
    `valor_pago` VARCHAR(50),
    `codigo_unidade_orcamentaria` VARCHAR(50),
    `descricao_unidade_orcamentaria` TEXT,
    `codigo_funcao` VARCHAR(50),
    `funcao` TEXT,
    `codigo_subfuncao` VARCHAR(50),
    `subfuncao` TEXT,
    `codigo_programa` VARCHAR(50),
    `programa` TEXT,
    `codigo_acao` VARCHAR(50),
    `acao` TEXT,
    `codigo_categoria_economica` VARCHAR(50),
    `categoria_economica` TEXT,
    `codigo_natureza` VARCHAR(50),
    `grupo_natureza_despesa` TEXT,
    `codigo_modalidade_aplicacao` VARCHAR(50),
    `modalidade_aplicacao` TEXT,
    `codigo_elemento_despesa` VARCHAR(50),
    `elemento_despesa` TEXT,
    `codigo_subelemento` VARCHAR(50),
    `codigo_subelemento_exibicao` TEXT,
    `numero_licitacao` VARCHAR(50),
    `modalidade_licitacao` TEXT,
    `numero_obra` VARCHAR(50),
    `historico` TEXT,
    `codigo_fonte_recurso` VARCHAR(50),
    `descricao_fonte_recurso` TEXT,
    `ano_fonte` VARCHAR(50),
    `co` VARCHAR(50),
    `descricao_co` TEXT
);

-- -----------------------------------------------------------------------------
-- 2. Carga do Arquivo CSV Bruto
-- -----------------------------------------------------------------------------
-- SHOW VARIABLES LIKE 'secure_file_priv';

LOAD DATA INFILE '/var/lib/mysql-files/despesas-2025.csv'

INTO TABLE `temp_despesas`
FIELDS TERMINATED BY ';'
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

COMMIT;

-- -----------------------------------------------------------------------------
-- 3. Filtro: 1º Semestre (Janeiro a Junho)
-- -----------------------------------------------------------------------------
DELETE FROM `temp_despesas`
WHERE CAST(LEFT(`mes`, 2) AS SIGNED) > 6
   OR `data_empenho` IS NULL 
   OR `data_empenho` = '';

COMMIT;

-- -----------------------------------------------------------------------------
-- 4. Normalização: Localidade e Unidades Gestoras
-- -----------------------------------------------------------------------------

-- 4.1. Tabela: municipio (sem UF, registro sentinela 1)
INSERT INTO `municipio` (`id_municipio`, `nome_municipio`)
VALUES (1, 'Não Informado');

INSERT INTO `municipio` (`nome_municipio`)
SELECT DISTINCT 
    TRIM(`municipio`)
FROM `temp_despesas`
WHERE `municipio` IS NOT NULL 
  AND TRIM(`municipio`) != ''
ORDER BY TRIM(`municipio`);

-- 4.2. Tabela: unidade_gestora
INSERT INTO `unidade_gestora` (`codigo_unidade_gestora`, `nome_unidade_gestora`, `id_municipio`)
VALUES (0, 'Não Informado', 1);

INSERT IGNORE INTO `unidade_gestora` (`codigo_unidade_gestora`, `nome_unidade_gestora`, `id_municipio`)
SELECT 
    CAST(t.`codigo_unidade_gestora` AS SIGNED),
    COALESCE(NULLIF(TRIM(t.`descricao_unidade_gestora`), ''), 'Não Informado'),
    COALESCE(m.`id_municipio`, 1)
FROM (
    SELECT DISTINCT 
        `codigo_unidade_gestora`, 
        `descricao_unidade_gestora`, 
        `municipio`
    FROM `temp_despesas`
    WHERE `codigo_unidade_gestora` IS NOT NULL 
      AND TRIM(`codigo_unidade_gestora`) != ''
      AND CAST(`codigo_unidade_gestora` AS SIGNED) > 0
) t
LEFT JOIN `municipio` m 
  ON TRIM(t.`municipio`) = m.`nome_municipio`;

-- -----------------------------------------------------------------------------
-- 5. Normalização: Credores e Licitações
-- -----------------------------------------------------------------------------

-- 5.1. Tabela: credor (VARCHAR mantendo zeros à esquerda)
INSERT IGNORE INTO `credor` (`cpf_cnpj`, `nome_credor`) 
VALUES ('0', 'Não Informado');

INSERT IGNORE INTO `credor` (`cpf_cnpj`, `nome_credor`)
SELECT DISTINCT 
    TRIM(`cpf_cnpj`), 
    COALESCE(NULLIF(TRIM(`nome_credor`), ''), 'Não Informado')
FROM `temp_despesas`
WHERE `cpf_cnpj` IS NOT NULL 
  AND TRIM(`cpf_cnpj`) != ''
  AND TRIM(`cpf_cnpj`) != '0';

-- 5.2. Tabela: licitacao (registro sentinela 1 para compras diretas)
INSERT INTO `licitacao` (`id_licitacao`, `numero_licitacao`, `modalidade_licitacao`, `numero_obra`)
VALUES (1, 'Sem Licitação', 'Sem Licitação', '0');

INSERT IGNORE INTO `licitacao` (`numero_licitacao`, `modalidade_licitacao`, `numero_obra`)
SELECT DISTINCT 
    COALESCE(NULLIF(TRIM(`numero_licitacao`), ''), 'Sem Licitação'),
    COALESCE(NULLIF(TRIM(`modalidade_licitacao`), ''), 'Sem Licitação'),
    COALESCE(NULLIF(TRIM(`numero_obra`), ''), '0')
FROM `temp_despesas`
WHERE TRIM(`numero_licitacao`) NOT IN ('000000000', '', '0', 'Sem Licitação')
   OR TRIM(`modalidade_licitacao`) NOT IN ('Sem Licitação', '', '0');

-- -----------------------------------------------------------------------------
-- 6. Normalização: Classificadores Orçamentários (Higienizados)
-- -----------------------------------------------------------------------------

-- 6.1. Funcao
INSERT IGNORE INTO `funcao` (`codigo_funcao`, `nome_funcao`) VALUES (0, 'Não Informado');
INSERT IGNORE INTO `funcao` (`codigo_funcao`, `nome_funcao`)
SELECT DISTINCT CAST(`codigo_funcao` AS SIGNED), `funcao`
FROM `temp_despesas`
WHERE CAST(`codigo_funcao` AS SIGNED) > 0;

-- 6.2. Programa
INSERT IGNORE INTO `programa` (`codigo_programa`, `nome_programa`) VALUES (0, 'Não Informado');
INSERT IGNORE INTO `programa` (`codigo_programa`, `nome_programa`)
SELECT DISTINCT CAST(`codigo_programa` AS SIGNED), `programa`
FROM `temp_despesas`
WHERE CAST(`codigo_programa` AS SIGNED) > 0;

-- 6.3. Acao
INSERT IGNORE INTO `acao` (`codigo_acao`, `nome_acao`) VALUES ('0', 'Não Informado');
INSERT IGNORE INTO `acao` (`codigo_acao`, `nome_acao`)
SELECT DISTINCT TRIM(`codigo_acao`), `acao`
FROM `temp_despesas`
WHERE TRIM(`codigo_acao`) NOT IN ('', '0') AND `codigo_acao` IS NOT NULL;

-- 6.4. Categoria Economica
INSERT IGNORE INTO `categoria_economica` (`codigo_categoria_economica`, `nome_categoria_economica`) VALUES (0, 'Não Informado');
INSERT IGNORE INTO `categoria_economica` (`codigo_categoria_economica`, `nome_categoria_economica`)
SELECT DISTINCT CAST(`codigo_categoria_economica` AS SIGNED), `categoria_economica`
FROM `temp_despesas`
WHERE CAST(`codigo_categoria_economica` AS SIGNED) > 0;

-- 6.5. Natureza Despesa
INSERT IGNORE INTO `natureza_despesa` (`codigo_natureza`, `nome_natureza_despesa`) VALUES (0, 'Não Informado');
INSERT IGNORE INTO `natureza_despesa` (`codigo_natureza`, `nome_natureza_despesa`)
SELECT DISTINCT CAST(`codigo_natureza` AS SIGNED), `grupo_natureza_despesa`
FROM `temp_despesas`
WHERE CAST(`codigo_natureza` AS SIGNED) > 0;

-- 6.6. Modalidade Aplicacao
INSERT IGNORE INTO `modalidade_aplicacao` (`codigo_modalidade_aplicacao`, `nome_modalidade_aplicacao`) VALUES (0, 'Não Informado');
INSERT IGNORE INTO `modalidade_aplicacao` (`codigo_modalidade_aplicacao`, `nome_modalidade_aplicacao`)
SELECT DISTINCT CAST(`codigo_modalidade_aplicacao` AS SIGNED), `modalidade_aplicacao`
FROM `temp_despesas`
WHERE CAST(`codigo_modalidade_aplicacao` AS SIGNED) > 0;

-- 6.7. Elemento Despesa
INSERT IGNORE INTO `elemento_despesa` (`codigo_elemento_despesa`, `nome_elemento_despesa`) VALUES (0, 'Não Informado');
INSERT IGNORE INTO `elemento_despesa` (`codigo_elemento_despesa`, `nome_elemento_despesa`)
SELECT DISTINCT CAST(`codigo_elemento_despesa` AS SIGNED), `elemento_despesa`
FROM `temp_despesas`
WHERE CAST(`codigo_elemento_despesa` AS SIGNED) > 0;

-- 6.8. Fonte Recurso
INSERT IGNORE INTO `fonte_recurso` (`codigo_fonte_recurso`, `nome_fonte_recurso`) VALUES (0, 'Não Informado');
INSERT IGNORE INTO `fonte_recurso` (`codigo_fonte_recurso`, `nome_fonte_recurso`)
SELECT DISTINCT CAST(`codigo_fonte_recurso` AS SIGNED), `descricao_fonte_recurso`
FROM `temp_despesas`
WHERE CAST(`codigo_fonte_recurso` AS SIGNED) > 0;

COMMIT;

-- -----------------------------------------------------------------------------
-- 7. Carga da Tabela Central: despesa
-- -----------------------------------------------------------------------------
TRUNCATE TABLE `despesa`;

INSERT INTO `despesa` (
    `numero_empenho`,
    `data_empenho`,
    `mes`,
    `valor_empenhado`,
    `valor_liquidado`,
    `valor_pago`,
    `historico`,
    `codigo_unidade_gestora`,
    `cpf_cnpj`,
    `id_licitacao`,
    `codigo_funcao`,
    `codigo_programa`,
    `codigo_acao`,
    `codigo_categoria_economica`,
    `codigo_natureza`,
    `codigo_modalidade_aplicacao`,
    `codigo_elemento_despesa`,
    `codigo_fonte_recurso`
)
SELECT 
    COALESCE(CAST(NULLIF(t.`numero_empenho`, '') AS SIGNED), 0),
    COALESCE(
        STR_TO_DATE(LEFT(t.`data_empenho`, 10), '%Y-%m-%d'),
        STR_TO_DATE(LEFT(t.`data_empenho`, 10), '%d/%m/%Y'),
        '2025-01-01'
    ),
    t.`mes`,
    COALESCE(CAST(REPLACE(REPLACE(NULLIF(t.`valor_empenhado`, ''), '.', ''), ',', '.') AS DECIMAL(15,2)), 0.00),
    COALESCE(CAST(REPLACE(REPLACE(NULLIF(t.`valor_liquidado`, ''), '.', ''), ',', '.') AS DECIMAL(15,2)), 0.00),
    COALESCE(CAST(REPLACE(REPLACE(NULLIF(t.`valor_pago`, ''), '.', ''), ',', '.') AS DECIMAL(15,2)), 0.00),
    COALESCE(t.`historico`, ''),
    COALESCE(CAST(NULLIF(t.`codigo_unidade_gestora`, '') AS SIGNED), 0),
    COALESCE(NULLIF(TRIM(t.`cpf_cnpj`), ''), '0'),
    COALESCE(l.`id_licitacao`, 1),
    COALESCE(CAST(NULLIF(t.`codigo_funcao`, '') AS SIGNED), 0),
    COALESCE(CAST(NULLIF(t.`codigo_programa`, '') AS SIGNED), 0),
    COALESCE(NULLIF(TRIM(t.`codigo_acao`), ''), '0'),
    COALESCE(CAST(NULLIF(t.`codigo_categoria_economica`, '') AS SIGNED), 0),
    COALESCE(CAST(NULLIF(t.`codigo_natureza`, '') AS SIGNED), 0),
    COALESCE(CAST(NULLIF(t.`codigo_modalidade_aplicacao`, '') AS SIGNED), 0),
    COALESCE(CAST(NULLIF(t.`codigo_elemento_despesa`, '') AS SIGNED), 0),
    COALESCE(CAST(NULLIF(t.`codigo_fonte_recurso`, '') AS SIGNED), 0)
FROM `temp_despesas` t
LEFT JOIN `licitacao` l
    ON TRIM(t.`numero_licitacao`) = l.`numero_licitacao`
   AND TRIM(t.`modalidade_licitacao`) = l.`modalidade_licitacao`
   AND TRIM(t.`numero_obra`) = l.`numero_obra`;

COMMIT;

-- -----------------------------------------------------------------------------
-- 8. Auditoria de Carga (Contadores)
-- -----------------------------------------------------------------------------
SELECT 'municipio' AS tabela, COUNT(*) AS total FROM `municipio`
UNION ALL
SELECT 'unidade_gestora', COUNT(*) FROM `unidade_gestora`
UNION ALL
SELECT 'credor', COUNT(*) FROM `credor`
UNION ALL
SELECT 'licitacao', COUNT(*) FROM `licitacao`
UNION ALL
SELECT 'funcao', COUNT(*) FROM `funcao`
UNION ALL
SELECT 'programa', COUNT(*) FROM `programa`
UNION ALL
SELECT 'acao', COUNT(*) FROM `acao`
UNION ALL
SELECT 'categoria_economica', COUNT(*) FROM `categoria_economica`
UNION ALL
SELECT 'natureza_despesa', COUNT(*) FROM `natureza_despesa`
UNION ALL
SELECT 'modalidade_aplicacao', COUNT(*) FROM `modalidade_aplicacao`
UNION ALL
SELECT 'elemento_despesa', COUNT(*) FROM `elemento_despesa`
UNION ALL
SELECT 'fonte_recurso', COUNT(*) FROM `fonte_recurso`
UNION ALL
SELECT 'despesa', COUNT(*) FROM `despesa`;

-- -----------------------------------------------------------------------------
-- 9. Limpeza da Tabela Temporária e Restauração de Ambiente
-- -----------------------------------------------------------------------------
DROP TABLE `temp_despesas`;
COMMIT;

SET autocommit = 1;
SET UNIQUE_CHECKS = 1;
SET FOREIGN_KEY_CHECKS = 1;
SET SQL_SAFE_UPDATES = 1;