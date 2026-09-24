# 📊 Modelagem e Engenharia de Banco de Dados Relacional (OLTP / 3FN) e NoSQL (MongoDB): Despesas Públicas (TCE-PB 2025)

[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Latest-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Relational Migrator](https://img.shields.io/badge/MongoDB-Relational_Migrator-00684A?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/products/tools/relational-migrator)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![phpMyAdmin](https://img.shields.io/badge/phpMyAdmin-Latest-6C78AF?style=for-the-badge&logo=phpmyadmin&logoColor=white)](https://www.phpmyadmin.net/)
[![Mongo Express](https://img.shields.io/badge/Mongo_Express-Latest-13AA52?style=for-the-badge&logo=mongodb&logoColor=white)](https://github.com/mongo-express/mongo-express)
[![Workbench](https://img.shields.io/badge/MySQL_Workbench-8.0-00758F?style=for-the-badge&logo=mysql&logoColor=white)](https://dev.mysql.com/downloads/workbench/)
[![Modelo](https://img.shields.io/badge/Arquitetura-OLTP_%7C_3FN_%26_NoSQL-success?style=for-the-badge)](https://en.wikipedia.org/wiki/Third_normal_form)

Projeto acadêmico de modelagem e engenharia de banco de dados relacional transacional (**OLTP**), estritamente normalizado até a **3ª Forma Normal (3FN)**, e sua respectiva transposição para banco de dados orientado a documentos (**NoSQL / MongoDB**), desenvolvido a partir dos microdados públicos de execução orçamentária do **Tribunal de Contas do Estado da Paraíba (TCE-PB)** para o **1º Semestre de 2025**.

O projeto estrutura o ciclo de vida da execução da despesa pública (**Empenho**, **Liquidação** e **Pagamento**) em torno de uma entidade transacional central (`despesa`), decomposta em 12 tabelas de domínio e localidade no modelo relacional, com tolerância zero a valores nulos em chaves através de **Registros Sentinelas**. No ambiente NoSQL (MongoDB), os dados são espelhados em 13 coleções através do **MongoDB Relational Migrator**.

> [!TIP]
> **Execução Local (MySQL 3306 & Workbench)**: Se você deseja rodar este projeto em uma instalação local do MySQL Server sem Docker, consulte o nosso guia dedicado:  
> 📘 [**`EXECUCAO_LOCAL.md` — Guia de Execução Local no MySQL Workbench**](file:///c:/Users/eu/Documents/GitHub/modelagem/EXECUCAO_LOCAL.md)

---

## 📌 Sumário

- [Origem dos Dados e Recorte Temporal](#-origem-dos-dados-e-recorte-temporal)
- [Ciclo da Despesa Orçamentária e Arquitetura Relacional](#️-ciclo-da-despesa-orçamentária-e-arquitetura-relacional)
- [Diagrama Entidade-Relacionamento (EER)](#-diagrama-entidade-relacionamento-eer)
- [Dicionário de Tabelas e Entidades](#-dicionário-de-tabelas-e-entidades)
- [Justificativas de Chaves Primárias](#-justificativas-de-chaves-primárias)
  - [Por que `numero_licitacao` não é a Chave Primária (PK)?](#por-que-numero_licitacao-não-é-a-chave-primária-pk)
- [Colunas Descartadas e Justificativas de Modelagem](#-colunas-descartadas-e-justificativas-de-modelagem)
- [Tratamento Documental: Preservação de CPF e CNPJ (VARCHAR)](#-tratamento-documental-preservação-de-cpf-e-cnpj-varchar)
- [Tratamento de Nulidade Estrita: Registros Sentinelas em Chaves Estrangeiras](#️-tratamento-de-nulidade-estrita-registros-sentinelas-em-chaves-estrangeiras)
- [Arquitetura de Infraestrutura (Docker)](#-arquitetura-de-infraestrutura-docker)
- [Pipeline de Carga e Normalização via SQL](#-pipeline-de-carga-e-normalização-via-sql)
- [Guia de Execução Passo a Passo (Ambiente Docker)](#-guia-de-execução-passo-a-passo-ambiente-docker)
  - [1. Pré-requisitos](#1-pré-requisitos)
  - [2. Download da Base Bruta](#2-download-da-base-bruta)
  - [3. Iniciar os Serviços Docker](#3-iniciar-os-serviços-docker)
  - [4. Copiar o CSV para a Pasta Segura do MySQL](#4-copiar-o-csv-para-a-pasta-segura-do-mysql)
  - [5. Executar os Scripts de Criação e Carga](#5-executar-os-scripts-de-criação-e-carga)
  - [6. Validação e Auditoria dos Dados](#6-validação-e-auditoria-dos-dados)
- [Modelagem NoSQL e Migração para MongoDB](#-modelagem-nosql-e-migração-para-mongodb)
  - [Diagrama da Arquitetura Orientada a Documentos](#diagrama-da-arquitetura-orientada-a-documentos)
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

Em substituição a modelos analíticos baseados em *Star Schema* (`fato_` e `dim_`), o banco de dados foi estruturado estritamente sob as regras da **3ª Forma Normal (3FN)**:

* **Entidade Central `despesa`**: Consolida os atributos transacionais e os valores monetários das três fases do gasto (`valor_empenhado`, `valor_liquidado`, `valor_pago` tipados em `DECIMAL(15,2)`), associando-se às respectivas entidades de domínio através de 10 Chaves Estrangeiras estritas (`FOREIGN KEY NOT NULL`).
* **Eliminação de Dependências Transitivas em Localidades**: Criação da tabela `municipio`, associando-se hierarquicamente à `unidade_gestora` (`unidade_gestora.id_municipio` $\rightarrow$ `municipio.id_municipio`).
* **Desacoplamento de Domínios**: Processos licitatórios (`licitacao`), credores (`credor`) e classificadores orçamentários (LOA/STN) isolados em tabelas próprias.

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
        int codigo_unidade_gestora FK "NOT NULL"
        varchar cpf_cnpj FK "NOT NULL"
        int id_licitacao FK "NOT NULL DEFAULT 1"
        int codigo_funcao FK "NOT NULL"
        int codigo_programa FK "NOT NULL"
        varchar codigo_acao FK "NOT NULL"
        int codigo_categoria_economica FK "NOT NULL"
        int codigo_natureza FK "NOT NULL"
        int codigo_modalidade_aplicacao FK "NOT NULL"
        int codigo_elemento_despesa FK "NOT NULL"
        int codigo_fonte_recurso FK "NOT NULL"
    }
```

O modelo relacional conceitual/lógico original está armazenado em:
📁 [`scripts/modelo_2025_gp5.mwb`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/modelo_2025_gp5.mwb).  
O diagrama visual exportado em alta resolução está disponível em:
🖼️ [`img/eer_diagram.png`](file:///c:/Users/eu/Documents/GitHub/modelagem/img/eer_diagram.png).

---

## 📋 Dicionário de Tabelas e Entidades

O banco de dados físico implementado consolida **13 tabelas relacionais**:

| Tabela | Tipo | Chave Primária (PK) | Chaves Estrangeiras (FK) | Descrição do Domínio |
| :--- | :--- | :--- | :--- | :--- |
| **`despesa`** | Central / Transacional | `id` (`INT AI`) | 10 FKs associadas (`NOT NULL`) | Execução orçamentária contendo número do empenho, data, mês, histórico e os valores empenhado, liquidado e pago. |
| **`municipio`** | Domínio / Localidade | `id_municipio` (`INT AI`) | Nenhuma | Municípios do Estado da Paraíba responsáveis pelas administrações públicas. |
| **`unidade_gestora`** | Entidade Administrativa | `codigo_unidade_gestora` (`INT`) | `id_municipio` | Órgãos executores da despesa (prefeituras, câmaras, fundos municipais). |
| **`credor`** | Agente Econômico | `cpf_cnpj` (`VARCHAR(255)`) | Nenhuma | Fornecedores, servidores e prestadores de serviços recebedores dos pagamentos. |
| **`licitacao`** | Processo Administrativo | `id_licitacao` (`INT AI`) | Nenhuma | Identificação do processo licitatório, número do certame e modalidade contratual. |
| **`funcao`** | Classificador Orçamentário | `codigo_funcao` (`INT`) | Nenhuma | Maior nível de agregação das áreas de atuação do setor público (ex: Saúde, Educação). |
| **`programa`** | Planejamento Orçamentário | `codigo_programa` (`INT`) | Nenhuma | Programas governamentais estabelecidos no Plano Plurianual (PPA). |
| **`acao`** | Instrumento de Despesa | `codigo_acao` (`VARCHAR(20)`) | Nenhuma | Projetos, atividades ou operações especiais com finalidade específica. |
| **`categoria_economica`** | Contabilidade Pública | `codigo_categoria_economica` (`INT`) | Nenhuma | Despesas Correntes (3) ou Despesas de Capital (4). |
| **`natureza_despesa`** | Contabilidade Pública | `codigo_natureza` (`INT`) | Nenhuma | Grupo de Natureza da Despesa (GND): Pessoal, Juros, Investimentos, etc. |
| **`modalidade_aplicacao`** | Contabilidade Pública | `codigo_modalidade_aplicacao` (`INT`) | Nenhuma | Especificação da destinação direta ou transferências intergovernamentais. |
| **`elemento_despesa`** | Contabilidade Pública | `codigo_elemento_despesa` (`INT`) | Nenhuma | Desdobramento específico do gasto (vencimentos, serviços de terceiros, diárias). |
| **`fonte_recurso`** | Financiamento Público | `codigo_fonte_recurso` (`INT`) | Nenhuma | Mecanismo financeiro e origem orçamentária que custeia a despesa. |

---

## 🔑 Justificativas de Chaves Primárias

### Por que `numero_licitacao` não é a Chave Primária (PK)?

Adotou-se a Surrogate Key sintética `id_licitacao (INT AUTO_INCREMENT)` em substituição ao atributo de negócio `numero_licitacao` devido aos seguintes fatores determinantes:

1. **Falta de Unicidade (Colisão de Números)**: A numeração de licitações é anual e municipal, e não de controle estadual unificado. No 1º semestre de 2025, existem dezenas de licitações com o número idêntico `"00001/2025"` ocorrendo simultaneamente em municípios diferentes (João Pessoa, Campina Grande, Patos, etc.). Exigir unicidade nessa coluna inviabilizaria inserções legítimas por erro de chave duplicada.
2. **Presença Massiva de Nulos**: Na base bruta do TCE-PB, centenas de milhares de linhas possuem o campo de licitação vazio/nulo (despesas diretas, diárias, folhas de pagamento). Por definição matemática e relacional, uma Chave Primária jamais pode conter valores nulos.
3. **Formatação Suja e Inconsistente**: Municípios registram o certame com variações livres de máscara (`"001/2025"`, `"PE 01/25"`, `"DISP 12"`), o que degradaria a ordenação e a consistência da indexação.
4. **Desempenho dos Índices e Chaves Estrangeiras**: Apontar na tabela `despesa` (com mais de 1 milhão de registros) uma FK numérica inteira (`INT`) consome apenas **4 bytes** por linha; propagar um `VARCHAR(50)` exigiria mais de **50 MB adicionais** de memória RAM e disco apenas para a coluna de relacionamento.

---

## 🗑️ Colunas Descartadas e Justificativas de Modelagem

A base de dados bruta original continha 40 colunas desnormalizadas. No processo de engenharia reversa e reestruturação para a 3FN, **12 colunas foram descartadas** com base em critérios técnicos e diretrizes de normalização:

| Coluna Bruta Original | Destino no Projeto | Justificativa Técnica e de Modelagem |
| :--- | :---: | :--- |
| **`numero_obra`** | Descartada da tabela `licitacao` | **Altíssima dispersão de nulos**: Presente com valores nulos/vazios em **mais de 96% das linhas** da base bruta do TCE-PB, sendo irrelevante na execução orçamentária corrente geral. |
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

## 🛡️ Tratamento de Nulidade Estrita: Registros Sentinelas em Chaves Estrangeiras

Para atender à diretriz de **tolerância zero a campos `NULL` em relacionamentos transacionais**, todas as 12 tabelas de domínio adotam a estratégia de **Registros Sentinelas** (IDs `0` ou `1` com o valor `'Não Informado'` ou `'Sem Licitação'`).

Dessa forma, a tabela central `despesa` garante integridade referencial estrita (**`NOT NULL` em todas as 10 Chaves Estrangeiras**), permitindo operações analíticas exclusivamente com **`INNER JOIN`** sem risco de descarte involuntário de transações.

| **Tabela de Domínio** | **Chave do Sentinela** | **Descrição Cadastrada** | **Finalidade de Negócio** |
| :--- | :--- | :--- | :--- |
| **`licitacao`** | `id_licitacao = 1` | `'Sem Licitação'` / `'Sem Licitação'` | Atende despesas diretas, diárias, folhas de pagamento e adiantamentos. |
| **`municipio`** | `id_municipio = 1` | `'Não Informado'` | Para órgãos estaduais sem sede municipal declarada. |
| **`unidade_gestora`** | `codigo = 0` | `'Não Informado'` (vinculada ao município 1) | Registros de órgãos sem código válido no empenho. |
| **`credor`** | `cpf_cnpj = '0'` | `'Não Informado'` | Despesas com favorecido não declarado na origem. |
| **`funcao`** | `codigo = 0` | `'Não Informado'` | Empenhos sem enquadramento funcional. |
| **`programa`** | `codigo = 0` | `'Não Informado'` | Empenhos sem programa de governo especificado. |
| **`acao`** | `codigo = '0'` | `'Não Informado'` | Empenhos sem ação orçamentária associada. |
| **`categoria_economica`** | `codigo = 0` | `'Não Informado'` | Casos sem classificação de despesa corrente/capital. |
| **`natureza_despesa`** | `codigo = 0` | `'Não Informado'` | Falta de grupo de natureza de despesa (GND). |
| **`modalidade_aplicacao`** | `codigo = 0` | `'Não Informado'` | Falta de modalidade de aplicação orçamentária. |
| **`elemento_despesa`** | `codigo = 0` | `'Não Informado'` | Falta de discriminação do item de gasto. |
| **`fonte_recurso`** | `codigo = 0` | `'Não Informado'` | Despesas sem especificação de fonte de financiamento. |

### Mitigação de Inconsistências de Tipagem no Script DML

| Situação Encontrada | Causa Raiz na Origem | Tratamento Aplicado no Script SQL (`Insert_Equipe_5_2026.2.sql`) |
| :--- | :--- | :--- |
| **Inconsistência de Datas** | Alternância de formatos `YYYY-MM-DD` e `DD/MM/YYYY` no CSV | `COALESCE(STR_TO_DATE(LEFT(data, 10), '%Y-%m-%d'), STR_TO_DATE(LEFT(data, 10), '%d/%m/%Y'), '2025-01-01')` |
| **Valores Financeiros Formatados** | Formato de moeda brasileiro (`1.250,50` com pontuação de milhar) | `COALESCE(CAST(REPLACE(REPLACE(val, '.', ''), ',', '.') AS DECIMAL(15,2)), 0.00)` |
| **Despesas sem Licitação** | Despesas diretas e dispensas | Registro Sentinela `id_licitacao = 1` associado via `COALESCE(l.id_licitacao, 1)` |
| **Deslocamento de Colunas** | Registros brutos com código 0 ou vazamentos textuais | Cláusula `WHERE CAST(codigo AS SIGNED) > 0`, garantindo apenas códigos legítimos |
| **Mês Transacional Nulo** | Omissão eventual do identificador de mês | `COALESCE(NULLIF(t.mes, ''), 'Não Informado')` garantindo `NOT NULL` |

---

## 🐳 Arquitetura de Infraestrutura (Docker)

O ambiente completo de bancos de dados relacionais e NoSQL, bem como suas respectivas interfaces de gestão gráfica, é provisionado via **Docker Compose** integrado na mesma rede interna ([`docker-compose.yml`](file:///c:/Users/eu/Documents/GitHub/modelagem/docker-compose.yml)):

```yaml
services:
  # SGBD Relacional
  db:
    image: mysql:8.0
    container_name: mysql_modelagem
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: modelagem
      MYSQL_USER: usuario
      MYSQL_PASSWORD: senhasegura
    ports:
      - "3307:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  # Interface Web MySQL
  phpmyadmin:
    image: phpmyadmin:latest
    container_name: phpmyadmin_modelagem
    restart: always
    ports:
      - "8080:80"
    environment:
      PMA_HOST: db
      PMA_PORT: 3306

  # SGBD NoSQL
  mongodb:
    image: mongo:latest
    container_name: mongodb_modelagem
    restart: always
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: rootpassword
    volumes:
      - mongo_data:/data/db

  # Interface Web MongoDB
  mongo-express:
    image: mongo-express:latest
    container_name: mongo_express_modelagem
    restart: always
    ports:
      - "8081:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: root
      ME_CONFIG_MONGODB_ADMINPASSWORD: rootpassword
      ME_CONFIG_MONGODB_URL: mongodb://root:rootpassword@mongodb:27017/
      ME_CONFIG_BASICAUTH: "false"

volumes:
  mysql_data:
    driver: local
  mongo_data:
    driver: local
```

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
│  - Registros sentinelas (cód 0 e 1)  │   │ - Vincula 10 FKs NOT NULL    │
└──────────────────────────────────────┘   └──────────────────────────────┘
                                                          │
                                                          ▼  DROP TABLE
                                           ┌──────────────────────────────┐
                                           │ Limpeza da Tabela de Staging │
                                           │ Restauração de Checks e FKs  │
                                           └──────────────────────────────┘
```

1. **[`scripts/Create_Equipe_5_2026.2.sql`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/Create_Equipe_5_2026.2.sql) (DDL)**:
   - Cria o schema `modelagem` com charset `utf8mb4`.
   - Cria as 13 tabelas relacionais, chaves primárias, chaves estrangeiras com restrições de integridade referencial estrita (`NOT NULL`) e índices secundários de consulta (`INDEX`).

2. **[`scripts/Insert_Equipe_5_2026.2.sql`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/Insert_Equipe_5_2026.2.sql) (DML Docker)**:
   - Criação da staging table `temp_despesas`.
   - Ingestão massiva em alta velocidade via `LOAD DATA INFILE` do caminho `/var/lib/mysql-files/despesas-2025.csv`.
   - Recorte analítico do 1º semestre via `DELETE FROM temp_despesas WHERE CAST(LEFT(mes, 2) AS SIGNED) > 6`.
   - Inserção dos registros sentinelas e povoamento idempotente das 12 tabelas de domínio.
   - Povoamento da tabela central `despesa` com casts monetários e integridade de chaves `NOT NULL`.
   - Descarte automático da staging table (`DROP TABLE temp_despesas`) e restauração das restrições.

3. **[`scripts/Insert_Equipe_5_2026.2(local).sql`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/Insert_Equipe_5_2026.2(local).sql) (DML Local)**:
   - Versão espelho otimizada para execução direta no MySQL Server nativo/Workbench (Porta 3306), conforme detalhado no [**`EXECUCAO_LOCAL.md`**](file:///c:/Users/eu/Documents/GitHub/modelagem/EXECUCAO_LOCAL.md).

---

## 🚀 Guia de Execução Passo a Passo (Ambiente Docker)

### 1. Pré-requisitos

* [Docker Desktop](https://www.docker.com/) instalado e em execução.
* [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) (opcional, para visualização de diagrama).

### 2. Download da Base Bruta

1. Acesse o portal: [TCE-PB Dados Abertos - Consolidados](https://dados-abertos.tce.pb.gov.br/dados-consolidados).
2. Na seção **Despesas**, baixe o pacote do exercício de **2025**.
3. Extraia o CSV para a pasta `raw/` com o nome exato:
   ```plaintext
   raw/despesas-2025.csv
   ```

### 3. Iniciar os Serviços Docker

Na raiz do repositório, suba os containers via Docker Compose:

```bash
docker compose up -d
```

Verifique o status dos serviços:
```bash
docker compose ps
```

### 4. Copiar o CSV para a Pasta Segura do MySQL

O MySQL restringe cargas locais fora do caminho seguro (`secure-file-priv`). Transfira o arquivo para o container:

```bash
docker cp raw/despesas-2025.csv mysql_modelagem:/var/lib/mysql-files/despesas-2025.csv
```

### 5. Executar os Scripts de Criação e Carga

Execute os comandos a partir da raiz do repositório:

#### 🪟 Windows (PowerShell):

```powershell
# 1. Criação do Banco de Dados e Tabelas (DDL)
Get-Content scripts/Create_Equipe_5_2026.2.sql | docker exec -i mysql_modelagem mysql -uroot -prootpassword modelagem

# 2. Carga, Filtro do 1º Semestre e Normalização Relacional (DML)
Get-Content scripts/Insert_Equipe_5_2026.2.sql | docker exec -i mysql_modelagem mysql -uroot -prootpassword modelagem
```

#### 🐧 Linux / macOS (Bash) ou Prompt de Comando (CMD):

```bash
# 1. Criação do Banco de Dados e Tabelas (DDL)
docker exec -i mysql_modelagem mysql -uroot -prootpassword modelagem < scripts/Create_Equipe_5_2026.2.sql

# 2. Carga, Filtro do 1º Semestre e Normalização Relacional (DML)
docker exec -i mysql_modelagem mysql -uroot -prootpassword modelagem < scripts/Insert_Equipe_5_2026.2.sql
```

### 6. Validação e Auditoria dos Dados

Abra o phpMyAdmin em [http://localhost:8080](http://localhost:8080) ou conecte o Workbench na porta `3307` e execute a verificação contábil:

```sql
USE `modelagem`;

-- 1. Total consolidado da tabela despesa (esperado: exatamente 1.068.148 linhas no 1º semestre)
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
    d.valor_empenhado,
    d.valor_liquidado,
    d.valor_pago
FROM despesa d
INNER JOIN unidade_gestora ug ON d.codigo_unidade_gestora = ug.codigo_unidade_gestora
INNER JOIN municipio m ON ug.id_municipio = m.id_municipio
INNER JOIN credor c ON d.cpf_cnpj = c.cpf_cnpj
INNER JOIN licitacao l ON d.id_licitacao = l.id_licitacao
ORDER BY d.data_empenho DESC
LIMIT 10;
```

---

## 🍃 Modelagem NoSQL e Migração para MongoDB

A migração do modelo relacional normalizado (OLTP / 3FN) para o banco de dados orientado a documentos (**MongoDB**) foi concebida para preservar a **mesma arquitetura modular relacional**, mapeando diretamente cada uma das 13 tabelas para **13 coleções BSON independentes** no banco `modelagem`.

Essa abordagem assegura total rastreabilidade fiscal, isolamento de domínios cadastrais e viabiliza operações relacionais e analíticas nativas no MongoDB através de pipelines de agregação com `$lookup`.

### Diagrama da Arquitetura Orientada a Documentos

```mermaid
graph TD
    subgraph "MongoDB: Database modelagem (13 Coleções)"
        direction TB
        despesa["Coleção: despesa (Central Transacional)"]
        
        municipio["Coleção: municipio"]
        unidade_gestora["Coleção: unidade_gestora"]
        credor["Coleção: credor"]
        licitacao["Coleção: licitacao"]
        funcao["Coleção: funcao"]
        programa["Coleção: programa"]
        acao["Coleção: acao"]
        categoria_economica["Coleção: categoria_economica"]
        natureza_despesa["Coleção: natureza_despesa"]
        modalidade_aplicacao["Coleção: modalidade_aplicacao"]
        elemento_despesa["Coleção: elemento_despesa"]
        fonte_recurso["Coleção: fonte_recurso"]
        
        municipio -->|"id_municipio"| unidade_gestora
        unidade_gestora -->|"codigo_unidade_gestora"| despesa
        credor -->|"cpf_cnpj"| despesa
        licitacao -->|"id_licitacao"| despesa
        funcao -->|"codigo_funcao"| despesa
        programa -->|"codigo_programa"| despesa
        acao -->|"codigo_acao"| despesa
        categoria_economica -->|"codigo_categoria_economica"| despesa
        natureza_despesa -->|"codigo_natureza"| despesa
        modalidade_aplicacao -->|"codigo_modalidade_aplicacao"| despesa
        elemento_despesa -->|"codigo_elemento_despesa"| despesa
        fonte_recurso -->|"codigo_fonte_recurso"| despesa
    end
```

---

### 🚀 Guia de Migração e Carga no MongoDB via Relational Migrator

Siga os passos abaixo para realizar a migração completa do MySQL para o MongoDB utilizando o [**MongoDB Relational Migrator**](https://www.mongodb.com/products/tools/relational-migrator):

#### Passo 1: Inicializar o Ambiente Docker
Certifique-se de que os serviços MySQL e MongoDB estão rodando:
```bash
docker compose up -d
docker compose ps
```

#### Passo 2: Criar/Importar o Projeto no MongoDB Relational Migrator
1. Abra o aplicativo desktop oficial **MongoDB Relational Migrator**.
2. Conecte-se ao banco de dados relacional de **Origem (Source - MySQL)**:
   * **Host**: `localhost` | **Porta**: `3307`
   * **Usuário**: `root` | **Senha**: `rootpassword`
   * **Database**: `modelagem`
3. O Migrator detectará automaticamente as 13 tabelas relacionais do banco.
4. Para a modelagem de destino, selecione o mapeamento **1:1 (Table to Collection)** para que cada uma das 13 tabelas seja transposta para uma coleção correspondente no MongoDB com o mesmo nome (`despesa`, `credor`, `licitacao`, `unidade_gestora`, etc.).

#### Passo 3: Conectar ao Banco de Dados de Destino (Target - MongoDB)
Configure o nó de conexão do MongoDB:
* **Connection String**: `mongodb://root:rootpassword@localhost:27017/modelagem?authSource=admin`

#### Passo 4: Executar a Migração
1. Acesse a aba **Data Migration** no menu superior do Migrator.
2. Crie um novo job no modo **Snapshot** (Carga em lote completa).
3. Selecione todas as 13 coleções mapeadas para migração.
4. Clique em **Start** e acompanhe o progresso em tempo real até a conclusão.

#### Passo 5: Validação dos Dados no MongoDB
Acesse o painel **Mongo Express** em [http://localhost:8081](http://localhost:8081) ou conecte-se via **MongoDB Compass** / **mongosh** na porta `27017`:

```javascript
use modelagem;

// 1. Total consolidado de documentos na coleção central despesa
db.despesa.countDocuments(); // Esperado: 1.068.148

// 2. Total de documentos na coleção credor
db.credor.countDocuments();  // Esperado: 168.771

// 3. Consulta analítica via pipeline com $lookup (equivalente ao INNER JOIN relacional)
db.despesa.aggregate([
  { $match: { numeroEmpenho: { $gt: 0 } } },
  {
    $lookup: {
      from: "credor",
      localField: "cpf_cnpj",
      foreignField: "cpf_cnpj",
      as: "dados_credor"
    }
  },
  {
    $lookup: {
      from: "unidade_gestora",
      localField: "codigo_unidade_gestora",
      foreignField: "codigo_unidade_gestora",
      as: "dados_ug"
    }
  },
  { $limit: 5 }
]);
```

---

## 📂 Estrutura do Repositório

### Visão em Árvore

```plaintext
modelagem/
├── README.md                                  # Documentação técnica e guia operacional do projeto
├── EXECUCAO_LOCAL.md                          # Guia passo a passo para execução no MySQL Server nativo / Workbench
├── LICENSE                                    # Termos de licença de uso (GPL v3)
├── docker-compose.yml                         # Infraestrutura MySQL 8.0, MongoDB, phpMyAdmin e Mongo Express
│
├── img/                                       # Diagramas visuais exportados
│   └── eer_diagram.png                        # Imagem exportada do modelo relacional (DER / 3FN)
│
├── raw/                                       # Diretório de dados brutos (ignorado no Git)
│   ├── despesas-2025.csv                      # CSV consolidado de despesas 2025 do TCE-PB
│   └── receitas-2025.csv                      # CSV consolidado de receitas 2025 do TCE-PB
│
├── scripts/                                   # Scripts SQL de automação e engenharia de dados
│   ├── Create_Equipe_5_2026.2.sql             # DDL: Definição de tabelas, PKs, 10 FKs NOT NULL e índices
│   ├── Insert_Equipe_5_2026.2.sql             # DML Docker: Carga do /var/lib/mysql-files/ e 3FN
│   ├── Insert_Equipe_5_2026.2(local).sql      # DML Local: Carga do diretório seguro local Uploads
│   └── modelo_2025_gp5.mwb                    # Modelo EER relacional editável do MySQL Workbench
│
└── zips/                                      # Arquivos compactados originais (opcional)
    ├── despesas-2025.zip                      # Download bruto de despesas do TCE-PB
    └── receitas-2025.zip                      # Download bruto de receitas do TCE-PB
```

### Organização e Papel das Pastas

| Diretório / Arquivo | Classificação | Descrição e Finalidade Técnica |
| :--- | :--- | :--- |
| **`README.md`** | Governança | Documentação principal com especificações arquiteturais, modelo conceitual, justificativas e guias Docker/NoSQL. |
| **`EXECUCAO_LOCAL.md`** | Guia Operacional | Manual prático para execução no MySQL Server bare-metal (porta 3306), Workbench e Google Drive. |
| **`docker-compose.yml`** | Infraestrutura | Manifesto Docker unificado contendo MySQL 8.0, MongoDB, phpMyAdmin e Mongo Express com volumes persistentes. |
| **`img/`** | Artefatos Visuais | Diagramas de entidade-relacionamento (DER/EER) exportados em alta resolução ([`eer_diagram.png`](file:///c:/Users/eu/Documents/GitHub/modelagem/img/eer_diagram.png)) para documentação e relatórios. |
| **`raw/`** | *Data Lake / Ingestão* | Pasta destinada a receber os arquivos brutos extraídos do portal de dados abertos do TCE-PB (`despesas-2025.csv`). Arquivos ignorados pelo Git via `.gitignore` devido ao tamanho (>1.9 GB). |
| **`scripts/`** | Engenharia SQL | **Coração do banco de dados**: contém scripts SQL nativos divididos em DDL ([`Create_Equipe_5_2026.2.sql`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/Create_Equipe_5_2026.2.sql)), DML Docker ([`Insert_Equipe_5_2026.2.sql`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/Insert_Equipe_5_2026.2.sql)), DML Local ([`Insert_Equipe_5_2026.2(local).sql`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/Insert_Equipe_5_2026.2(local).sql)) e o modelo Workbench ([`modelo_2025_gp5.mwb`](file:///c:/Users/eu/Documents/GitHub/modelagem/scripts/modelo_2025_gp5.mwb)). |
| **`zips/`** | Arquivos Compactados | Pasta de conveniência local para armazenamento dos arquivos compactados baixados diretamente do portal governamental. |
