-- =============================================================================
-- SCRIPT DE CRIAÇÃO DO BANCO DE DADOS (DDL)
-- Equipe 5 - Disciplina de Modelagem e Banco de Dados (2026.2)
-- Base de Dados: Despesas TCE-PB (Execução Orçamentária)
-- =============================================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE SCHEMA IF NOT EXISTS `modelagem` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `modelagem` ;

-- -----------------------------------------------------
-- 1. Localidade e Órgãos Administrativos
-- -----------------------------------------------------
DROP TABLE IF EXISTS `modelagem`.`despesa` ;
DROP TABLE IF EXISTS `modelagem`.`unidade_gestora` ;
DROP TABLE IF EXISTS `modelagem`.`municipio` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`municipio` (
  `id_municipio` INT NOT NULL AUTO_INCREMENT,
  `nome_municipio` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id_municipio`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

CREATE TABLE IF NOT EXISTS `modelagem`.`unidade_gestora` (
  `codigo_unidade_gestora` INT NOT NULL,
  `nome_unidade_gestora` VARCHAR(255) NOT NULL,
  `id_municipio` INT NOT NULL,
  PRIMARY KEY (`codigo_unidade_gestora`),
  INDEX `fk_ug_municipio_idx` (`id_municipio` ASC) VISIBLE,
  CONSTRAINT `fk_ug_municipio`
    FOREIGN KEY (`id_municipio`)
    REFERENCES `modelagem`.`municipio` (`id_municipio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

-- -----------------------------------------------------
-- 2. Credores e Processos de Contratação
-- -----------------------------------------------------
DROP TABLE IF EXISTS `modelagem`.`credor` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`credor` (
  `cpf_cnpj` VARCHAR(255) NOT NULL,
  `nome_credor` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`cpf_cnpj`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

DROP TABLE IF EXISTS `modelagem`.`licitacao` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`licitacao` (
  `id_licitacao` INT NOT NULL AUTO_INCREMENT,
  `numero_licitacao` VARCHAR(50) NOT NULL DEFAULT 'Sem Licitação',
  `modalidade_licitacao` VARCHAR(100) NOT NULL DEFAULT 'Sem Licitação',
  PRIMARY KEY (`id_licitacao`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

-- -----------------------------------------------------
-- 3. Classificadores Orçamentários (LOA / STN)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `modelagem`.`funcao` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`funcao` (
  `codigo_funcao` INT NOT NULL,
  `nome_funcao` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`codigo_funcao`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

DROP TABLE IF EXISTS `modelagem`.`programa` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`programa` (
  `codigo_programa` INT NOT NULL,
  `nome_programa` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`codigo_programa`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

DROP TABLE IF EXISTS `modelagem`.`acao` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`acao` (
  `codigo_acao` VARCHAR(20) NOT NULL,
  `nome_acao` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`codigo_acao`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

DROP TABLE IF EXISTS `modelagem`.`categoria_economica` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`categoria_economica` (
  `codigo_categoria_economica` INT NOT NULL,
  `nome_categoria_economica` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`codigo_categoria_economica`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

DROP TABLE IF EXISTS `modelagem`.`natureza_despesa` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`natureza_despesa` (
  `codigo_natureza` INT NOT NULL,
  `nome_natureza_despesa` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`codigo_natureza`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

DROP TABLE IF EXISTS `modelagem`.`modalidade_aplicacao` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`modalidade_aplicacao` (
  `codigo_modalidade_aplicacao` INT NOT NULL,
  `nome_modalidade_aplicacao` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`codigo_modalidade_aplicacao`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

DROP TABLE IF EXISTS `modelagem`.`elemento_despesa` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`elemento_despesa` (
  `codigo_elemento_despesa` INT NOT NULL,
  `nome_elemento_despesa` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`codigo_elemento_despesa`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

DROP TABLE IF EXISTS `modelagem`.`fonte_recurso` ;

CREATE TABLE IF NOT EXISTS `modelagem`.`fonte_recurso` (
  `codigo_fonte_recurso` INT NOT NULL,
  `nome_fonte_recurso` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`codigo_fonte_recurso`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

-- -----------------------------------------------------
-- 4. Tabela Central: Execução da Despesa
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `modelagem`.`despesa` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `numero_empenho` INT NOT NULL,
  `data_empenho` DATE NOT NULL,
  `mes` VARCHAR(20) NOT NULL,
  `valor_empenhado` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `valor_liquidado` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `valor_pago` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `historico` TEXT NULL DEFAULT NULL,
  `codigo_unidade_gestora` INT NOT NULL,
  `cpf_cnpj` VARCHAR(255) NOT NULL,
  `id_licitacao` INT NOT NULL DEFAULT 1,
  `codigo_funcao` INT NOT NULL,
  `codigo_programa` INT NOT NULL,
  `codigo_acao` VARCHAR(20) NOT NULL,
  `codigo_categoria_economica` INT NOT NULL,
  `codigo_natureza` INT NOT NULL,
  `codigo_modalidade_aplicacao` INT NOT NULL,
  `codigo_elemento_despesa` INT NOT NULL,
  `codigo_fonte_recurso` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_despesa_ug_idx` (`codigo_unidade_gestora` ASC) VISIBLE,
  INDEX `fk_despesa_credor_idx` (`cpf_cnpj` ASC) VISIBLE,
  INDEX `fk_despesa_licitacao_idx` (`id_licitacao` ASC) VISIBLE,
  INDEX `fk_despesa_funcao_idx` (`codigo_funcao` ASC) VISIBLE,
  INDEX `fk_despesa_programa_idx` (`codigo_programa` ASC) VISIBLE,
  INDEX `fk_despesa_acao_idx` (`codigo_acao` ASC) VISIBLE,
  INDEX `fk_despesa_categoria_idx` (`codigo_categoria_economica` ASC) VISIBLE,
  INDEX `fk_despesa_natureza_idx` (`codigo_natureza` ASC) VISIBLE,
  INDEX `fk_despesa_modalidade_idx` (`codigo_modalidade_aplicacao` ASC) VISIBLE,
  INDEX `fk_despesa_elemento_idx` (`codigo_elemento_despesa` ASC) VISIBLE,
  INDEX `fk_despesa_fonte_idx` (`codigo_fonte_recurso` ASC) VISIBLE,
  CONSTRAINT `fk_despesa_ug`
    FOREIGN KEY (`codigo_unidade_gestora`)
    REFERENCES `modelagem`.`unidade_gestora` (`codigo_unidade_gestora`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_credor`
    FOREIGN KEY (`cpf_cnpj`)
    REFERENCES `modelagem`.`credor` (`cpf_cnpj`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_licitacao`
    FOREIGN KEY (`id_licitacao`)
    REFERENCES `modelagem`.`licitacao` (`id_licitacao`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_funcao`
    FOREIGN KEY (`codigo_funcao`)
    REFERENCES `modelagem`.`funcao` (`codigo_funcao`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_programa`
    FOREIGN KEY (`codigo_programa`)
    REFERENCES `modelagem`.`programa` (`codigo_programa`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_acao`
    FOREIGN KEY (`codigo_acao`)
    REFERENCES `modelagem`.`acao` (`codigo_acao`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_categoria`
    FOREIGN KEY (`codigo_categoria_economica`)
    REFERENCES `modelagem`.`categoria_economica` (`codigo_categoria_economica`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_natureza`
    FOREIGN KEY (`codigo_natureza`)
    REFERENCES `modelagem`.`natureza_despesa` (`codigo_natureza`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_modalidade`
    FOREIGN KEY (`codigo_modalidade_aplicacao`)
    REFERENCES `modelagem`.`modalidade_aplicacao` (`codigo_modalidade_aplicacao`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_elemento`
    FOREIGN KEY (`codigo_elemento_despesa`)
    REFERENCES `modelagem`.`elemento_despesa` (`codigo_elemento_despesa`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_despesa_fonte`
    FOREIGN KEY (`codigo_fonte_recurso`)
    REFERENCES `modelagem`.`fonte_recurso` (`codigo_fonte_recurso`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;