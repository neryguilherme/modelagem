# 📊 Modelagem e Normalização de Dados de Despesas Públicas (TCE-PB 2025)

[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![phpMyAdmin](https://img.shields.io/badge/phpMyAdmin-Latest-6C78AF?style=for-the-badge&logo=phpmyadmin&logoColor=white)](https://www.phpmyadmin.net/)

Projeto de Engenharia e Modelagem de Dados desenvolvido para extrair, limpar, filtrar, normalizar (até a **3ª Forma Normal - 3FN**) e persistir os registros de despesas públicas do Estado da Paraíba referentes ao **1º Semestre de 2025**.

---

## 📌 Sumário
- [Origem dos Dados](#-origem-dos-dados)
- [Arquitetura de Infraestrutura (Docker)](#-arquitetura-de-infraestrutura-docker)
- [Pipeline de Normalização de Dados](#-pipeline-de-normalização-de-dados)
  - [1. Extração e Filtragem](#1-extração-e-filtragem)
  - [2. Processo de Normalização (1FN, 2FN e 3FN)](#2-processo-de-normalização-1fn-2fn-e-3fn)
  - [3. Dicionário de Tabelas e Entidades Geradas](#3-dicionário-de-tabelas-e-entidades-geradas)
- [Diagrama Entidade-Relacionamento (ERD)](#-diagrama-entidade-relacionamento-erd)
- [Como Executar o Projeto](#-como-executar-o-projeto)
  - [Pré-requisitos](#pré-requisitos)
  - [Passo a Passo](#passo-a-passo)
- [Estrutura de Diretórios](#-estrutura-de-diretórios)

---

## 🌐 Origem dos Dados

Os dados brutos utilizados neste projeto são de domínio público e foram obtidos através do portal de dados abertos do **Tribunal de Contas do Estado da Paraíba (TCE-PB)**:

* **Portal**: [Dados Abertos TCE-PB - Dados Consolidados](https://dados-abertos.tce.pb.gov.br/dados-consolidados)
* **Dataset**: Despesas consolidadas do exercício de **2025** (`despesas-2025.csv`).
* **Volume Original**: 2.387.532 linhas e 40 colunas (~1.95 GB).

---

## 🐳 Arquitetura de Infraestrutura (Docker)

O ambiente de banco de dados e interface gráfica foi totalmente conteinerizado utilizando **Docker Compose**, garantindo isolamento, reprodutibilidade e persistência de dados.

### Serviços Configurados

| Serviço | Imagem | Porta Host:Container | Descrição |
| :--- | :--- | :--- | :--- |
| **`db`** | `mysql:8.0` | `3307:3306` | Banco de Dados Relacional MySQL 8.0 |
| **`phpmyadmin`** | `phpmyadmin:latest` | `8080:80` | Interface Web para visualização e consulta dos dados |

### Credenciais de Conexão

* **Host**: `localhost` (ou `127.0.0.1`)
* **Porta MySQL**: `3307`
* **Banco de Dados**: `modelagem`
* **Usuário**: `usuario`
* **Senha**: `senhasegura`
* **Root Password**: `rootpassword`
* **URL phpMyAdmin**: [http://localhost:8080](http://localhost:8080)
* **Volume Persistente**: `mysql_data` montado em `/var/lib/mysql`

---

## ⚙️ Pipeline de Normalização de Dados

### 1. Extração e Filtragem

1. **Ingestão**: Carregamento do arquivo `src/raw/despesas-2025.csv` delimitado por ponto e vírgula (`;`).
2. **Filtragem Temporal (1º Semestre)**:
   - A base anual completa possui **2.387.532 registros**.
   - Foi aplicado um filtro baseado no campo `data_empenho` para restringir aos meses de janeiro a junho ($\le 6$).
   - **Resultado do recorte**: **1.068.148 linhas** e **40 colunas**.

---

### 2. Processo de Normalização (1FN, 2FN e 3FN)

A base bruta do TCE-PB é fornecida em formato tabular desnormalizado (tabela única e plana com 40 atributos), contendo redundâncias massivas, repetições de nomes de entidades e tipos de dados não padronizados.

A função `normalizar_empenhos()` implementa a separação dimensional respeitando rigorosamente as Formas Normais:

```
┌───────────────────────────────────────────────────────────────────┐
│                     Tabela Desnormalizada Raw                     │
│                    (1.068.148 linhas × 40 cols)                   │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │ 1FN: Limpeza, Tipagem Atômica e Tratamento       │
        │ - Limpeza de caracteres BOM (\ufeff)             │
        │ - Parsing de moedas (str -> float)               │
        │ - Conversão de data_empenho para datetime        │
        └─────────────────────────┬────────────────────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │ 2FN & 3FN: Decomposição em Entidades             │
        │ - Eliminação de Dependências Parciais e          │
        │   Transitivas                                    │
        │ - Extração de 13 Tabelas Dimensão                │
        │ - Criação da Tabela Fato (chaves estrangeiras)   │
        └─────────────────────────┬────────────────────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │ Carga em Lotes no MySQL (chunksize = 20.000)     │
        └──────────────────────────────────────────────────┘
```

#### 🔹 Primeira Forma Normal (1FN)
* **Atomicidade dos Dados**: Garantia de que cada campo contenha apenas valores indivisíveis.
* **Sanitização de Cabeçalhos**: Remoção de caracteres ocultos de codificação (*BOM* `\ufeff`) dos nomes das colunas.
* **Padronização e Cast Numérico**:
  - As colunas de valores financeiros (`valor_empenhado`, `valor_liquidado`, `valor_pago`) foram convertidas de texto em padrão brasileiro (`1.234,56`) para valores decimais de ponto flutuante (`float`), com tratamento de nulos (`fillna(0.0)`).
* **Padronização Temporal**:
  - Conversão da coluna `data_empenho` para o formato `datetime` nativo.

#### 🔹 Segunda Forma Normal (2FN)
* **Eliminação de Dependências Parciais**:
  - Em um empenho, atributos descritivos dependem de identificadores específicos e não de uma chave composta global.
  - Campos descritivos (ex: nome do credor, descrição da unidade gestora, nome da ação) foram desvinculados do registro transacional de despesa.

#### 🔹 Terceira Forma Normal (3FN)
* **Eliminação de Dependências Transitivas**:
  - Atributos não-chave que determinavam outros atributos não-chave foram isolados em tabelas próprias (ex: `codigo_funcao` $\rightarrow$ `funcao`, `codigo_subfuncao` $\rightarrow$ `subfuncao`, `cpf_cnpj` $\rightarrow$ `nome_credor`, `codigo_unidade_gestora` $\rightarrow$ `descricao_unidade_gestora`, `municipio`).
* **Estruturação Fato / Dimensão**:
  - Os valores descritivos textuais foram extraídos para **13 tabelas de dimensão** sem duplicatas (`drop_duplicates()`), mantendo apenas os identificadores numéricos e de negócio como **chaves estrangeiras (FK)** na tabela principal `fato_empenhos`.

---

### 3. Dicionário de Tabelas e Entidades Geradas

Após o processo de normalização dos dados do 1º semestre de 2025, foram geradas **14 tabelas**:

| Tabela | Tipo | Quantidade de Registros | Colunas / Atributos |
| :--- | :---: | :---: | :--- |
| **`fato_empenhos`** | **Fato** | **1.068.148** | `numero_empenho`, `data_empenho`, `mes`, `codigo_unidade_gestora`, `codigo_unidade_orcamentaria`, `cpf_cnpj`, `codigo_funcao`, `codigo_subfuncao`, `codigo_programa`, `codigo_acao`, `codigo_categoria_economica`, `codigo_natureza`, `codigo_modalidade_aplicacao`, `codigo_elemento_despesa`, `codigo_subelemento`, `codigo_subelemento_exibicao`, `codigo_fonte_recurso`, `co`, `numero_licitacao`, `modalidade_licitacao`, `numero_obra`, `valor_empenhado`, `valor_liquidado`, `valor_pago`, `historico`, `ano_fonte` |
| **`dim_credor`** | Dimensão | 168.771 | `cpf_cnpj` *(PK)*, `nome_credor` |
| **`dim_acao`** | Dimensão | 1.104 | `codigo_acao` *(PK)*, `acao` |
| **`dim_unidade_gestora`** | Dimensão | 622 | `codigo_unidade_gestora` *(PK)*, `descricao_unidade_gestora`, `municipio` |
| **`dim_unidade_orcamentaria`** | Dimensão | 519 | `codigo_unidade_orcamentaria` *(PK)*, `descricao_unidade_orcamentaria` |
| **`dim_programa`** | Dimensão | 513 | `codigo_programa` *(PK)*, `programa` |
| **`dim_subfuncao`** | Dimensão | 88 | `codigo_subfuncao` *(PK)*, `subfuncao` |
| **`dim_fonte_recurso`** | Dimensão | 64 | `codigo_fonte_recurso` *(PK)*, `descricao_fonte_recurso` |
| **`dim_elemento_despesa`** | Dimensão | 50 | `codigo_elemento_despesa` *(PK)*, `elemento_despesa` |
| **`dim_funcao`** | Dimensão | 26 | `codigo_funcao` *(PK)*, `funcao` |
| **`dim_co`** | Dimensão | 15 | `co` *(PK)*, `descricao_co` |
| **`dim_modalidade_aplicacao`** | Dimensão | 14 | `codigo_modalidade_aplicacao` *(PK)*, `modalidade_aplicacao` |
| **`dim_natureza`** | Dimensão | 6 | `codigo_natureza` *(PK)*, `grupo_natureza_despesa` |
| **`dim_categoria_economica`** | Dimensão | 2 | `codigo_categoria_economica` *(PK)*, `categoria_economica` |

---

## 📐 Diagrama Entidade-Relacionamento (ERD)

```mermaid
erDiagram
    fato_empenhos }o--|| dim_unidade_gestora : "codigo_unidade_gestora"
    fato_empenhos }o--|| dim_unidade_orcamentaria : "codigo_unidade_orcamentaria"
    fato_empenhos }o--|| dim_credor : "cpf_cnpj"
    fato_empenhos }o--|| dim_funcao : "codigo_funcao"
    fato_empenhos }o--|| dim_subfuncao : "codigo_subfuncao"
    fato_empenhos }o--|| dim_programa : "codigo_programa"
    fato_empenhos }o--|| dim_acao : "codigo_acao"
    fato_empenhos }o--|| dim_categoria_economica : "codigo_categoria_economica"
    fato_empenhos }o--|| dim_natureza : "codigo_natureza"
    fato_empenhos }o--|| dim_modalidade_aplicacao : "codigo_modalidade_aplicacao"
    fato_empenhos }o--|| dim_elemento_despesa : "codigo_elemento_despesa"
    fato_empenhos }o--|| dim_fonte_recurso : "codigo_fonte_recurso"
    fato_empenhos }o--o| dim_co : "co"

    fato_empenhos {
        bigint numero_empenho
        datetime data_empenho
        string mes
        double codigo_unidade_gestora FK
        bigint codigo_unidade_orcamentaria FK
        bigint cpf_cnpj FK
        bigint codigo_funcao FK
        bigint codigo_subfuncao FK
        bigint codigo_programa FK
        bigint codigo_acao FK
        bigint codigo_categoria_economica FK
        bigint codigo_natureza FK
        bigint codigo_modalidade_aplicacao FK
        bigint codigo_elemento_despesa FK
        bigint codigo_subelemento
        string codigo_subelemento_exibicao
        bigint codigo_fonte_recurso FK
        double co FK
        bigint numero_licitacao
        string modalidade_licitacao
        bigint numero_obra
        double valor_empenhado
        double valor_liquidado
        double valor_pago
        string historico
        bigint ano_fonte
    }

    dim_unidade_gestora {
        double codigo_unidade_gestora PK
        string descricao_unidade_gestora
        string municipio
    }

    dim_unidade_orcamentaria {
        bigint codigo_unidade_orcamentaria PK
        string descricao_unidade_orcamentaria
    }

    dim_credor {
        bigint cpf_cnpj PK
        string nome_credor
    }

    dim_funcao {
        bigint codigo_funcao PK
        string funcao
    }

    dim_subfuncao {
        bigint codigo_subfuncao PK
        string subfuncao
    }

    dim_programa {
        bigint codigo_programa PK
        string programa
    }

    dim_acao {
        bigint codigo_acao PK
        string acao
    }

    dim_categoria_economica {
        bigint codigo_categoria_economica PK
        string categoria_economica
    }

    dim_natureza {
        bigint codigo_natureza PK
        string grupo_natureza_despesa
    }

    dim_modalidade_aplicacao {
        bigint codigo_modalidade_aplicacao PK
        string modalidade_aplicacao
    }

    dim_elemento_despesa {
        bigint codigo_elemento_despesa PK
        string elemento_despesa
    }

    dim_fonte_recurso {
        bigint codigo_fonte_recurso PK
        string descricao_fonte_recurso
    }

    dim_co {
        double co PK
        string descricao_co
    }
```

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução.
* [Python 3.10+](https://www.python.org/) com suporte a Jupyter Notebook.

### Passo a Passo

#### 1. Clonar o Repositório
```bash
git clone https://github.com/neryguilherme/modelagem.git
cd modelagem
```

#### 2. Iniciar os Containers (MySQL e phpMyAdmin)
Navegue até a pasta `src` e suba os serviços via Docker Compose:
```bash
cd src
docker compose up -d
```
Verifique se os containers `mysql_modelagem` e `phpmyadmin_modelagem` estão saudáveis (`Up`):
```bash
docker compose ps
```

#### 3. Configurar o Ambiente Python
Crie e ative um ambiente virtual (opcional, caso não use o existente) e instale as dependências:
```bash
pip install pandas numpy pyarrow duckdb sqlalchemy pymysql jupyter
```

#### 4. Executar o Pipeline de Normalização
1. Abra o Jupyter Notebook:
   ```bash
   jupyter notebook normalizacao.ipynb
   ```
2. Execute as células do notebook em sequência:
   - Carregamento da base bruta `raw/despesas-2025.csv`.
   - Filtragem dos dados do **1º semestre de 2025**.
   - Criação da conexão com o banco MySQL (`mysql+pymysql://usuario:senhasegura@localhost:3307/modelagem`).
   - Execução da função `normalizar_empenhos()`.
   - Carga das 14 tabelas no MySQL em chunks (`chunksize=20000`).

#### 5. Visualizar no phpMyAdmin
1. Acesse no navegador: [http://localhost:8080](http://localhost:8080)
2. Informe as credenciais:
   - **Servidor**: `db`
   - **Usuário**: `usuario`
   - **Senha**: `senhasegura`
3. Selecione o banco de dados `modelagem` para visualizar a tabela fato e as tabelas dimensão criadas.

---

## 📂 Estrutura de Diretórios

```plaintext
modelagem/
│
├── README.md                      # Documentação técnica do projeto
├── LICENSE                        # Licença de uso
│
└── src/
    ├── docker-compose.yml         # Configuração dos containers MySQL 8.0 e phpMyAdmin
    ├── normalizacao.ipynb         # Notebook com pipeline de ETL, normalização (3FN) e carga
    │
    └── raw/
        ├── despesas-2025.csv      # Base bruta de despesas de 2025 (TCE-PB)
        └── receitas-2025.csv      # Base bruta de receitas de 2025 (TCE-PB)
```