# 📊 Modelagem e Engenharia de Banco de Dados Relacional (OLTP / 3FN) e NoSQL (MongoDB): Despesas Públicas (TCE-PB 2025)

[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Latest-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Relational Migrator](https://img.shields.io/badge/MongoDB-Relational_Migrator-00684A?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/products/tools/relational-migrator)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![phpMyAdmin](https://img.shields.io/badge/phpMyAdmin-Latest-6C78AF?style=for-the-badge&logo=phpmyadmin&logoColor=white)](https://www.phpmyadmin.net/)
[![Mongo Express](https://img.shields.io/badge/Mongo_Express-Latest-13AA52?style=for-the-badge&logo=mongodb&logoColor=white)](https://github.com/mongo-express/mongo-express)
[![Workbench](https://img.shields.io/badge/MySQL_Workbench-8.0-00758F?style=for-the-badge&logo=mysql&logoColor=white)](https://dev.mysql.com/downloads/workbench/)
[![Modelo](https://img.shields.io/badge/Arquitetura-OLTP_%7C_3FN_%26_NoSQL-success?style=for-the-badge)](https://en.wikipedia.org/wiki/Third_normal_form)

Projeto acadêmico de modelagem e engenharia de banco de dados relacional transacional (**OLTP**), estritamente normalizado até a **3ª Forma Normal (3FN)**, e sua posterior modernização para modelo orientado a documentos (**NoSQL / MongoDB**), desenvolvido a partir dos microdados públicos de execução orçamentária do **Tribunal de Contas do Estado da Paraíba (TCE-PB)** para o **1º Semestre de 2025**.

O projeto estrutura o ciclo de vida da execução da despesa pública (**Empenho**, **Liquidação** e **Pagamento**) em torno de uma entidade transacional central (`despesa`), decomposta em 12 tabelas de domínio e localidade no ambiente relacional, e migrada para o MongoDB através do padrão **Extended Reference Pattern** com auxílio do **MongoDB Relational Migrator**. O ecossistema completo conta com conteinerização integrada via **Docker Compose**, scripts SQL puros de higienização/carga e esquemas NoSQL validados.

---

## 📌 Sumário

- [Origem dos Dados e Recorte Temporal](#-origem-dos-dados-e-recorte-temporal)
- [Ciclo da Despesa Orçamentária e Arquitetura Relacional](#️-ciclo-da-despesa-orçamentária-e-arquitetura-relacional)
- [Diagrama Entidade-Relacionamento (EER)](#-diagrama-entidade-relacionamento-eer)
- [Dicionário de Tabelas e Entidades](#-dicionário-de-tabelas-e-entidades)
- [Colunas Descartadas e Justificativas de Modelagem](#-colunas-descartadas-e-justificativas-de-modelagem)
- [Tratamento Documental: Preservação de CPF e CNPJ (VARCHAR)](#-tratamento-documental-preservação-de-cpf-e-cnpj-varchar)
- [Estratégia de Mitigação de Inconsistências e Nulos](#️-estratégia-de-mitigação-de-inconsistências-e-nulos)
- [Arquitetura de Infraestrutura (Docker)](#-arquitetura-de-infraestrutura-docker)
- [Pipeline de Carga e Normalização via SQL](#-pipeline-de-carga-e-normalização-via-sql)
- [Guia de Execução Passo a Passo (Ambiente Relacional / MySQL)](#-guia-de-execução-passo-a-passo-ambiente-relacional--mysql)
  - [1. Pré-requisitos](#1-pré-requisitos)
  - [2. Download da Base Bruta](#2-download-da-base-bruta)
  - [3. Iniciar os Serviços Docker](#3-iniciar-os-serviços-docker)
  - [4. Copiar o CSV para a Pasta do MySQL](#4-copiar-o-csv-para-a-pasta-do-mysql)
  - [5. Executar os Scripts de Criação e Carga](#5-executar-os-scripts-de-criação-e-carga)
  - [6. Validação e Auditoria dos Dados](#6-validação-e-auditoria-dos-dados)
- [Modelagem NoSQL e Migração para MongoDB](#-modelagem-nosql-e-migração-para-mongodb)
  - [Diagrama da Arquitetura Orientada a Documentos](#diagrama-da-arquitetura-orientada-a-documentos)
  - [Racional Arquitetural: Agrupamento em despesa vs. Coleção credor](#racional-arquitetural-agrupamento-em-despesa-vs-coleção-credor)
  - [Guia de Migração e Carga no MongoDB via Relational Migrator](#guia-de-migração-e-carga-no-mongodb-via-relational-migrator)
- [Estrutura do Repositório](#-estrutura-do-repositório)
  - [Visão em Árvore](#visão-em-árvore)
  - [Organização e Papel das Pastas](#organização-e-papel-das-pastas)

---

## 🌐 Origem dos Dados e Recorte Temporal

Os microdados foram obtidos através do portal de transparência e dados abertos do **Tribunal de Contas do Estado da Paraíba (TCE-PB)**:

* **Portal**: [TCE-PB Dados Abertos - Dados Consolidados](https://dados-abertos.tce.pb.gov.br/dados-consolidados)
* **Dataset**: Despesas consolidadas do exercício de 2025 (`despesas-2025.csv`).
* **Volume Bruto Anual**: **2.387.532 linhas** e **40 colunas** desnormalizadas (~1.95 GB).
* **Corte Temporal Aplicado**: **1º Semestre de 2025** (Janeiro a Junho — **1.068.148 registros validados**).

> [!NOTE]
> **Racional do Corte Temporal**: A restrição do dataset ao 1º semestre (meses $\le 6$) viabiliza a auditoria contábil de um ciclo fiscal semestral completo e fechado, assegurando viabilidade no carregamento transacional do banco de dados relacional sem estouro de memória ou limites de timeout de conexão.

---

## 🏛️ Ciclo da Despesa Orçamentária e Arquitetura Relacional

Conforme a **Lei Federal nº 4.320/1964**, a execução da despesa pública não é uma métrica estática, mas um processo contábil executado em três estágios cronológicos sucessivos:

$$ \text{1. Empenho} \longrightarrow \text{2. Liquidação} \longrightarrow \text{3. Pagamento} \Longrightarrow \text{Despesa} $$

1. **Empenho**: Ato emanado por autoridade competente que cria para o Estado a obrigação de pagamento pendente ou não de implemento de condição, reservando a dotação orçamentária necessária.
2. **Liquidação**: Verificação do direito adquirido pelo credor, baseada em títulos e comprovantes da prestação efetiva do serviço ou entrega do bem.
3. **Pagamento**: Emissão da ordem bancária e quitação financeira extinguindo a obrigação do poder público.

### Transição de Data Warehouse (OLAP) para Modelo Relacional Puro (OLTP / 3FN)

Em substituição a modelos analíticos de Business Intelligence baseados em *Star Schema* (`fato_` e `dim_`), o banco de dados foi estruturado estritamente sob as regras da **3ª Forma Normal (3FN)**:

* **Entidade Central `despesa`**: Consolida os atributos transacionais e os valores monetários das três fases do gasto (`valor_empenhado`, `valor_liquidado`, `valor_pago` tipados em `DECIMAL(15,2)`), associando-os às respectivas entidades de domínio através de Chaves Estrangeiras (FK).
* **Eliminação de Dependências Transitivas em Localidades**: Criação da tabela `municipio`, associando-se hierarquicamente à `unidade_gestora` (`unidade_gestora.id_municipio` $\rightarrow$ `municipio.id_municipio`).
* **Desacoplamento de Domínios**: Categorias de contratação (`licitacao`), agentes econômicos (`credor`) e classificadores funcionais e orçamentários padronizados pela STN e MOG foram isolados em tabelas próprias.

---

## 📐 Diagrama Entidade-Relacionamento (EER)

```mermaid
erDiagram
    municipio ||--o{ unidade_gestora : "localiza"
    unidade_gestora ||--o{ despesa : "executa"
    credor ||--o{ despesa : "favorecido"
    licitacao ||--o{ despesa : "origina"
    funcao ||--o{ despesa : "classifica"
    programa ||--o{ despesa : "planeja"
    acao ||--o{ despesa : "destina"
    categoria_economica ||--o{ despesa : "enquadra"
    natureza_despesa ||--o{ despesa : "agrupa"
    modalidade_aplicacao ||--o{ despesa : "aplica"
    elemento_despesa ||--o{ despesa : "especifica"
    fonte_recurso ||--o{ despesa : "financia"

    municipio {
        int id_municipio PK
        varchar nome_municipio
    }

    unidade_gestora {
        int codigo_unidade_gestora PK
        varchar nome_unidade_gestora
        int id_municipio FK
    }

    credor {
        varchar cpf_cnpj PK
        varchar nome_credor
    }

    licitacao {
        int id_licitacao PK
        varchar numero_licitacao
        varchar modalidade_licitacao
        varchar numero_obra
    }

    funcao {
        int codigo_funcao PK
        varchar nome_funcao
    }

    programa {
        int codigo_programa PK
        varchar nome_programa
    }

    acao {
        varchar codigo_acao PK
        varchar nome_acao
    }

    categoria_economica {
        int codigo_categoria_economica PK
        varchar nome_categoria_economica
    }

    natureza_despesa {
        int codigo_natureza PK
        varchar nome_natureza_despesa
    }

    modalidade_aplicacao {
        int codigo_modalidade_aplicacao PK
        varchar nome_modalidade_aplicacao
    }

    elemento_despesa {
        int codigo_elemento_despesa PK
        varchar nome_elemento_despesa
    }

    fonte_recurso {
        int codigo_fonte_recurso PK
        varchar nome_fonte_recurso
    }

    despesa {
        int id PK "Surrogate Key (AUTO_INCREMENT)"
        int numero_empenho
        date data_empenho
        varchar mes
        decimal valor_empenhado
        decimal valor_liquidado
        decimal valor_pago
        text historico
        int codigo_unidade_gestora FK
        varchar cpf_cnpj FK
        int id_licitacao FK
        int codigo_funcao FK
        int codigo_programa FK
        varchar codigo_acao FK
        int codigo_categoria_economica FK
        int codigo_natureza FK
        int codigo_modalidade_aplicacao FK
        int codigo_elemento_despesa FK
        int codigo_fonte_recurso FK
    }
```

O modelo relacional conceitual/lógico original está armazenado em:
📁 [`src/scripts/sql/modelo_2025.mwb`](ou [`src/modelo_2025.mwb`]).  
O diagrama visual exportado em alta resolução está disponível em:
🖼️ [`src/img/eer_diagram.png`].

---

## 📋 Dicionário de Tabelas e Entidades

O banco de dados físico implementado consolida **13 tabelas**:

| Tabela | Tipo | Chave Primária (PK) | Chaves Estrangeiras (FK) | Descrição do Domínio |
| :--- | :--- | :--- | :--- | :--- |
| **`despesa`** | Central / Transacional | `id` (`INT AI`) | 10 FKs associadas | Execução orçamentária contendo número do empenho, data, mês, histórico e os valores empenhado, liquidado e pago. |
| **`municipio`** | Domínio / Localidade | `id_municipio` (`INT AI`) | Nenhuma | Municípios do Estado da Paraíba responsáveis pelas administrações públicas. |
| **`unidade_gestora`** | Entidade Administrativa | `codigo_unidade_gestora` (`INT`) | `id_municipio` | Órgãos executores da despesa (prefeituras, câmaras, fundos municipais). |
| **`credor`** | Agente Econômico | `cpf_cnpj` (`VARCHAR(255)`) | Nenhuma | Fornecedores, servidores e prestadores de serviços recebedores dos pagamentos. |
| **`licitacao`** | Processo Administrativo | `id_licitacao` (`INT AI`) | Nenhuma | Identificação do processo licitatório, número do certame, modalidade e registro de obra. |
| **`funcao`** | Classificador Orçamentário | `codigo_funcao` (`INT`) | Nenhuma | Maior nível de agregação das áreas de atuação do setor público (ex: Saúde, Educação). |
| **`programa`** | Planejamento Orçamentário | `codigo_programa` (`INT`) | Nenhuma | Programas governamentais estabelecidos no Plano Plurianual (PPA). |
| **`acao`** | Instrumento de Despesa | `codigo_acao` (`VARCHAR(20)`) | Nenhuma | Projetos, atividades ou operações especiais com finalidade específica. |
| **`categoria_economica`** | Contabilidade Pública | `codigo_categoria_economica` (`INT`) | Nenhuma | Despesas Correntes (3) ou Despesas de Capital (4). |
| **`natureza_despesa`** | Contabilidade Pública | `codigo_natureza` (`INT`) | Nenhuma | Grupo de Natureza da Despesa (GND): Pessoal, Juros, Investimentos, etc. |
| **`modalidade_aplicacao`** | Contabilidade Pública | `codigo_modalidade_aplicacao` (`INT`) | Nenhuma | Especificação da destinação direta ou transferências intergovernamentais. |
| **`elemento_despesa`** | Contabilidade Pública | `codigo_elemento_despesa` (`INT`) | Nenhuma | Desdobramento específico do gasto (vencimentos, serviços de terceiros, diárias). |
| **`fonte_recurso`** | Financiamento Público | `codigo_fonte_recurso` (`INT`) | Nenhuma | Mecanismo financeiro e origem orçamentária que custeia a despesa. |

---

## 🗑️ Colunas Descartadas e Justificativas de Modelagem

A base de dados bruta original continha 40 colunas desnormalizadas. No processo de engenharia reversa e reestruturação para a 3FN, **11 colunas foram descartadas** com base em critérios técnicos e diretrizes acadêmicas:

| Coluna Bruta Original | Destino no Projeto | Justificativa Técnica e de Modelagem |
| :--- | :---: | :--- |
| **`codigo_subfuncao`**<br>**`subfuncao`** | Descartadas | **Eliminação de sub-hierarquias excessivas**: Atendimento direto à diretriz de remover tabelas *"SUB"*. A classificação setorial foi concentrada na entidade principal `funcao`, simplificando as junções sem perda de granularidade funcional. |
| **`codigo_subelemento`**<br>**`codigo_subelemento_exibicao`** | Descartadas | **Eliminação de desdobramentos redundantes**: O nível analítico contábil oficial da despesa é assegurado pela tabela `elemento_despesa`. A divisão em subelementos gerava excesso de registros textuais nulos na origem. |
| **`codigo_unidade_orcamentaria`**<br>**`descricao_unidade_orcamentaria`** | Descartadas | **Eliminação de órgão subordinado**: Em conformidade com o feedback de modelagem de evitar múltiplos níveis administrativos, a gestão orçamentária foi unificada no órgão executor formal (`unidade_gestora`). |
| **`co`** *(Cód. de Operação)*<br>**`descricao_co`** | Descartadas | **Tratamento de completude de dados**: Atributo financeiro auxiliar com mais de 73% de valores nulos/vazios na origem (preenchimento restrito a repasses específicos de Saúde/FUNDEB), dispensável na execução orçamentária geral. |
| **`ano_fonte`** | Descartada | **Redundância temporal**: Metadado contábil idêntico ao exercício fiscal corrente de 2025 já registrado na data de emissão do empenho (`data_empenho`). |
| **`uf`** *(da tabela municipio)* | Descartada | **Redundância factual estrita**: O dataset fiscaliza exclusivamente os 223 municípios do Estado da Paraíba (PB). Manter uma coluna `uf` com valor unívoco constituiria redundância dimensional desnecessária. |

---

## 🆔 Tratamento Documental: Preservação de CPF e CNPJ (VARCHAR)

Nas primeiras versões do projeto, o atributo identificador de credores (`cpf_cnpj`) era tipado numericamente como `BIGINT`. Essa abordagem acarretava truncamento involuntário e perda irreparável de dados:

### O Problema da Tipagem Numérica (`BIGINT`)

Na matemática computacional, valores inteiros descartam zeros à esquerda:

$$ \text{CAST}('00000000000191' \text{ AS SIGNED}) \Longrightarrow 191 $$

* O **Banco do Brasil** (CNPJ matriz `00.000.000/0001-91`) era gravado no banco como `191`.
* CPFs de pessoas físicas com zeros à esquerda (ex: `00008086298167`) tinham seus dígitos iniciais desconsiderados, impedindo buscas literais e validações de máscara.

### A Solução Adotada (`VARCHAR(255)`)

A coluna `cpf_cnpj` foi convertida formalmente para **`VARCHAR(255)`** tanto na tabela de domínio `credor` quanto na tabela transacional `despesa`:
* Preserva integralmente o formato padronizado de 14 caracteres do TCE-PB (14 dígitos para CNPJ ou 11 dígitos com preenchimento de zeros à esquerda para CPF).
* Habilita a aplicação direta de validações com algoritmos de dígito verificador da Receita Federal e consultas indexadas via `WHERE cpf_cnpj = '00000000000191'`.

---

## 🛡️ Estratégia de Mitigação de Inconsistências e Nulos

Para manter integridade referencial estrita (`FOREIGN KEY NOT NULL`) e prevenir falhas durante o carregamento de mais de 1 milhão de linhas, foram implementadas as seguintes soluções nos scripts SQL:

| Situação Encontrada | Causa Raiz na Origem | Tratamento Aplicado no Script SQL (`Insert_Equipe_5_2026.2.sql`) |
| :--- | :--- | :--- |
| **Inconsistência de Datas** | Alternância de formatos `YYYY-MM-DD` e `DD/MM/YYYY` no CSV | Conversão dinâmica com dupla checagem:<br>`COALESCE(STR_TO_DATE(LEFT(data, 10), '%Y-%m-%d'), STR_TO_DATE(LEFT(data, 10), '%d/%m/%Y'), '2025-01-01')` |
| **Valores Financeiros Formatados** | Formato de moeda brasileiro (`1.250,50` com pontos de milhar e vírgula decimal) | Sanitização em tempo de carga com conversão monetária:<br>`COALESCE(CAST(REPLACE(REPLACE(val, '.', ''), ',', '.') AS DECIMAL(15,2)), 0.00)` |
| **Compras sem Licitação** | Despesas diretas ou adiantamentos sem processo licitatório | Criação do Registro Sentinela `id_licitacao = 1` com a descrição `'Sem Licitação'`, associado via `COALESCE`. |
| **Deslocamento de Colunas (Linhas Órfãs)** | Registros brutos com código 0 e textos vizinhos vazados | Cláusula de proteção `WHERE CAST(codigo AS SIGNED) > 0`, garantindo apenas códigos legítimos e inserindo explicitamente `(0, 'Não Informado')`. |
| **Unidades Gestoras sem Município** | Registros administrativos com código 0 | Criação do Município Sentinela `id_municipio = 1` (`'Não Informado'`) associado à Unidade Gestora 0. |

---

## 🐳 Arquitetura de Infraestrutura (Docker)

O ambiente completo de bancos de dados relacionais e NoSQL, bem como suas respectivas interfaces de gestão gráfica, é provisionado via **Docker Compose** integrado na mesma rede interna (`docker-compose.yml`), garantindo isolamento e portabilidade:

### Serviços Configurados

| Serviço | Container | Imagem | Porta Host:Container | Descrição |
| :--- | :--- | :--- | :---: | :--- |
| **`db`** | `mysql_modelagem` | `mysql:8.0` | `3307:3306` | SGBD Relacional MySQL 8.0 com volume persistente. |
| **`phpmyadmin`** | `phpmyadmin_modelagem` | `phpmyadmin:latest` | `8080:80` | Interface gráfica Web para inspeção e auditoria SQL. |
| **`mongodb`** | `mongodb_modelagem` | `mongo:latest` | `27017:27017` | SGBD NoSQL orientado a documentos com autenticação ativada. |
| **`mongo-express`** | `mongo_express_modelagem` | `mongo-express:latest` | `8081:8081` | Interface Web para exploração e visualização de coleções BSON/JSON. |

### Parâmetros de Conexão

* **MySQL Host / Porta**: `localhost:3307` | **Database**: `modelagem`
  * **Usuário Comum**: `usuario` | **Senha**: `senhasegura`
  * **Root**: `root` | **Senha**: `rootpassword`
* **URL phpMyAdmin**: [http://localhost:8080](http://localhost:8080)
* **MongoDB Host / Porta**: `localhost:27017` | **Database**: `modelagem`
  * **Root**: `root` | **Senha**: `rootpassword`
  * **URI de Conexão**: `mongodb://root:rootpassword@localhost:27017/modelagem?authSource=admin`
* **URL Mongo Express**: [http://localhost:8081](http://localhost:8081)

---

## ⚙️ Pipeline de Carga e Normalização via SQL

O processo dispensa interpretadores intermediários, sendo executado nativamente pelo motor InnoDB do MySQL através de scripts SQL puros:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Arquivo CSV Bruto: despesas-2025.csv                 │
│                          (2.387.532 linhas brutas)                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼  LOAD DATA INFILE
┌─────────────────────────────────────────────────────────────────────────┐
│                     Tabela Temporária: temp_despesas                    │
│                     (Staging com tipagem tolerante)                     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼  DELETE WHERE mes > 6
┌─────────────────────────────────────────────────────────────────────────┐
│                  Filtro Temporal do 1º Semestre (2025)                  │
│                     (1.068.148 registros validados)                     │
└──────────────────┬──────────────────────────────────┬───────────────────┘
                   │                                  │
                   ▼                                  ▼
┌──────────────────────────────────────┐   ┌──────────────────────────────┐
│  INSERT IGNORE ... SELECT DISTINCT   │   │ INSERT INTO despesa          │
│  - Popula as 12 tabelas de domínio   │   │ - Mapeia valores empenhado,  │
│  - Gera localidade (municipio/UG)    │   │   liquidado e pago           │
│  - Registros sentinelas (código 0)   │   │ - Converte chaves FK         │
└──────────────────────────────────────┘   └──────────────────────────────┘
                                                          │
                                                          ▼  DROP TABLE
                                           ┌──────────────────────────────┐
                                           │ Limpeza da Tabela de Staging │
                                           │ Restauração de Checks e FKs  │
                                           └──────────────────────────────┘
```

1. **[`Create_Equipe_5_2026.2.sql`] (DDL)**:
   - Cria o schema `modelagem` com charset `utf8mb4`.
   - Cria as 13 tabelas relacionais, chaves primárias, chaves estrangeiras com restrições de integridade referencial (`ON DELETE NO ACTION ON UPDATE NO ACTION`) e índices secundários de consulta (`INDEX`).

2. **[`Insert_Equipe_5_2026.2.sql`] (DML)**:
   - Criação da staging table `temp_despesas`.
   - Ingestão massiva em alta velocidade via `LOAD DATA INFILE`.
   - Recorte analítico do 1º semestre via `DELETE FROM temp_despesas WHERE CAST(LEFT(mes, 2) AS SIGNED) > 6`.
   - Povoamento idempotente das 12 tabelas de domínio com `INSERT IGNORE ... SELECT DISTINCT`.
   - Povoamento da tabela central `despesa` aplicando casts, conversões e mapeamentos de integridade referencial.
   - Descarte automático da staging table (`DROP TABLE temp_despesas`) e restauração das restrições.

---

## 🚀 Guia de Execução Passo a Passo (Ambiente Relacional / MySQL)

### 1. Pré-requisitos

* [Docker Desktop](https://www.docker.com/) instalado e em execução.
* [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) (opcional, para visualização de diagrama).

### 2. Download da Base Bruta

1. Acesse o portal: [TCE-PB Dados Abertos - Consolidados](https://dados-abertos.tce.pb.gov.br/dados-consolidados).
2. Na seção **Despesas**, baixe o pacote do exercício de **2025**.
3. Extraia o CSV para a pasta `src/raw/` com o nome exato:
   ```plaintext
   src/raw/despesas-2025.csv
   ```

### 3. Iniciar os Serviços Docker

Na pasta `src/`, suba os containers via Docker Compose:

```bash
cd src
docker compose up -d
```

Verifique o status dos serviços:
```bash
docker compose ps
```

### 4. Copiar o CSV para a Pasta do MySQL

O MySQL restringe cargas locais fora do caminho seguro (`secure-file-priv`). Transfira o arquivo para o container:

```bash
docker cp raw/despesas-2025.csv mysql_modelagem:/var/lib/mysql-files/despesas-2025.csv
```

### 5. Executar os Scripts de Criação e Carga

Execute os comandos a partir da raiz do repositório:

#### 🪟 Windows (PowerShell):

```powershell
# 1. Criação do Banco de Dados e Tabelas (DDL)
Get-Content src/scripts/sql/Create_Equipe_5_2026.2.sql | docker exec -i mysql_modelagem mysql -uroot -prootpassword modelagem

# 2. Carga, Filtro do 1º Semestre e Normalização Relacional (DML)
Get-Content src/scripts/sql/Insert_Equipe_5_2026.2.sql | docker exec -i mysql_modelagem mysql -uroot -prootpassword modelagem
```

#### 🐧 Linux / macOS (Bash) ou Prompt de Comando (CMD):

```bash
# 1. Criação do Banco de Dados e Tabelas (DDL)
docker exec -i mysql_modelagem mysql -uroot -prootpassword modelagem < src/scripts/sql/Create_Equipe_5_2026.2.sql

# 2. Carga, Filtro do 1º Semestre e Normalização Relacional (DML)
docker exec -i mysql_modelagem mysql -uroot -prootpassword modelagem < src/scripts/sql/Insert_Equipe_5_2026.2.sql
```

### 6. Validação e Auditoria dos Dados

Abra o phpMyAdmin em [http://localhost:8080](http://localhost:8080) ou conecte o Workbench na porta `3307` e execute a verificação contábil:

```sql
USE `modelagem`;

-- 1. Total de registros da tabela despesa (esperado: exatamente 1.068.148 linhas no 1º semestre)
SELECT COUNT(*) AS total_despesas FROM despesa;

-- 2. Auditoria de ausência de nulos em chaves primárias e campos obrigatórios
SELECT 
    COUNT(*) - COUNT(id) AS nulos_id,
    COUNT(*) - COUNT(data_empenho) AS nulos_data,
    COUNT(*) - COUNT(codigo_unidade_gestora) AS nulos_ug,
    COUNT(*) - COUNT(cpf_cnpj) AS nulos_credor
FROM despesa;

-- 3. Consulta analítica integrando a execução dos 3 estágios da despesa
SELECT 
    d.numero_empenho,
    d.data_empenho,
    m.nome_municipio,
    ug.nome_unidade_gestora,
    c.nome_credor,
    d.valor_empenhado,
    d.valor_liquidado,
    d.valor_pago
FROM despesa d
JOIN unidade_gestora ug ON d.codigo_unidade_gestora = ug.codigo_unidade_gestora
JOIN municipio m ON ug.id_municipio = m.id_municipio
JOIN credor c ON d.cpf_cnpj = c.cpf_cnpj
ORDER BY d.data_empenho DESC
LIMIT 10;
```

---

## 🍃 Modelagem NoSQL e Migração para MongoDB

A migração do modelo relacional normalizado (OLTP / 3FN) para o banco de dados orientado a documentos (**MongoDB**) foi projetada utilizando o padrão arquitetural **Extended Reference Pattern** (Modelo Híbrido), implementado visualmente e executado via **MongoDB Relational Migrator**.

### Diagrama da Arquitetura Orientada a Documentos

```mermaid
graph TD
    subgraph "MongoDB: Database modelagem"
        direction TB
        C["Coleção: credor"]
        D["Coleção: despesa"]
        
        subgraph "Documento: despesa"
            direction TB
            D1["Campos Transacionais: numeroEmpenho, dataEmpenho, mes, valores..."]
            D2["Subdocumento: credor { cpfCnpj, nomeCredor }"]
            D3["Subdocumento: unidadeGestora { ..., municipio }"]
            D4["Subdocumento: licitacao"]
            D5["Subdocumentos Orçamentários: funcao, programa, acao, elemento..."]
        end
    end
    
    C -. "Extended Reference (Cadastro Central)" .-> D2
```

### 🧠 Racional Arquitetural: Agrupamento em `despesa` vs. Coleção `credor`

A decisão de incorporar 11 tabelas dentro do documento `despesa` e manter apenas `credor` como coleção separada fundamenta-se nos princípios centrais de modelagem de documentos:

#### 1. Por que incorporar classificadores, licitação e localidade na despesa?
* **Atomicidade do Ato Orçamentário**: No setor público (Lei 4.320/64), uma despesa é caracterizada por sua dotação completa (Função, Programa, Ação, Elemento, Fonte, Unidade Gestora). Esses classificadores possuem baixa cardinalidade (entre 2 e 1.100 registros) e são conceitualmente imutáveis após a liquidação do empenho.
* **Eliminação de `$lookup` (Zero Joins)**: Armazenar esses dados incorporados (*embedded*) permite que qualquer relatório analítico de gastos (ex.: despesas de Saúde em Amparo) seja consultado em uma única operação de I/O em disco, dispensando os múltiplos *JOINs* que tornavam o modelo relacional custoso.

#### 2. Por que manter a coleção independente `credor`?
* **Alta Cardinalidade e Entidade de Negócio**: O universo de credores soma **168.771 registros distintos** (CPFs e CNPJs de fornecedores, servidores e terceirizados). O credor possui ciclo de vida próprio e independe de haver empenho no mês vigente.
* **Consultas Cadastrais Diretas**: Manter a coleção de topo `credor` viabiliza análises cadastrais (auditorias fiscais, listas de fornecedores contratados) sem a necessidade de varrer exaustivamente a coleção de 1 milhão de transações de despesas.
* **Aplicação do Extended Reference Pattern**: Para manter as consultas financeiras rápidas sem abrir mão do catálogo mestre, adota-se o modelo híbrido:
  - A coleção `credor` guarda o **cadastro primário completo** (`cpfCnpj`, `nomeCredor`).
  - A coleção `despesa` embute apenas a **referência necessária para exibição imediata**:
    ```json
    {
      "credor": {
        "cpfCnpj": "00000000000191",
        "nomeCredor": "BANCO DO BRASIL SA"
      }
    }
    ```

---

### 🚀 Guia de Migração e Carga no MongoDB via Relational Migrator

O projeto de migração está formalmente configurado e armazenado em:  
📁 [`src/scripts/nosql/migracao_modelagem.relmig`]
com schemas JSON complementares em [`src/scripts/nosql/credor_MongoDBSchema.json`] e [`src/scripts/nosql/despesa_MongoDBSchema.json`].

Siga os passos abaixo para replicar a migração do MySQL para o MongoDB:

#### Passo 1: Inicializar o Ambiente Docker
Certifique-se de que os serviços MySQL e MongoDB estão rodando:
```bash
cd src
docker compose up -d
docker compose ps
```

#### Passo 2: Importar o Projeto no MongoDB Relational Migrator
1. Abra o aplicativo desktop oficial [MongoDB Relational Migrator](https://www.mongodb.com/products/tools/relational-migrator).
2. Na tela inicial, clique em **Import project** (ou **Open Project**).
3. Selecione o arquivo de migração do projeto:
   ```plaintext
   src/scripts/nosql/migracao_modelagem.relmig
   ```
4. O projeto carregará automaticamente as 13 tabelas do MySQL e as regras de transformação NoSQL já configuradas (mapeamento das 11 tabelas como subdocumentos incorporados em `despesa` e criação da coleção de topo `credor`).

#### Passo 3: Conectar aos Bancos de Dados
Configure os nós de conexão no aplicativo:
* **Origem (Source - MySQL)**:
  * **Host**: `localhost` | **Porta**: `3307`
  * **Usuário**: `root` | **Senha**: `rootpassword`
  * **Database**: `modelagem`
* **Destino (Target - MongoDB)**:
  * **Connection String**: `mongodb://root:rootpassword@localhost:27017/modelagem?authSource=admin`

#### Passo 4: Executar a Migração
1. Acesse a aba **Data Migration** no menu superior do Migrator.
2. Crie um novo job no modo **Snapshot** (Carga em lote pontual).
3. Selecione as coleções de destino: **`despesa`** e **`credor`**.
4. Clique em **Start** e acompanhe o progresso do carregamento.

---

## 📂 Estrutura do Repositório

### Visão em Árvore

```plaintext
modelagem/
├── README.md                                  # Documentação técnica e guia operacional do projeto
├── LICENSE                                    # Termos de licença de uso (GPL v3)
│
├── src/                                       # Diretório principal de desenvolvimento
│   ├── docker-compose.yml                     # Infraestrutura MySQL 8.0, MongoDB, phpMyAdmin e Mongo Express
│   ├── modelo_2025.mwb                        # Modelo EER relacional editável do MySQL Workbench
│   │
│   ├── img/                                   # Diagramas visuais exportados
│   │   └── eer_diagram.png                    # Imagem exportada do modelo relacional (DER / 3FN)
│   │
│   ├── raw/                                   # Diretório de dados brutos (ignorado no Git)
│   │   ├── despesas-2025.csv                  # CSV consolidado de despesas 2025 do TCE-PB
│   │   └── receitas-2025.csv                  # CSV consolidado de receitas 2025 do TCE-PB
│   │
│   ├── scripts/                               # Automação de banco de dados (SQL e NoSQL)
│   │   ├── sql/                               # Scripts SQL de engenharia e modelagem relacional
│   │   │   ├── Create_Equipe_5_2026.2.sql     # DDL: Definição de tabelas, PKs, FKs e restrições
│   │   │   ├── Insert_Equipe_5_2026.2.sql     # DML: Staging, carga, filtro semestral e 3FN
│   │   │   ├── Insert_Equipe_5_2026.2(local).sql # DML alternativo para execução local
│   │   │   └── modelo_2025.mwb                # Cópia do modelo relacional do Workbench
│   │   │
│   │   └── nosql/                             # Artefatos de modelagem e migração para MongoDB
│   │       ├── migracao_modelagem.relmig      # Projeto do MongoDB Relational Migrator
│   │       ├── credor_MongoDBSchema.json      # JSON Schema da coleção credor
│   │       └── despesa_MongoDBSchema.json     # JSON Schema da coleção despesa
│   │
│   └── python/                                # Análise exploratória preliminar
│       ├── consolidacao.ipynb                 # Notebook de inspeção e consolidação multianual
│       └── normalizacao.ipynb                 # Notebook com prototipagem inicial de normalização
│
└── zips/                                      # Arquivos compactados originais (opcional)
    ├── despesas-2025.zip                      # Download bruto de despesas do TCE-PB
    └── receitas-2025.zip                      # Download bruto de receitas do TCE-PB
```

### Organização e Papel das Pastas

| Diretório / Arquivo | Classificação | Descrição e Finalidade Técnica |
| :--- | :--- | :--- |
| **`/` (Raiz)** | Governança | Abriga a documentação principal ([`README.md`]), termos de licença ([`LICENSE`]) e configurações do repositório Git. |
| **`src/`** | Núcleo do Projeto | Diretório central que reúne infraestrutura conteinerizada, modelagem relacional, scripts de automação e cadernos de apoio. |
| **`src/docker-compose.yml`** | Infraestrutura | Manifesto Docker unificado contendo MySQL 8.0, MongoDB, phpMyAdmin e Mongo Express com volumes persistentes. |
| **`src/modelo_2025.mwb`** | Modelagem EER | Arquivo fonte editável do MySQL Workbench com o modelo relacional normalizado até a 3FN, chaves e restrições. |
| **`src/img/`** | Artefatos Visuais | Diagramas de entidade-relacionamento (DER/EER) exportados em alta resolução ([`eer_diagram.png`]) para documentação e relatórios. |
| **`src/raw/`** | *Data Lake / Ingestão* | Pasta destinada a receber os arquivos brutos extraídos do portal de dados abertos do TCE-PB (`despesas-2025.csv`). Arquivos ignorados pelo Git via `.gitignore` devido ao tamanho (>1.9 GB). |
| **`src/scripts/sql/`** | Engenharia Relacional | Contém os scripts SQL nativos: DDL ([`Create_Equipe_5_2026.2.sql`]), DML ([`Insert_Equipe_5_2026.2.sql`]) e modelo `.mwb`. |
| **`src/scripts/nosql/`** | Engenharia NoSQL | Artefatos da migração para MongoDB: projeto do MongoDB Relational Migrator ([`migracao_modelagem.relmig`]) e esquemas JSON de validação das coleções `despesa` e `credor`. |
| **`src/python/`** | *Data Science / EDA* | Cadernos Jupyter (`.ipynb`) utilizados na fase exploratória inicial de análise estatística, consolidação multianual e prototipagem dos tratamentos de dados. |
| **`zips/`** | Arquivos Compactados | Pasta de conveniência local para armazenamento dos arquivos compactados baixados diretamente do portal governamental. |
