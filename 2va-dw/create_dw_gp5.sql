-- =============================================================================
-- DATA WAREHOUSE - MODELO DIMENSIONAL (STAR SCHEMA COM DIM_LOCAL)
-- Base: Despesas TCE-PB 2025
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS `dw_despesas` DEFAULT CHARACTER SET utf8mb4 ;
USE `dw_despesas` ;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `fatoDespesa`;
DROP TABLE IF EXISTS `dimData`;
DROP TABLE IF EXISTS `dimLocal`;
DROP TABLE IF EXISTS `dimUnidadeGestora`;
DROP TABLE IF EXISTS `dimCredor`;
DROP TABLE IF EXISTS `dimClassificacaoOrcamentaria`;
DROP TABLE IF EXISTS `dimLicitacao`;

-- -----------------------------------------------------------------------------
-- 1. Dimensão Data (Estrutura canônica do slide da professora)
-- -----------------------------------------------------------------------------
CREATE TABLE `dimData` (
  `keyData` INT NOT NULL,
  `data_id` DATETIME NOT NULL,
  `dia_ehdiautil` INT NOT NULL,
  `dia_numeronasemana` INT NOT NULL,
  `dia_numeronomes` INT NOT NULL,
  `dia_numeronoano` INT NOT NULL,
  `semana_id` INT NOT NULL,
  `semana_nome` VARCHAR(255) NOT NULL,
  `semana_texto` VARCHAR(255) NOT NULL,
  `semana_numeronoano` INT NOT NULL,
  `mes_id` INT NOT NULL,
  `mes_nome` VARCHAR(255) NOT NULL,
  `mes_texto` VARCHAR(255) NOT NULL,
  `mes_numeronoano` VARCHAR(255) NOT NULL,
  `trimestre_id` INT NOT NULL,
  `trimestre_nome` VARCHAR(255) NOT NULL,
  `trimestre_texto` VARCHAR(255) NOT NULL,
  `trimestre_numeronoano` INT NOT NULL,
  `semestre_id` INT NOT NULL,
  `semestre_nome` VARCHAR(255) NOT NULL,
  `semestre_texto` VARCHAR(255) NOT NULL,
  `semestre_numeronoano` INT NOT NULL,
  `ano_id` INT NOT NULL,
  `ano_nome` VARCHAR(255) NOT NULL,
  `ano_texto` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`keyData`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4;

-- -----------------------------------------------------------------------------
-- 2. Dimensão Local (Município)
-- -----------------------------------------------------------------------------
CREATE TABLE `dimLocal` (
  `key` INT NOT NULL AUTO_INCREMENT,
  `id_municipio` INT NOT NULL,
  `nome_municipio` VARCHAR(100) NOT NULL,
  `date_from` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `date_to` TIMESTAMP NULL DEFAULT NULL,
  `version` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`key`),
  INDEX `idx_local_origem` (`id_municipio` ASC)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4;

-- -----------------------------------------------------------------------------
-- 3. Dimensão Unidade Gestora (Órgão Executor)
-- -----------------------------------------------------------------------------
CREATE TABLE `dimUnidadeGestora` (
  `key` INT NOT NULL AUTO_INCREMENT,
  `codigo_unidade_gestora` INT NOT NULL,
  `nome_unidade_gestora` VARCHAR(255) NOT NULL,
  `date_from` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `date_to` TIMESTAMP NULL DEFAULT NULL,
  `version` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`key`),
  INDEX `idx_ug_origem` (`codigo_unidade_gestora` ASC)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4;

-- -----------------------------------------------------------------------------
-- 4. Dimensão Credor (Favorecido)
-- -----------------------------------------------------------------------------
CREATE TABLE `dimCredor` (
  `key` INT NOT NULL AUTO_INCREMENT,
  `cpf_cnpj` VARCHAR(255) NOT NULL,
  `nome_credor` VARCHAR(255) NOT NULL,
  `date_from` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `date_to` TIMESTAMP NULL DEFAULT NULL,
  `version` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`key`),
  INDEX `idx_credor_origem` (`cpf_cnpj` ASC)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4;

-- -----------------------------------------------------------------------------
-- 5. Dimensão Classificação Orçamentária (Hierarquia LOA)
-- -----------------------------------------------------------------------------
CREATE TABLE `dimClassificacaoOrcamentaria` (
  `key` INT NOT NULL AUTO_INCREMENT,
  `codigo_funcao` INT NOT NULL,
  `nome_funcao` VARCHAR(100) NOT NULL,
  `codigo_programa` INT NOT NULL,
  `nome_programa` VARCHAR(255) NOT NULL,
  `codigo_acao` VARCHAR(20) NOT NULL,
  `nome_acao` VARCHAR(255) NOT NULL,
  `codigo_categoria_economica` INT NOT NULL,
  `nome_categoria_economica` VARCHAR(100) NOT NULL,
  `codigo_natureza` INT NOT NULL,
  `nome_natureza_despesa` VARCHAR(100) NOT NULL,
  `codigo_modalidade_aplicacao` INT NOT NULL,
  `nome_modalidade_aplicacao` VARCHAR(100) NOT NULL,
  `codigo_elemento_despesa` INT NOT NULL,
  `nome_elemento_despesa` VARCHAR(100) NOT NULL,
  `codigo_fonte_recurso` INT NOT NULL,
  `nome_fonte_recurso` VARCHAR(255) NOT NULL,
  `date_from` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `date_to` TIMESTAMP NULL DEFAULT NULL,
  `version` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`key`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4;

-- -----------------------------------------------------------------------------
-- 6. Dimensão Licitação (Processo Licitatório / Sentinela)
-- -----------------------------------------------------------------------------
CREATE TABLE `dimLicitacao` (
  `key` INT NOT NULL AUTO_INCREMENT,
  `id_licitacao` INT NOT NULL,
  `numero_licitacao` VARCHAR(50) NOT NULL,
  `modalidade_licitacao` VARCHAR(100) NOT NULL,
  `date_from` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `date_to` TIMESTAMP NULL DEFAULT NULL,
  `version` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`key`),
  INDEX `idx_licitacao_origem` (`id_licitacao` ASC)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4;

-- -----------------------------------------------------------------------------
-- 7. Tabela Fato: fatoDespesa (PK Composta por 6 FKs)
-- -----------------------------------------------------------------------------
CREATE TABLE `fatoDespesa` (
  `dataKey` INT NOT NULL,
  `localKey` INT NOT NULL,
  `unidadeGestoraKey` INT NOT NULL,
  `credorKey` INT NOT NULL,
  `classificacaoKey` INT NOT NULL,
  `licitacaoKey` INT NOT NULL,
  `valorEmpenhado` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `valorLiquidado` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `valorPago` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `saldoAPagar` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`dataKey`, `localKey`, `unidadeGestoraKey`, `credorKey`, `classificacaoKey`, `licitacaoKey`),
  INDEX `fk_fato_data_idx` (`dataKey` ASC),
  INDEX `fk_fato_local_idx` (`localKey` ASC),
  INDEX `fk_fato_ug_idx` (`unidadeGestoraKey` ASC),
  INDEX `fk_fato_credor_idx` (`credorKey` ASC),
  INDEX `fk_fato_classificacao_idx` (`classificacaoKey` ASC),
  INDEX `fk_fato_licitacao_idx` (`licitacaoKey` ASC),
  CONSTRAINT `fk_fato_data`
    FOREIGN KEY (`dataKey`) REFERENCES `dimData` (`keyData`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_fato_local`
    FOREIGN KEY (`localKey`) REFERENCES `dimLocal` (`key`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_fato_ug`
    FOREIGN KEY (`unidadeGestoraKey`) REFERENCES `dimUnidadeGestora` (`key`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_fato_credor`
    FOREIGN KEY (`credorKey`) REFERENCES `dimCredor` (`key`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_fato_classificacao`
    FOREIGN KEY (`classificacaoKey`) REFERENCES `dimClassificacaoOrcamentaria` (`key`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_fato_licitacao`
    FOREIGN KEY (`licitacaoKey`) REFERENCES `dimLicitacao` (`key`)
    ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;