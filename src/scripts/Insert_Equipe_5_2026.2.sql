-- =============================================================================
-- SCRIPT DE CARGA E NORMALIZAÇÃO: Equipe 5 (2026.2)
-- Base de Dados: Despesas TCE-PB 2025 (Filtro: 1º Semestre)
-- =============================================================================

SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;
SET SQL_MODE = '';
SET SQL_SAFE_UPDATES = 0;
SET autocommit = 0;

USE `modelagem`;

-- -----------------------------------------------------
-- 1. Criação da Tabela Temporária de Staging
-- -----------------------------------------------------
DROP TABLE IF EXISTS `temp_despesas`;

CREATE TABLE `temp_despesas` (
    `municipio` VARCHAR(255),
    `codigo_unidade_gestora` VARCHAR(50),
    `descricao_unidade_gestora` TEXT,
    `numero_empenho` VARCHAR(50),
    `data_empenho` VARCHAR(50),
    `mes` VARCHAR(50),
    `cpf_cnpj` VARCHAR(50),
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

-- -----------------------------------------------------
-- 2. Carga do Arquivo CSV Bruto
-- -----------------------------------------------------
LOAD DATA INFILE '/var/lib/mysql-files/despesas-2025.csv'
INTO TABLE `temp_despesas`
FIELDS TERMINATED BY ';'
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

COMMIT;

-- -----------------------------------------------------
-- 3. Filtro: Manter Apenas o 1º Semestre (Janeiro a Junho)
-- Usa formato ISO (%Y-%m-%d) ou o prefixo do mês (01 a 06)
-- -----------------------------------------------------
DELETE FROM `temp_despesas`
WHERE CAST(LEFT(`mes`, 2) AS SIGNED) > 6
   OR `data_empenho` IS NULL 
   OR `data_empenho` = '';

COMMIT;

-- -----------------------------------------------------
-- 4. Carga das Tabelas de Dimensão (Normalização 2FN e 3FN)
-- Inclui registros padrão (código 0) para evitar órfãos nulos
-- -----------------------------------------------------
INSERT IGNORE INTO `dim_acao` (`codigo_acao`, `acao`)
SELECT DISTINCT CAST(`codigo_acao` AS SIGNED), `acao`
FROM `temp_despesas`
WHERE `codigo_acao` IS NOT NULL AND `codigo_acao` != '';

INSERT IGNORE INTO `dim_categoria_economica` (`codigo_categoria_economica`, `categoria_economica`)
SELECT DISTINCT CAST(`codigo_categoria_economica` AS SIGNED), `categoria_economica`
FROM `temp_despesas`
WHERE `codigo_categoria_economica` IS NOT NULL AND `codigo_categoria_economica` != '';

-- Dimensão CO com registro sentinela 0
INSERT IGNORE INTO `dim_co` (`co`, `descricao_co`) VALUES (0, 'Não Aplicável');
INSERT IGNORE INTO `dim_co` (`co`, `descricao_co`)
SELECT DISTINCT CAST(`co` AS DOUBLE), `descricao_co`
FROM `temp_despesas`
WHERE `co` IS NOT NULL AND `co` != '';

INSERT IGNORE INTO `dim_credor` (`cpf_cnpj`, `nome_credor`)
SELECT DISTINCT CAST(`cpf_cnpj` AS SIGNED), `nome_credor`
FROM `temp_despesas`
WHERE `cpf_cnpj` IS NOT NULL AND `cpf_cnpj` != '';

INSERT IGNORE INTO `dim_elemento_despesa` (`codigo_elemento_despesa`, `elemento_despesa`)
SELECT DISTINCT CAST(`codigo_elemento_despesa` AS SIGNED), `elemento_despesa`
FROM `temp_despesas`
WHERE `codigo_elemento_despesa` IS NOT NULL AND `codigo_elemento_despesa` != '';

INSERT IGNORE INTO `dim_fonte_recurso` (`codigo_fonte_recurso`, `descricao_fonte_recurso`)
SELECT DISTINCT CAST(`codigo_fonte_recurso` AS SIGNED), `descricao_fonte_recurso`
FROM `temp_despesas`
WHERE `codigo_fonte_recurso` IS NOT NULL AND `codigo_fonte_recurso` != '';

INSERT IGNORE INTO `dim_funcao` (`codigo_funcao`, `funcao`)
SELECT DISTINCT CAST(`codigo_funcao` AS SIGNED), `funcao`
FROM `temp_despesas`
WHERE `codigo_funcao` IS NOT NULL AND `codigo_funcao` != '';

INSERT IGNORE INTO `dim_modalidade_aplicacao` (`codigo_modalidade_aplicacao`, `modalidade_aplicacao`)
SELECT DISTINCT CAST(`codigo_modalidade_aplicacao` AS SIGNED), `modalidade_aplicacao`
FROM `temp_despesas`
WHERE `codigo_modalidade_aplicacao` IS NOT NULL AND `codigo_modalidade_aplicacao` != '';

INSERT IGNORE INTO `dim_natureza` (`codigo_natureza`, `grupo_natureza_despesa`)
SELECT DISTINCT CAST(`codigo_natureza` AS SIGNED), `grupo_natureza_despesa`
FROM `temp_despesas`
WHERE `codigo_natureza` IS NOT NULL AND `codigo_natureza` != '';

INSERT IGNORE INTO `dim_programa` (`codigo_programa`, `programa`)
SELECT DISTINCT CAST(`codigo_programa` AS SIGNED), `programa`
FROM `temp_despesas`
WHERE `codigo_programa` IS NOT NULL AND `codigo_programa` != '';

INSERT IGNORE INTO `dim_subfuncao` (`codigo_subfuncao`, `subfuncao`)
SELECT DISTINCT CAST(`codigo_subfuncao` AS SIGNED), `subfuncao`
FROM `temp_despesas`
WHERE `codigo_subfuncao` IS NOT NULL AND `codigo_subfuncao` != '';

-- Dimensão Unidade Gestora com registro sentinela 0
INSERT IGNORE INTO `dim_unidade_gestora` (`codigo_unidade_gestora`, `descricao_unidade_gestora`, `municipio`) 
VALUES (0, 'Não Informado', 'Não Informado');
INSERT IGNORE INTO `dim_unidade_gestora` (`codigo_unidade_gestora`, `descricao_unidade_gestora`, `municipio`)
SELECT DISTINCT CAST(`codigo_unidade_gestora` AS DOUBLE), `descricao_unidade_gestora`, `municipio`
FROM `temp_despesas`
WHERE `codigo_unidade_gestora` IS NOT NULL AND `codigo_unidade_gestora` != '';

INSERT IGNORE INTO `dim_unidade_orcamentaria` (`codigo_unidade_orcamentaria`, `descricao_unidade_orcamentaria`)
SELECT DISTINCT CAST(`codigo_unidade_orcamentaria` AS SIGNED), `descricao_unidade_orcamentaria`
FROM `temp_despesas`
WHERE `codigo_unidade_orcamentaria` IS NOT NULL AND `codigo_unidade_orcamentaria` != '';

COMMIT;

-- -----------------------------------------------------
-- 5. Carga da Tabela Fato
-- Trata datas no padrão %Y-%m-%d e zera nulos via COALESCE
-- -----------------------------------------------------
TRUNCATE TABLE `fato_empenhos`;

INSERT INTO `fato_empenhos` (
    `numero_empenho`,
    `data_empenho`,
    `mes`,
    `codigo_unidade_gestora`,
    `codigo_unidade_orcamentaria`,
    `cpf_cnpj`,
    `codigo_funcao`,
    `codigo_subfuncao`,
    `codigo_programa`,
    `codigo_acao`,
    `codigo_categoria_economica`,
    `codigo_natureza`,
    `codigo_modalidade_aplicacao`,
    `codigo_elemento_despesa`,
    `codigo_subelemento`,
    `codigo_subelemento_exibicao`,
    `codigo_fonte_recurso`,
    `co`,
    `numero_licitacao`,
    `modalidade_licitacao`,
    `numero_obra`,
    `valor_empenhado`,
    `valor_liquidado`,
    `valor_pago`,
    `historico`,
    `ano_fonte`
)
SELECT 
    CAST(NULLIF(`numero_empenho`, '') AS SIGNED),
    -- Conversão compatível com YYYY-MM-DD e DD/MM/YYYY
    COALESCE(
        STR_TO_DATE(LEFT(`data_empenho`, 10), '%Y-%m-%d'),
        STR_TO_DATE(LEFT(`data_empenho`, 10), '%d/%m/%Y')
    ),
    `mes`,
    COALESCE(CAST(NULLIF(`codigo_unidade_gestora`, '') AS DOUBLE), 0),
    CAST(NULLIF(`codigo_unidade_orcamentaria`, '') AS SIGNED),
    CAST(NULLIF(`cpf_cnpj`, '') AS SIGNED),
    CAST(NULLIF(`codigo_funcao`, '') AS SIGNED),
    CAST(NULLIF(`codigo_subfuncao`, '') AS SIGNED),
    CAST(NULLIF(`codigo_programa`, '') AS SIGNED),
    CAST(NULLIF(`codigo_acao`, '') AS SIGNED),
    CAST(NULLIF(`codigo_categoria_economica`, '') AS SIGNED),
    CAST(NULLIF(`codigo_natureza`, '') AS SIGNED),
    CAST(NULLIF(`codigo_modalidade_aplicacao`, '') AS SIGNED),
    CAST(NULLIF(`codigo_elemento_despesa`, '') AS SIGNED),
    CAST(NULLIF(`codigo_subelemento`, '') AS SIGNED),
    COALESCE(`codigo_subelemento_exibicao`, 'SEM SUBELEMENTO'),
    CAST(NULLIF(`codigo_fonte_recurso`, '') AS SIGNED),
    COALESCE(CAST(NULLIF(`co`, '') AS DOUBLE), 0),
    CAST(NULLIF(`numero_licitacao`, '') AS SIGNED),
    COALESCE(`modalidade_licitacao`, 'Sem Licitação'),
    CAST(NULLIF(`numero_obra`, '') AS SIGNED),
    COALESCE(CAST(REPLACE(REPLACE(NULLIF(`valor_empenhado`, ''), '.', ''), ',', '.') AS DOUBLE), 0.0),
    COALESCE(CAST(REPLACE(REPLACE(NULLIF(`valor_liquidado`, ''), '.', ''), ',', '.') AS DOUBLE), 0.0),
    COALESCE(CAST(REPLACE(REPLACE(NULLIF(`valor_pago`, ''), '.', ''), ',', '.') AS DOUBLE), 0.0),
    COALESCE(`historico`, ''),
    COALESCE(CAST(NULLIF(`ano_fonte`, '') AS SIGNED), 2025)
FROM `temp_despesas`;

COMMIT;

-- -----------------------------------------------------
-- 6. Validação das Cargas (Contadores)
-- -----------------------------------------------------
SELECT 'dim_acao' AS tabela, COUNT(*) AS total FROM `dim_acao`
UNION ALL
SELECT 'dim_credor', COUNT(*) FROM `dim_credor`
UNION ALL
SELECT 'dim_unidade_gestora', COUNT(*) FROM `dim_unidade_gestora`
UNION ALL
SELECT 'fato_empenhos', COUNT(*) FROM `fato_empenhos`;

-- -----------------------------------------------------
-- 7. Limpeza e Restauração das Restrições
-- -----------------------------------------------------
DROP TABLE `temp_despesas`;
COMMIT;

SET autocommit = 1;
SET UNIQUE_CHECKS = 1;
SET FOREIGN_KEY_CHECKS = 1;
SET SQL_SAFE_UPDATES = 1;