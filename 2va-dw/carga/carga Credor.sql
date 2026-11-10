USE `dw_despesas`;

-- 1. Desativa checagem de FK para limpar a tabela
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE `dw_despesas`.`dimcredor`;
SET FOREIGN_KEY_CHECKS = 1;

-- 2. Insere a Chave Zero exigida
SET SESSION SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
INSERT INTO `dw_despesas`.`dimcredor` 
    (`key`, `cpf_cnpj`, `nome_credor`, `date_from`, `date_to`, `version`)
VALUES 
    (0, '0', 'Sem Credor', '1970-01-01 00:00:01', '2038-01-01 00:00:00', 1);

-- 3. Insere todos os credores da base relacional
INSERT INTO `dw_despesas`.`dimcredor` 
    (`cpf_cnpj`, `nome_credor`, `date_from`, `date_to`, `version`)
SELECT 
    cpf_cnpj, 
    nome_credor, 
    '1970-01-01 00:00:01', 
    '2038-01-01 00:00:00', 
    1
FROM `modelagem`.`credor`
WHERE cpf_cnpj <> '0';