# 💻 Guia de Execução Local: MySQL Server & MySQL Workbench (Porta 3306)

Este guia orienta a execução do projeto em ambiente **bare-metal / nativo** (fora de containers Docker), utilizando uma instalação local do **MySQL Server 8.0** na porta padrão **3306** e o **MySQL Workbench**.

---

## 📌 Sumário

1. [Pré-requisitos e Ferramentas](#1-pré-requisitos-e-ferramentas)
2. [Download dos Arquivos do Projeto (Google Drive)](#2-download-dos-arquivos-do-projeto-google-drive)
3. [Configuração do Diretório Seguro do MySQL (`secure-file-priv`)](#3-configuração-do-diretório-seguro-do-mysql-secure-file-priv)
4. [Execução dos Scripts no MySQL Workbench](#4-execução-dos-scripts-no-mysql-workbench)
5. [Consultas de Validação e Auditoria Contábil](#5-consultas-de-validação-e-auditoria-contábil)
6. [Resolução de Problemas Frequentes](#6-resolução-de-problemas-frequentes)

---

## 1. Pré-requisitos e Ferramentas

* **[MySQL Server 8.0+](https://dev.mysql.com/downloads/mysql/)** instalado localmente e rodando como serviço (Porta padrão: `3306`).
* **[MySQL Workbench 8.0+](https://dev.mysql.com/downloads/workbench/)** instalado para execução gráfica e visualização do modelo EER.
* Espaço livre em disco: Mínimo de **8 GB** livres (para o CSV bruto e os arquivos de dados do InnoDB).

---

## 2. Download dos Arquivos do Projeto (Google Drive)

Caso deseje obter os artefatos consolidados (incluindo dumps prontos e a base bruta completa), acesse o repositório oficial da equipe no Google Drive:

🔗 **Google Drive**: [Pasta Compartilhada - Modelagem de Dados (Grupo 5)](https://drive.google.com/drive/folders/1WSZSHjmrSFi8i4FbKjitcYGoCbP1Uuwr?usp=drive_link)

### 📂 Estrutura de Arquivos Disponíveis no Drive

A pasta do Google Drive reúne os seguintes recursos:

* 📁 **`Dump_Mongo/`**: Exportação binária/BSON de todas as coleções do MongoDB.
* 📁 **`Dump_MySQL/`**: Dump SQL completo estruturado para restauração direta.
* 📁 **`modelagem-mongo-gp5-json-JSON_EXAMPLE_SCHEMA/`**: Exemplos de documentos e schemas JSON das coleções NoSQL.
* 📁 **`raw/`**: Base bruta original do TCE-PB extraída (`despesas-2025.csv`).
* 📄 **`Create_Equipe_5_2026.2.sql`**: Script DDL de criação do banco de dados, chaves primárias e estrangeiras.
* 📄 **`Insert_Equipe_5_2026.2(local).sql`**: Script DML de ingestão massiva e normalização 3FN configurado para caminhos locais do Windows.
* 📐 **`modelo_2025_gp5.mwb`**: Modelo conceitual/EER editável no MySQL Workbench.
* 🖼️ **`modelo_2025_gp5.png`**: Diagrama relacional visual de alta resolução.
* 📝 **`Validação da Base de Dados - Grupo 5`**: Relatório de testes contábeis e integridade relacional.

Extraia os arquivos baixados em uma pasta de trabalho local, por exemplo:
`C:\Users\eu\Documents\aModelagem\` (ou no diretório do repositório clonado).

---

## 3. Configuração do Diretório Seguro do MySQL (`secure-file-priv`)

Por motivos de segurança e prevenção contra ataques de injeção de arquivos, o MySQL Server bloqueia a execução do comando `LOAD DATA INFILE` fora de uma pasta autorizada.

### 3.1. Descobrir a Pasta Segura da sua Instalação

Abra o MySQL Workbench, conecte-se na sua instância local e execute:

```sql
SHOW VARIABLES LIKE 'secure_file_priv';
```

No **Windows**, o caminho padrão geralmente é:
```plaintext
C:\ProgramData\MySQL\MySQL Server 8.0\Uploads\
```

> [!NOTE]
> A pasta `ProgramData` é oculta por padrão no Windows Explorer. Para acessá-la, habilite a visualização de itens ocultos ou digite o caminho diretamente na barra de endereços do Explorer.

### 3.2. Copiar a Base Bruta para a Pasta Segura

Abra o **Prompt de Comando (CMD)** ou **PowerShell** como Administrador e execute o comando de cópia:

```cmd
:: Exemplo com o caminho padrão de trabalho:
copy "C:\Users\eu\Documents\aModelagem\raw\despesas-2025.csv" "C:\ProgramData\MySQL\MySQL Server 8.0\Uploads\despesas-2025.csv"
```

Se a sua pasta de trabalho ou o seu `secure_file_priv` estiver em outro local, substitua os caminhos:
```cmd
copy "SEU_CAMINHO_LOCAL\raw\despesas-2025.csv" "SUA_PASTA_SEGURA\despesas-2025.csv"
```

> [!IMPORTANT]
> Caso a sua variável `secure_file_priv` aponte para um diretório diferente do padrão, abra o script [`scripts/Insert_Equipe_5_2026.2(local).sql`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/Insert_Equipe_5_2026.2(local).sql) na linha **66** e atualize o caminho entre aspas simples para corresponder exatamente à localização do seu arquivo CSV:
> ```sql
> LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/despesas-2025.csv'
> ```
> *(Lembre-se de utilizar barras normais `/` no SQL, mesmo no ambiente Windows).*

---

## 4. Execução dos Scripts no MySQL Workbench

### Passo 1: Conexão Local
Abra o **MySQL Workbench** e clique na sua conexão local:
* **Host**: `localhost` (ou `127.0.0.1`)
* **Porta**: `3306`
* **Usuário**: `root` (ou seu usuário administrativo)

### Passo 2: Executar o Script DDL (Criação do Banco e Tabelas)
1. No menu superior, vá em **File** $\rightarrow$ **Open SQL Script...** (ou `Ctrl + Shift + O`).
2. Selecione o arquivo:
   [`scripts/Create_Equipe_5_2026.2.sql`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/Create_Equipe_5_2026.2.sql)
3. Clique no ícone de **Raio** (⚡) para executar todo o script.
4. O script criará o schema `modelagem`, as 13 tabelas normalizadas (3FN), suas chaves primárias, restrições de integridade referencial (`FOREIGN KEY NOT NULL`) e índices secundários.

### Passo 3: Executar o Script DML (Carga, Filtro e Normalização)
1. No menu superior, vá em **File** $\rightarrow$ **Open SQL Script...**.
2. Selecione o arquivo:
   [`scripts/Insert_Equipe_5_2026.2(local).sql`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/Insert_Equipe_5_2026.2(local).sql)
3. Clique no ícone de **Raio** (⚡).
4. O script executará as seguintes etapas automatizadas:
   - Criação da tabela de staging `temp_despesas`;
   - Ingestão massiva em alta performance via `LOAD DATA INFILE`;
   - Filtro temporal restrito ao 1º semestre de 2025 (meses 01 a 06);
   - Inserção dos registros sentinelas (códigos `0` ou `1`) para garantir tolerância zero a nulos;
   - Povoamento idempotente das 12 tabelas de domínio;
   - Povoamento da tabela central `despesa` com casts monetários e mapeamento de chaves;
   - Remoção automática da tabela de staging e restauração dos índices e chaves.

---

## 5. Consultas de Validação e Auditoria Contábil

Após a finalização do script de carga, abra uma nova aba de query no Workbench e execute os testes de conferência:

```sql
USE `modelagem`;

-- 1. Conferência da volumetria final consolidada (esperado: exatamente 1.068.148 linhas no 1º semestre)
SELECT COUNT(*) AS total_despesas FROM despesa;

-- 2. Auditoria de ausência estrita de nulos nas chaves e campos obrigatórios (deve retornar 0 em todas)
SELECT 
    COUNT(*) - COUNT(id) AS nulos_id,
    COUNT(*) - COUNT(numero_empenho) AS nulos_empenho,
    COUNT(*) - COUNT(data_empenho) AS nulos_data,
    COUNT(*) - COUNT(mes) AS nulos_mes,
    COUNT(*) - COUNT(codigo_unidade_gestora) AS nulos_ug,
    COUNT(*) - COUNT(cpf_cnpj) AS nulos_credor,
    COUNT(*) - COUNT(id_licitacao) AS nulos_licitacao,
    COUNT(*) - COUNT(codigo_funcao) AS nulos_funcao,
    COUNT(*) - COUNT(codigo_programa) AS nulos_programa,
    COUNT(*) - COUNT(codigo_acao) AS nulos_acao,
    COUNT(*) - COUNT(codigo_categoria_economica) AS nulos_categoria,
    COUNT(*) - COUNT(codigo_natureza) AS nulos_natureza,
    COUNT(*) - COUNT(codigo_modalidade_aplicacao) AS nulos_modalidade,
    COUNT(*) - COUNT(codigo_elemento_despesa) AS nulos_elemento,
    COUNT(*) - COUNT(codigo_fonte_recurso) AS nulos_fonte
FROM despesa;

-- 3. Consulta analítica integrando as tabelas de domínio via INNER JOIN
SELECT 
    d.numero_empenho,
    d.data_empenho,
    m.nome_municipio,
    ug.nome_unidade_gestora,
    c.nome_credor,
    l.modalidade_licitacao,
    f.nome_funcao,
    p.nome_programa,
    d.valor_empenhado,
    d.valor_liquidado,
    d.valor_pago
FROM despesa d
INNER JOIN unidade_gestora ug ON d.codigo_unidade_gestora = ug.codigo_unidade_gestora
INNER JOIN municipio m ON ug.id_municipio = m.id_municipio
INNER JOIN credor c ON d.cpf_cnpj = c.cpf_cnpj
INNER JOIN licitacao l ON d.id_licitacao = l.id_licitacao
INNER JOIN funcao f ON d.codigo_funcao = f.codigo_funcao
INNER JOIN programa p ON d.codigo_programa = p.codigo_programa
ORDER BY d.data_empenho DESC
LIMIT 10;
```

---

## 6. Resolução de Problemas Frequentes

### Erro 1290 (HY000): The MySQL server is running with the --secure-file-priv option so it cannot execute this statement
* **Causa**: O arquivo CSV está fora do diretório retornado por `SHOW VARIABLES LIKE 'secure_file_priv';`.
* **Solução**: Copie o arquivo CSV exatamente para a pasta autorizada do seu MySQL Server ou configure `secure-file-priv = ""` no arquivo de configuração `my.ini` (e reinicie o serviço do MySQL).

### Erro 2068 / 3948: Loading local data is disabled; this must be enabled on both the client and server sides
* **Causa**: O script tenta usar `LOAD DATA LOCAL INFILE` sem a flag global habilitada.
* **Solução**: O script do projeto utiliza `LOAD DATA INFILE` padrão (lado servidor), que lê diretamente da pasta local segura do MySQL sem necessitar da permissão `LOCAL`.

### Timeout de Execução no MySQL Workbench (Error Code: 2013)
* **Causa**: O Workbench possui um timeout padrão de 30 ou 60 segundos para consultas normais. Como a carga processa mais de 2 milhões de linhas antes do filtro, a execução pode demorar entre 1 e 3 minutos dependendo do seu hardware.
* **Solução**:
  1. No Workbench, vá em **Edit** $\rightarrow$ **Preferences...**.
  2. Clique na aba **SQL Editor**.
  3. No grupo **DBMS connection read timeout interval (in seconds)**, altere de `30` para `600` (ou `0` para desativar o timeout).
  4. Clique em **OK** e reconecte ao servidor.
