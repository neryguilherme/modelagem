import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ==============================================================================
# 1. CONFIGURAÇÃO DE AMBIENTE E PÁGINA
# ==============================================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "dw_despesas")

st.set_page_config(
    page_title="Dashboard OLAP | DW Despesas Públicas TCE-PB 2025",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(28, 131, 225, 0.06);
        border: 1px solid rgba(28, 131, 225, 0.18);
        padding: 12px 16px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# 2. CONEXÃO COM O BANCO DE DADOS E UTILITÁRIOS DE FORMATAÇÃO
# ==============================================================================
@st.cache_resource
def get_engine():
    conn_url = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )
    return create_engine(conn_url, pool_pre_ping=True, pool_recycle=3600)


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def fmt_brl(val: float | int | None) -> str:
    if val is None or pd.isna(val):
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_brl_compact(val: float | int | None) -> str:
    if val is None or pd.isna(val):
        return "R$ 0"
    abs_val = abs(val)
    if abs_val >= 1_000_000_000:
        return f"R$ {val / 1_000_000_000:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs_val >= 1_000_000:
        return f"R$ {val / 1_000_000:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs_val >= 1_000:
        return f"R$ {val / 1_000:,.1f} mil".replace(",", "X").replace(".", ",").replace("X", ".")
    return fmt_brl(val)


def fmt_int(val: float | int | None) -> str:
    if val is None or pd.isna(val):
        return "0"
    return f"{int(val):,}".replace(",", ".")


def fmt_pct(val: float | int | None) -> str:
    if val is None or pd.isna(val):
        return "0,00%"
    return f"{val:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


# ==============================================================================
# 3. CARREGAMENTO DAS DIMENSÕES E CONSTRUTOR DE JOINS OTIMIZADOS (STAR SCHEMA)
# ==============================================================================
@st.cache_data(ttl=1200, show_spinner=False)
def load_filter_options():
    meses_df = run_query(
        """
        SELECT DISTINCT
            mes_id,
            mes_nome,
            mes_texto,
            CAST(mes_numeronoano AS UNSIGNED) AS mes_num,
            trimestre_texto
        FROM dimdata
        WHERE ano_id = 2025 AND semestre_numeronoano = 1
        ORDER BY mes_id
        """
    )

    municipios_df = run_query(
        """
        SELECT `key`, id_municipio, nome_municipio
        FROM dimlocal
        ORDER BY CASE WHEN `key` = 0 THEN 1 ELSE 0 END, nome_municipio
        """
    )

    categorias_df = run_query(
        """
        SELECT DISTINCT codigo_categoria_economica, nome_categoria_economica
        FROM dimclassificacaoorcamentaria
        ORDER BY codigo_categoria_economica
        """
    )

    funcoes_df = run_query(
        """
        SELECT DISTINCT codigo_funcao, nome_funcao
        FROM dimclassificacaoorcamentaria
        ORDER BY nome_funcao
        """
    )

    modalidades_df = run_query(
        """
        SELECT DISTINCT modalidade_licitacao
        FROM dimlicitacao
        ORDER BY modalidade_licitacao
        """
    )

    return meses_df, municipios_df, categorias_df, funcoes_df, modalidades_df


DIM_JOIN_SQL = {
    "dt": "INNER JOIN dimdata dt ON f.dataKey = dt.keyData",
    "loc": "INNER JOIN dimlocal loc ON f.localKey = loc.`key`",
    "ug": "INNER JOIN dimunidadegestora ug ON f.unidadeGestoraKey = ug.`key`",
    "cr": "INNER JOIN dimcredor cr ON f.credorKey = cr.`key`",
    "cla": "INNER JOIN dimclassificacaoorcamentaria cla ON f.classificacaoKey = cla.`key`",
    "lic": "INNER JOIN dimlicitacao lic ON f.licitacaoKey = lic.`key`",
}


def build_star_query_parts(
    required_dims: list[str],
    meses_sel: list[int],
    trimestres_sel: list[str],
    municipios_sel: list[str],
    categorias_sel: list[str],
    funcoes_sel: list[str],
    modalidades_sel: list[str],
    ignore_categoria_filter: bool = False,
    ignore_funcao_filter: bool = False,
) -> tuple[str, str, dict]:
    """
    Constrói dinamicamente apenas os JOINs necessários para a consulta e os filtros ativos,
    evitando junções desnecessárias nas 854 mil linhas da tabela fato.
    """
    needed = set(required_dims)
    clauses = ["1=1"]
    params = {}

    if meses_sel:
        needed.add("dt")
        placeholders = ", ".join([f":m_{i}" for i in range(len(meses_sel))])
        clauses.append(f"dt.mes_id IN ({placeholders})")
        for i, v in enumerate(meses_sel):
            params[f"m_{i}"] = int(v)

    if trimestres_sel:
        needed.add("dt")
        placeholders = ", ".join([f":t_{i}" for i in range(len(trimestres_sel))])
        clauses.append(f"dt.trimestre_texto IN ({placeholders})")
        for i, v in enumerate(trimestres_sel):
            params[f"t_{i}"] = v

    if municipios_sel:
        needed.add("loc")
        placeholders = ", ".join([f":mun_{i}" for i in range(len(municipios_sel))])
        clauses.append(f"loc.nome_municipio IN ({placeholders})")
        for i, v in enumerate(municipios_sel):
            params[f"mun_{i}"] = v

    if categorias_sel and not ignore_categoria_filter:
        needed.add("cla")
        placeholders = ", ".join([f":cat_{i}" for i in range(len(categorias_sel))])
        clauses.append(f"cla.nome_categoria_economica IN ({placeholders})")
        for i, v in enumerate(categorias_sel):
            params[f"cat_{i}"] = v

    if funcoes_sel and not ignore_funcao_filter:
        needed.add("cla")
        placeholders = ", ".join([f":fn_{i}" for i in range(len(funcoes_sel))])
        clauses.append(f"cla.nome_funcao IN ({placeholders})")
        for i, v in enumerate(funcoes_sel):
            params[f"fn_{i}"] = v

    if modalidades_sel:
        needed.add("lic")
        placeholders = ", ".join([f":mod_{i}" for i in range(len(modalidades_sel))])
        clauses.append(f"lic.modalidade_licitacao IN ({placeholders})")
        for i, v in enumerate(modalidades_sel):
            params[f"mod_{i}"] = v

    ordered_dims = [d for d in ["dt", "loc", "ug", "cr", "cla", "lic"] if d in needed]
    joins_sql = "\n    ".join([DIM_JOIN_SQL[d] for d in ordered_dims])
    where_sql = " AND ".join(clauses)
    return joins_sql, where_sql, params


# ==============================================================================
# 4. INICIALIZAÇÃO E BARRA LATERAL (FILTROS OLAP DINÂMICOS)
# ==============================================================================
try:
    meses_df, municipios_df, categorias_df, funcoes_df, modalidades_df = load_filter_options()
except Exception as err:
    st.error(
        f"❌ Erro ao conectar ao banco MySQL `{DB_NAME}` em `{DB_HOST}:{DB_PORT}` com usuário `{DB_USER}`.\n\n"
        f"Detalhe técnico: `{err}`"
    )
    st.stop()

with st.sidebar:
    st.title("🎛️ Filtros OLAP (Slice & Dice)")
    st.caption(f"🟢 Conectado: `{DB_HOST}:{DB_PORT}/{DB_NAME}`")

    st.markdown("### 📅 Recorte Temporal (`dimData`)")
    opcoes_trimestre = sorted(meses_df["trimestre_texto"].unique().tolist())
    trimestres_sel = st.multiselect(
        "Trimestres:",
        options=opcoes_trimestre,
        default=[],
        placeholder="Todos os trimestres (1º Semestre)",
    )

    meses_map = {
        f"{row['mes_nome']} - {row['mes_texto']}": int(row["mes_id"])
        for _, row in meses_df.iterrows()
    }
    meses_labels_sel = st.multiselect(
        "Meses:",
        options=list(meses_map.keys()),
        default=[],
        placeholder="Todos os meses (Jan a Jun/2025)",
    )
    meses_sel = [meses_map[label] for label in meses_labels_sel]

    st.markdown("### 🏛️ Localidade e Classificação")
    municipios_sel = st.multiselect(
        "Municípios (`dimLocal`):",
        options=municipios_df["nome_municipio"].tolist(),
        default=[],
        placeholder="Todos os 223 municípios",
    )

    categorias_sel = st.multiselect(
        "Categoria Econômica (`dimClassificacao`):",
        options=categorias_df["nome_categoria_economica"].tolist(),
        default=[],
        placeholder="Todas as categorias",
    )

    funcoes_sel = st.multiselect(
        "Função Orçamentária (`dimClassificacao`):",
        options=funcoes_df["nome_funcao"].tolist(),
        default=[],
        placeholder="Todas as funções",
    )

    modalidades_sel = st.multiselect(
        "Modalidade de Licitação (`dimLicitacao`):",
        options=modalidades_df["modalidade_licitacao"].tolist(),
        default=[],
        placeholder="Todas as modalidades",
    )

    st.markdown("---")
    st.markdown("### ⚙️ Parâmetros Globais de Retorno")
    top_n_default = st.number_input(
        "Quantidade padrão de itens (Top N):",
        min_value=1,
        max_value=500,
        value=15,
        step=5,
        help="Define o limite padrão inicial de linhas/barras nos rankings (você também pode ajustar individualmente em cada análise).",
    )
    ocultar_sentinelas = st.toggle(
        "Ocultar registros sentinelas (Chave 0 / Sem Credor)",
        value=True,
        help="Exclui as chaves sentinelas ('Sem Credor', 'Sem Município', 'Não Informado') dos rankings analíticos.",
    )

    if st.button("🔄 Limpar Cache de Consultas", width="stretch"):
        st.cache_data.clear()
        st.rerun()

# ==============================================================================
# 5. CABEÇALHO E KPIS GLOBAIS DO DATA WAREHOUSE
# ==============================================================================
st.title("📊 Painel Analítico OLAP — Data Warehouse de Despesas Públicas (TCE-PB 2025)")
st.markdown(
    "Exploração multidimensional interativa sobre o **Star Schema (`dw_despesas`)** do 1º Semestre de 2025. "
    "Utilize a barra lateral para aplicar cortes (*Slice & Dice*) e os controles de cada aba para ajustar limites (*Top N*), métricas e níveis de granularidade (*Drill-down / Roll-up*)."
)

kpi_joins, kpi_where, kpi_params = build_star_query_parts(
    required_dims=[],
    meses_sel=meses_sel,
    trimestres_sel=trimestres_sel,
    municipios_sel=municipios_sel,
    categorias_sel=categorias_sel,
    funcoes_sel=funcoes_sel,
    modalidades_sel=modalidades_sel,
)

kpi_sql = f"""
SELECT
    COUNT(*) AS total_registros_fato,
    SUM(f.valorEmpenhado) AS total_empenhado,
    SUM(f.valorLiquidado) AS total_liquidado,
    SUM(f.valorPago) AS total_pago,
    SUM(f.saldoAPagar) AS total_saldo_pagar,
    COUNT(DISTINCT NULLIF(f.localKey, 0)) AS total_municipios,
    COUNT(DISTINCT NULLIF(f.unidadeGestoraKey, 0)) AS total_ugs,
    COUNT(DISTINCT NULLIF(f.credorKey, 0)) AS total_credores
FROM fatodespesa f
{kpi_joins}
WHERE {kpi_where}
"""
kpi_df = run_query(kpi_sql, kpi_params)
kpi_row = kpi_df.iloc[0]

tot_emp = float(kpi_row["total_empenhado"] or 0.0)
tot_liq = float(kpi_row["total_liquidado"] or 0.0)
tot_pag = float(kpi_row["total_pago"] or 0.0)
tot_sal = float(kpi_row["total_saldo_pagar"] or 0.0)
taxa_conv_global = (tot_pag / tot_emp * 100.0) if tot_emp > 0 else 0.0
taxa_liq_global = (tot_liq / tot_emp * 100.0) if tot_emp > 0 else 0.0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("💰 Total Empenhado", fmt_brl_compact(tot_emp), help=fmt_brl(tot_emp))
k2.metric("📋 Total Liquidado", fmt_brl_compact(tot_liq), f"{fmt_pct(taxa_liq_global)} do empenhado", help=fmt_brl(tot_liq))
k3.metric("✅ Total Pago", fmt_brl_compact(tot_pag), f"{fmt_pct(taxa_conv_global)} conversão", help=fmt_brl(tot_pag))
k4.metric("⚠️ Saldo a Pagar", fmt_brl_compact(tot_sal), f"{fmt_pct(100 - taxa_conv_global)} retido", delta_color="inverse", help=fmt_brl(tot_sal))
k5.metric("🏙️ Municípios / UGs", f"{fmt_int(kpi_row['total_municipios'])} / {fmt_int(kpi_row['total_ugs'])}")
k6.metric("🤝 Credores Ativos", fmt_int(kpi_row["total_credores"]), f"{fmt_int(kpi_row['total_registros_fato'])} células Fato")

st.markdown("---")

# ==============================================================================
# 6. NAVEGAÇÃO POR ABAS DAS 8 QUESTÕES ANALÍTICAS + EXPLORADOR OLAP LIVRE
# ==============================================================================
tabs = st.tabs(
    [
        "1️⃣ Liquidez Mensal",
        "2️⃣ Top Fornecedores",
        "3️⃣ Disparidade Municipal",
        "4️⃣ Saúde vs. Educação",
        "5️⃣ Risco Fiscal (RAP)",
        "6️⃣ Capilaridade Intermunicipal",
        "7️⃣ Dispersão & Natureza (ROLLUP)",
        "8️⃣ Rastreabilidade (Capital)",
        "🧊 Cubo OLAP Livre",
    ]
)

# ------------------------------------------------------------------------------
# ABA 1: CURVA DE CONVERSÃO E LIQUIDEZ MENSAL
# ------------------------------------------------------------------------------
with tabs[0]:
    st.subheader("1. Curva de Conversão e Liquidez Mensal")
    st.info(
        "**Pergunta de Negócio:** *Qual o volume financeiro empenhado, liquidado e pago por cada mês, "
        "e qual a taxa percentual de conversão de empenhos em pagamentos efetivos?*"
    )

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        granularidade_tempo = st.selectbox(
            "Nível de Agregação Temporal (Roll-up / Drill-down):",
            options=["Mês", "Trimestre", "Semana do Ano", "Dia Útil vs. Fim de Semana"],
            index=0,
            key="q1_gran",
        )
    with c2:
        exibir_valores_grafico = st.selectbox(
            "Formato dos Rótulos no Gráfico:",
            options=["Compacto (R$ mi / bi)", "Completo (R$)"],
            index=0,
            key="q1_fmt",
        )
    with c3:
        meta_conversao = st.slider(
            "Linha de Referência — Taxa de Conversão (%):",
            min_value=0,
            max_value=100,
            value=80,
            step=5,
            key="q1_meta",
        )

    if granularidade_tempo == "Mês":
        grp_select = "dt.mes_id AS ordem, CONCAT(dt.mes_nome, ' - ', dt.mes_texto, '/2025') AS periodo"
        grp_by = "dt.mes_id, dt.mes_nome, dt.mes_texto"
    elif granularidade_tempo == "Trimestre":
        grp_select = "dt.trimestre_id AS ordem, CONCAT(dt.trimestre_nome, ' - ', dt.trimestre_texto) AS periodo"
        grp_by = "dt.trimestre_id, dt.trimestre_nome, dt.trimestre_texto"
    elif granularidade_tempo == "Semana do Ano":
        grp_select = "dt.semana_numeronoano AS ordem, CONCAT('Sem ', LPAD(dt.semana_numeronoano, 2, '0')) AS periodo"
        grp_by = "dt.semana_numeronoano"
    else:
        grp_select = (
            "dt.dia_ehdiautil AS ordem, "
            "CASE WHEN dt.dia_ehdiautil = 1 THEN 'Dia Útil' ELSE 'Fim de Semana / Feriado' END AS periodo"
        )
        grp_by = "dt.dia_ehdiautil"

    q1_joins, q1_where, q1_params = build_star_query_parts(
        required_dims=["dt"],
        meses_sel=meses_sel,
        trimestres_sel=trimestres_sel,
        municipios_sel=municipios_sel,
        categorias_sel=categorias_sel,
        funcoes_sel=funcoes_sel,
        modalidades_sel=modalidades_sel,
    )

    q1_sql = f"""
    SELECT
        {grp_select},
        COUNT(*) AS qtd_alocacoes,
        SUM(f.valorEmpenhado) AS valor_empenhado,
        SUM(f.valorLiquidado) AS valor_liquidado,
        SUM(f.valorPago) AS valor_pago,
        SUM(f.saldoAPagar) AS saldo_a_pagar,
        ROUND(SUM(f.valorLiquidado) / NULLIF(SUM(f.valorEmpenhado), 0) * 100, 2) AS taxa_liquidacao_pct,
        ROUND(SUM(f.valorPago) / NULLIF(SUM(f.valorEmpenhado), 0) * 100, 2) AS taxa_conversao_pct,
        ROUND(SUM(f.valorPago) / NULLIF(SUM(f.valorLiquidado), 0) * 100, 2) AS eficiencia_pagamento_liq_pct
    FROM fatodespesa f
    {q1_joins}
    WHERE {q1_where} AND dt.keyData > 0
    GROUP BY {grp_by}
    ORDER BY ordem ASC
    """
    q1_df = run_query(q1_sql, q1_params)

    if q1_df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        fig_q1 = make_subplots(specs=[[{"secondary_y": True}]])

        for col_name, label, color in [
            ("valor_empenhado", "Valor Empenhado", "#1f77b4"),
            ("valor_liquidado", "Valor Liquidado", "#ff7f0e"),
            ("valor_pago", "Valor Pago", "#2ca02c"),
        ]:
            text_vals = (
                [fmt_brl_compact(v) for v in q1_df[col_name]]
                if exibir_valores_grafico.startswith("Compacto")
                else [fmt_brl(v) for v in q1_df[col_name]]
            )
            fig_q1.add_trace(
                go.Bar(
                    x=q1_df["periodo"],
                    y=q1_df[col_name],
                    name=label,
                    marker_color=color,
                    text=text_vals,
                    textposition="auto",
                ),
                secondary_y=False,
            )

        fig_q1.add_trace(
            go.Scatter(
                x=q1_df["periodo"],
                y=q1_df["taxa_conversao_pct"],
                name="Taxa de Conversão (Pago / Empenhado %)",
                mode="lines+markers+text",
                text=[f"{v:.1f}%" for v in q1_df["taxa_conversao_pct"].fillna(0)],
                textposition="top center",
                line=dict(color="#d62728", width=3),
                marker=dict(size=9),
            ),
            secondary_y=True,
        )

        fig_q1.add_trace(
            go.Scatter(
                x=q1_df["periodo"],
                y=q1_df["taxa_liquidacao_pct"],
                name="Taxa de Liquidação (Liquidado / Empenhado %)",
                mode="lines+markers",
                line=dict(color="#9467bd", width=2, dash="dot"),
                marker=dict(size=7),
            ),
            secondary_y=True,
        )

        fig_q1.add_hline(
            y=meta_conversao,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Referência ({meta_conversao}%)",
            secondary_y=True,
        )

        fig_q1.update_layout(
            title=f"Execução Orçamentária e Taxa de Conversão por {granularidade_tempo}",
            barmode="group",
            height=480,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title=granularidade_tempo,
        )
        fig_q1.update_yaxes(title_text="Volume Financeiro (R$)", secondary_y=False)
        fig_q1.update_yaxes(title_text="Taxa Percentual (%)", range=[0, 115], secondary_y=True)

        st.plotly_chart(fig_q1, width="stretch")

        q1_disp = q1_df[
            [
                "periodo",
                "qtd_alocacoes",
                "valor_empenhado",
                "valor_liquidado",
                "valor_pago",
                "saldo_a_pagar",
                "taxa_liquidacao_pct",
                "taxa_conversao_pct",
                "eficiencia_pagamento_liq_pct",
            ]
        ].copy()
        q1_disp.columns = [
            "Período",
            "Registros Fato",
            "Valor Empenhado (R$)",
            "Valor Liquidado (R$)",
            "Valor Pago (R$)",
            "Saldo a Pagar (R$)",
            "Taxa Liquidação (%)",
            "Taxa Conversão Pago/Emp (%)",
            "Quitação Pago/Liq (%)",
        ]
        st.dataframe(
            q1_disp.style.format(
                {
                    "Registros Fato": "{:,.0f}",
                    "Valor Empenhado (R$)": "R$ {:,.2f}",
                    "Valor Liquidado (R$)": "R$ {:,.2f}",
                    "Valor Pago (R$)": "R$ {:,.2f}",
                    "Saldo a Pagar (R$)": "R$ {:,.2f}",
                    "Taxa Liquidação (%)": "{:.2f}%",
                    "Taxa Conversão Pago/Emp (%)": "{:.2f}%",
                    "Quitação Pago/Liq (%)": "{:.2f}%",
                },
                thousands=".",
                decimal=",",
            ),
            width="stretch",
            hide_index=True,
        )

        with st.expander("🔍 Ver Consulta SQL executada no Data Warehouse"):
            st.code(q1_sql, language="sql")


# ------------------------------------------------------------------------------
# ABA 2: CONCENTRAÇÃO DE PAGAMENTOS NOS PRINCIPAIS FORNECEDORES
# ------------------------------------------------------------------------------
with tabs[1]:
    st.subheader("2. Concentração de Pagamentos nos Principais Fornecedores")
    st.info(
        "**Pergunta de Negócio:** *Quais são os credores que receberam o maior volume financeiro pago, "
        "quantas unidades gestoras distintas os contrataram e qual foi o tíquete médio por empenho/alocação?*"
    )

    c1, c2, c3, c4 = st.columns([1.5, 2, 1.5, 2])
    with c1:
        q2_top_n = st.number_input(
            "Quantos fornecedores retornar (Top N):",
            min_value=1,
            max_value=500,
            value=int(top_n_default),
            step=5,
            key="q2_topn",
        )
    with c2:
        q2_ordem = st.selectbox(
            "Ordenar Fornecedores por:",
            options=[
                "Maior Volume Pago (R$)",
                "Maior Volume Empenhado (R$)",
                "Maior Nº de Unidades Gestoras",
                "Maior Tíquete Médio Pago (R$)",
            ],
            index=0,
            key="q2_ord",
        )
    with c3:
        q2_min_ugs = st.number_input(
            "Mínimo de UGs Distintas:",
            min_value=1,
            max_value=200,
            value=1,
            step=1,
            key="q2_min_ugs",
        )
    with c4:
        q2_busca_credor = st.text_input(
            "Filtrar por Nome ou CPF/CNPJ do Credor:",
            value="",
            placeholder="Ex: INSTITUTO, CONSTRUTORA, 0000...",
            key="q2_search",
        )

    ordem_map_q2 = {
        "Maior Volume Pago (R$)": "valor_pago DESC",
        "Maior Volume Empenhado (R$)": "valor_empenhado DESC",
        "Maior Nº de Unidades Gestoras": "ugs_distintas DESC, valor_pago DESC",
        "Maior Tíquete Médio Pago (R$)": "tiquete_medio_pago DESC",
    }

    req_q2 = ["cr"] if q2_busca_credor.strip() else []
    q2_joins, q2_where, params_q2 = build_star_query_parts(
        required_dims=req_q2,
        meses_sel=meses_sel,
        trimestres_sel=trimestres_sel,
        municipios_sel=municipios_sel,
        categorias_sel=categorias_sel,
        funcoes_sel=funcoes_sel,
        modalidades_sel=modalidades_sel,
    )

    credor_key_filter = "AND f.credorKey > 0" if ocultar_sentinelas else ""
    params_q2["min_ugs"] = int(q2_min_ugs)
    params_q2["limit_n"] = int(q2_top_n)

    if q2_busca_credor.strip():
        credor_key_filter += " AND (cr.nome_credor LIKE :busca_cr OR cr.cpf_cnpj LIKE :busca_cr)"
        params_q2["busca_cr"] = f"%{q2_busca_credor.strip()}%"

    q2_sql = f"""
    SELECT
        cr.cpf_cnpj,
        cr.nome_credor,
        agg.ugs_distintas,
        agg.municipios_distintos,
        agg.qtd_alocacoes,
        agg.valor_empenhado,
        agg.valor_liquidado,
        agg.valor_pago,
        agg.tiquete_medio_pago,
        agg.tiquete_medio_empenhado
    FROM (
        SELECT
            f.credorKey,
            COUNT(DISTINCT NULLIF(f.unidadeGestoraKey, 0)) AS ugs_distintas,
            COUNT(DISTINCT NULLIF(f.localKey, 0)) AS municipios_distintos,
            COUNT(*) AS qtd_alocacoes,
            SUM(f.valorEmpenhado) AS valor_empenhado,
            SUM(f.valorLiquidado) AS valor_liquidado,
            SUM(f.valorPago) AS valor_pago,
            ROUND(SUM(f.valorPago) / NULLIF(COUNT(*), 0), 2) AS tiquete_medio_pago,
            ROUND(SUM(f.valorEmpenhado) / NULLIF(COUNT(*), 0), 2) AS tiquete_medio_empenhado
        FROM fatodespesa f
        {q2_joins}
        WHERE {q2_where} {credor_key_filter}
        GROUP BY f.credorKey
        HAVING ugs_distintas >= :min_ugs
        ORDER BY {ordem_map_q2[q2_ordem]}
        LIMIT :limit_n
    ) agg
    INNER JOIN dimcredor cr ON agg.credorKey = cr.`key`
    ORDER BY {ordem_map_q2[q2_ordem]}
    """
    q2_df = run_query(q2_sql, params_q2)

    if q2_df.empty:
        st.warning("Nenhum fornecedor encontrado com os critérios selecionados.")
    else:
        q2_df["share_pago_pct"] = (q2_df["valor_pago"] / tot_pag * 100.0) if tot_pag > 0 else 0.0
        q2_df["credor_label"] = (
            q2_df["nome_credor"].str.slice(0, 38) + " (" + q2_df["cpf_cnpj"].astype(str) + ")"
        )

        s1, s2, s3 = st.columns(3)
        soma_top_pago = float(q2_df["valor_pago"].sum())
        s1.metric(
            f"Volume Pago ao Top {len(q2_df)} Fornecedores",
            fmt_brl_compact(soma_top_pago),
            f"{fmt_pct((soma_top_pago / tot_pag * 100) if tot_pag > 0 else 0)} do total pago",
        )
        s2.metric(
            "Média de UGs por Fornecedor (no Top N)",
            f"{q2_df['ugs_distintas'].mean():.1f} UGs",
            f"Máx: {fmt_int(q2_df['ugs_distintas'].max())} UGs",
        )
        s3.metric(
            "Tíquete Médio Pago (Média do Top N)",
            fmt_brl_compact(q2_df["tiquete_medio_pago"].mean()),
            help=fmt_brl(q2_df["tiquete_medio_pago"].mean()),
        )

        col_g1, col_g2 = st.columns([1.35, 1])
        with col_g1:
            fig_q2_bar = px.bar(
                q2_df.iloc[::-1],
                x="valor_pago",
                y="credor_label",
                orientation="h",
                color="ugs_distintas",
                color_continuous_scale="Viridis",
                text=[fmt_brl_compact(v) for v in q2_df.iloc[::-1]["valor_pago"]],
                labels={
                    "valor_pago": "Volume Pago (R$)",
                    "credor_label": "Credor (CPF/CNPJ)",
                    "ugs_distintas": "UGs Distintas",
                },
                title=f"Top {len(q2_df)} Fornecedores por Volume Financeiro Pago",
            )
            fig_q2_bar.update_layout(height=max(420, min(900, len(q2_df) * 28)))
            st.plotly_chart(fig_q2_bar, width="stretch")

        with col_g2:
            fig_q2_scat = px.scatter(
                q2_df,
                x="ugs_distintas",
                y="valor_pago",
                size="tiquete_medio_pago",
                color="municipios_distintos",
                hover_name="nome_credor",
                hover_data={
                    "cpf_cnpj": True,
                    "valor_pago": ":,.2f",
                    "tiquete_medio_pago": ":,.2f",
                    "ugs_distintas": True,
                    "municipios_distintos": True,
                },
                labels={
                    "ugs_distintas": "Nº de Unidades Gestoras Distintas",
                    "valor_pago": "Volume Total Pago (R$)",
                    "tiquete_medio_pago": "Tíquete Médio Pago",
                    "municipios_distintos": "Municípios",
                },
                title="Dispersão: Capilaridade em UGs vs. Volume Pago (Bolha = Tíquete Médio)",
            )
            fig_q2_scat.update_layout(height=max(420, min(900, len(q2_df) * 28)))
            st.plotly_chart(fig_q2_scat, width="stretch")

        q2_disp = q2_df[
            [
                "cpf_cnpj",
                "nome_credor",
                "ugs_distintas",
                "municipios_distintos",
                "qtd_alocacoes",
                "valor_empenhado",
                "valor_liquidado",
                "valor_pago",
                "tiquete_medio_empenhado",
                "tiquete_medio_pago",
                "share_pago_pct",
            ]
        ].copy()
        q2_disp.columns = [
            "CPF / CNPJ",
            "Nome do Credor",
            "UGs Distintas",
            "Municípios",
            "Alocações (Fato)",
            "Total Empenhado (R$)",
            "Total Liquidado (R$)",
            "Total Pago (R$)",
            "Tíquete Médio Emp. (R$)",
            "Tíquete Médio Pago (R$)",
            "% do Total Pago",
        ]
        st.dataframe(
            q2_disp.style.format(
                {
                    "UGs Distintas": "{:,.0f}",
                    "Municípios": "{:,.0f}",
                    "Alocações (Fato)": "{:,.0f}",
                    "Total Empenhado (R$)": "R$ {:,.2f}",
                    "Total Liquidado (R$)": "R$ {:,.2f}",
                    "Total Pago (R$)": "R$ {:,.2f}",
                    "Tíquete Médio Emp. (R$)": "R$ {:,.2f}",
                    "Tíquete Médio Pago (R$)": "R$ {:,.2f}",
                    "% do Total Pago": "{:.2f}%",
                },
                thousands=".",
                decimal=",",
            ),
            width="stretch",
            hide_index=True,
        )

        with st.expander("🔍 Ver Consulta SQL executada no Data Warehouse"):
            st.code(q2_sql, language="sql")


# ------------------------------------------------------------------------------
# ABA 3: DISPARIDADE MUNICIPAL EM RELAÇÃO À MÉDIA ESTADUAL
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("3. Disparidade Municipal em Relação à Média Estadual")
    st.info(
        "**Pergunta de Negócio:** *Quais municípios paraibanos tiveram uma despesa total paga superior "
        "à média dos gastos municipais do estado?*"
    )

    c1, c2, c3, c4 = st.columns([2, 2, 1.5, 1.5])
    with c1:
        q3_metrica = st.selectbox(
            "Métrica de Comparação Municipal:",
            options=["Valor Pago (R$)", "Valor Empenhado (R$)", "Valor Liquidado (R$)"],
            index=0,
            key="q3_met",
        )
    with c2:
        q3_Modo = st.selectbox(
            "Filtro em Relação à Média Estadual:",
            options=[
                "Apenas Municípios ACIMA da Média Estadual",
                "Todos os Municípios (Acima e Abaixo)",
                "Apenas Municípios ABAIXO da Média Estadual",
            ],
            index=0,
            key="q3_modo",
        )
    with c3:
        q3_mult = st.slider(
            "Múltiplo Mínimo da Média (x):",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.25,
            help="1.0x = exatamente acima da média estadual; 2.0x = pelo menos o dobro da média estadual.",
            key="q3_mult",
        )
    with c4:
        q3_top_n = st.number_input(
            "Limite de Municípios a Exibir:",
            min_value=1,
            max_value=225,
            value=min(50, max(20, int(top_n_default))),
            step=5,
            key="q3_topn",
        )

    q3_joins, q3_where, q3_params = build_star_query_parts(
        required_dims=["loc"],
        meses_sel=meses_sel,
        trimestres_sel=trimestres_sel,
        municipios_sel=municipios_sel,
        categorias_sel=categorias_sel,
        funcoes_sel=funcoes_sel,
        modalidades_sel=modalidades_sel,
    )

    q3_sql = f"""
    SELECT
        loc.id_municipio,
        loc.nome_municipio,
        COUNT(DISTINCT NULLIF(f.unidadeGestoraKey, 0)) AS qtd_ugs,
        SUM(f.valorEmpenhado) AS valor_empenhado,
        SUM(f.valorLiquidado) AS valor_liquidado,
        SUM(f.valorPago) AS valor_pago,
        SUM(f.saldoAPagar) AS saldo_a_pagar
    FROM fatodespesa f
    {q3_joins}
    WHERE {q3_where} {"AND f.localKey > 0" if ocultar_sentinelas else ""}
    GROUP BY loc.`key`, loc.id_municipio, loc.nome_municipio
    """
    q3_all_df = run_query(q3_sql, q3_params)

    if q3_all_df.empty:
        st.warning("Nenhum município retornado para os filtros selecionados.")
    else:
        col_met_map = {
            "Valor Pago (R$)": "valor_pago",
            "Valor Empenhado (R$)": "valor_empenhado",
            "Valor Liquidado (R$)": "valor_liquidado",
        }
        target_col = col_met_map[q3_metrica]
        q3_all_df[target_col] = q3_all_df[target_col].astype(float)

        media_estadual = float(q3_all_df[target_col].mean())
        mediana_estadual = float(q3_all_df[target_col].median())
        soma_estadual = float(q3_all_df[target_col].sum())

        q3_all_df["media_estadual"] = media_estadual
        q3_all_df["diferenca_media"] = q3_all_df[target_col] - media_estadual
        q3_all_df["multiplo_media"] = q3_all_df[target_col] / media_estadual if media_estadual > 0 else 0.0
        q3_all_df["share_estadual_pct"] = (
            q3_all_df[target_col] / soma_estadual * 100.0 if soma_estadual > 0 else 0.0
        )
        q3_all_df["status_media"] = q3_all_df[target_col].apply(
            lambda x: "Acima da Média" if x > media_estadual else "Abaixo da Média"
        )

        acima_df = q3_all_df[q3_all_df[target_col] > media_estadual]
        qtd_acima = len(acima_df)
        qtd_total_mun = len(q3_all_df)
        share_acima = float(acima_df[target_col].sum() / soma_estadual * 100.0) if soma_estadual > 0 else 0.0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📏 Média Estadual por Município", fmt_brl_compact(media_estadual), help=fmt_brl(media_estadual))
        m2.metric("⚖️ Mediana Estadual por Município", fmt_brl_compact(mediana_estadual), help=fmt_brl(mediana_estadual))
        m3.metric(
            "🏙️ Municípios Acima da Média",
            f"{qtd_acima} de {qtd_total_mun}",
            f"{fmt_pct(qtd_acima / qtd_total_mun * 100 if qtd_total_mun else 0)} dos municípios",
        )
        m4.metric(
            "💰 Concentração nos Acima da Média",
            fmt_pct(share_acima),
            f"Concentram {fmt_brl_compact(float(acima_df[target_col].sum()))}",
        )

        q3_filtered = q3_all_df.copy()
        if q3_Modo.startswith("Apenas Municípios ACIMA"):
            q3_filtered = q3_filtered[q3_filtered["multiplo_media"] >= max(1.0, q3_mult)]
        elif q3_Modo.startswith("Apenas Municípios ABAIXO"):
            q3_filtered = q3_filtered[q3_filtered[target_col] <= media_estadual]
        else:
            q3_filtered = q3_filtered[q3_filtered["multiplo_media"] >= q3_mult]

        q3_filtered = q3_filtered.sort_values(by=target_col, ascending=False).head(int(q3_top_n))

        fig_q3 = px.bar(
            q3_filtered,
            x="nome_municipio",
            y=target_col,
            color="status_media",
            color_discrete_map={"Acima da Média": "#1f77b4", "Abaixo da Média": "#aec7e8"},
            text=[f"{m:.1f}x" for m in q3_filtered["multiplo_media"]],
            hover_data={
                "valor_empenhado": ":,.2f",
                "valor_pago": ":,.2f",
                "diferenca_media": ":,.2f",
                "multiplo_media": ":.2f",
                "share_estadual_pct": ":.2f",
            },
            labels={
                "nome_municipio": "Município",
                target_col: q3_metrica,
                "status_media": "Posição vs. Média",
            },
            title=f"Disparidade Municipal ({len(q3_filtered)} exibidos) vs. Média Estadual ({fmt_brl_compact(media_estadual)})",
        )
        fig_q3.add_hline(
            y=media_estadual,
            line_dash="dash",
            line_color="#d62728",
            line_width=2.5,
            annotation_text=f"Média Estadual: {fmt_brl_compact(media_estadual)}",
            annotation_position="top right",
        )
        fig_q3.update_layout(height=460, xaxis_tickangle=-45)
        st.plotly_chart(fig_q3, width="stretch")

        q3_disp = q3_filtered[
            [
                "nome_municipio",
                "qtd_ugs",
                "valor_empenhado",
                "valor_liquidado",
                "valor_pago",
                "media_estadual",
                "diferenca_media",
                "multiplo_media",
                "share_estadual_pct",
            ]
        ].copy()
        q3_disp.columns = [
            "Município",
            "UGs",
            "Total Empenhado (R$)",
            "Total Liquidado (R$)",
            "Total Pago (R$)",
            "Média Estadual (R$)",
            "Acima/Abaixo da Média (R$)",
            "Múltiplo da Média (x)",
            "% do Estado",
        ]
        st.dataframe(
            q3_disp.style.format(
                {
                    "UGs": "{:,.0f}",
                    "Total Empenhado (R$)": "R$ {:,.2f}",
                    "Total Liquidado (R$)": "R$ {:,.2f}",
                    "Total Pago (R$)": "R$ {:,.2f}",
                    "Média Estadual (R$)": "R$ {:,.2f}",
                    "Acima/Abaixo da Média (R$)": "R$ {:+,.2f}",
                    "Múltiplo da Média (x)": "{:.2f}x",
                    "% do Estado": "{:.2f}%",
                },
                thousands=".",
                decimal=",",
            ),
            width="stretch",
            hide_index=True,
        )

        with st.expander("🔍 Ver Consulta SQL executada no Data Warehouse"):
            st.code(q3_sql, language="sql")


# ------------------------------------------------------------------------------
# ABA 4: EVOLUÇÃO TEMPORAL DAS ÁREAS ESSENCIAIS (SAÚDE VS. EDUCAÇÃO)
# ------------------------------------------------------------------------------
with tabs[3]:
    st.subheader("4. Evolução Temporal das Áreas Essenciais (Saúde vs. Educação)")
    st.info(
        "**Pergunta de Negócio:** *Quando comparamos a evolução mês a mês, qual foi o volume pago para as "
        "funções prioritárias (como Saúde e Educação) e qual a sua participação percentual sobre o montante geral pago?*"
    )

    todas_funcoes_lista = funcoes_df["nome_funcao"].tolist()
    default_prioritarias = [f for f in ["Saúde", "Educação"] if f in todas_funcoes_lista]

    c1, c2 = st.columns([3, 1.5])
    with c1:
        funcoes_foco = st.multiselect(
            "Selecione as Funções Prioritárias para Comparação Mês a Mês:",
            options=todas_funcoes_lista,
            default=default_prioritarias,
            key="q4_funcoes",
        )
    with c2:
        q4_metrica = st.selectbox(
            "Métrica Financeira Analisada:",
            options=["Valor Pago (R$)", "Valor Empenhado (R$)", "Valor Liquidado (R$)"],
            index=0,
            key="q4_met",
        )

    joins_q4, where_q4, params_q4 = build_star_query_parts(
        required_dims=["dt", "cla"],
        meses_sel=meses_sel,
        trimestres_sel=trimestres_sel,
        municipios_sel=municipios_sel,
        categorias_sel=categorias_sel,
        funcoes_sel=funcoes_sel,
        modalidades_sel=modalidades_sel,
        ignore_funcao_filter=True,
    )

    q4_sql = f"""
    SELECT
        dt.mes_id,
        CONCAT(dt.mes_nome, ' - ', dt.mes_texto) AS mes_label,
        cla.nome_funcao,
        SUM(f.valorEmpenhado) AS valor_empenhado,
        SUM(f.valorLiquidado) AS valor_liquidado,
        SUM(f.valorPago) AS valor_pago
    FROM fatodespesa f
    {joins_q4}
    WHERE {where_q4} AND dt.keyData > 0
    GROUP BY dt.mes_id, dt.mes_nome, dt.mes_texto, cla.nome_funcao
    ORDER BY dt.mes_id ASC
    """
    q4_raw_df = run_query(q4_sql, params_q4)

    if q4_raw_df.empty or not funcoes_foco:
        st.warning("Selecione pelo menos uma Função Prioritária para visualizar a evolução.")
    else:
        col_q4 = {
            "Valor Pago (R$)": "valor_pago",
            "Valor Empenhado (R$)": "valor_empenhado",
            "Valor Liquidado (R$)": "valor_liquidado",
        }[q4_metrica]

        totais_mes = (
            q4_raw_df.groupby(["mes_id", "mes_label"], as_index=False)[col_q4]
            .sum()
            .rename(columns={col_q4: "montante_geral_mes"})
        )

        foco_df = q4_raw_df[q4_raw_df["nome_funcao"].isin(funcoes_foco)].merge(
            totais_mes, on=["mes_id", "mes_label"], how="left"
        )
        foco_df["participacao_pct"] = (
            foco_df[col_q4] / foco_df["montante_geral_mes"] * 100.0
        ).fillna(0.0)

        total_geral_sem = float(totais_mes["montante_geral_mes"].sum())
        cols_kpi_q4 = st.columns(min(4, len(funcoes_foco) + 1))
        for idx, fn_name in enumerate(funcoes_foco[:3]):
            val_fn = float(foco_df[foco_df["nome_funcao"] == fn_name][col_q4].sum())
            pct_fn = (val_fn / total_geral_sem * 100.0) if total_geral_sem > 0 else 0.0
            cols_kpi_q4[idx].metric(
                f"🏛️ {fn_name} (Semestre)",
                fmt_brl_compact(val_fn),
                f"{fmt_pct(pct_fn)} do Montante Geral",
                help=fmt_brl(val_fn),
            )
        soma_todas_foco = float(foco_df[col_q4].sum())
        cols_kpi_q4[-1].metric(
            "🎯 Soma das Áreas Selecionadas",
            fmt_brl_compact(soma_todas_foco),
            f"{fmt_pct((soma_todas_foco / total_geral_sem * 100) if total_geral_sem > 0 else 0)} do Total Geral",
            help=fmt_brl(soma_todas_foco),
        )

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            fig_q4_vol = px.bar(
                foco_df,
                x="mes_label",
                y=col_q4,
                color="nome_funcao",
                barmode="group",
                text=[fmt_brl_compact(v) for v in foco_df[col_q4]],
                labels={
                    "mes_label": "Mês (2025)",
                    col_q4: q4_metrica,
                    "nome_funcao": "Função Orçamentária",
                },
                title=f"Evolução Mensal do Volume ({q4_metrica}) por Função Prioritária",
            )
            fig_q4_vol.update_layout(height=430)
            st.plotly_chart(fig_q4_vol, width="stretch")

        with g_col2:
            fig_q4_pct = px.line(
                foco_df,
                x="mes_label",
                y="participacao_pct",
                color="nome_funcao",
                markers=True,
                text=[f"{v:.1f}%" for v in foco_df["participacao_pct"]],
                labels={
                    "mes_label": "Mês (2025)",
                    "participacao_pct": "Participação sobre o Total Geral (%)",
                    "nome_funcao": "Função Orçamentária",
                },
                title="Participação Percentual (%) sobre o Montante Geral do Mês",
            )
            fig_q4_pct.update_traces(textposition="top center", line=dict(width=3), marker=dict(size=9))
            fig_q4_pct.update_layout(height=430)
            st.plotly_chart(fig_q4_pct, width="stretch")

        q4_disp = foco_df[
            [
                "mes_label",
                "nome_funcao",
                "valor_empenhado",
                "valor_liquidado",
                "valor_pago",
                "montante_geral_mes",
                "participacao_pct",
            ]
        ].copy()
        q4_disp.columns = [
            "Mês",
            "Função Prioritária",
            "Empenhado na Função (R$)",
            "Liquidado na Função (R$)",
            "Pago na Função (R$)",
            f"Montante Geral do Mês ({q4_metrica})",
            "% sobre Montante Geral",
        ]
        st.dataframe(
            q4_disp.style.format(
                {
                    "Empenhado na Função (R$)": "R$ {:,.2f}",
                    "Liquidado na Função (R$)": "R$ {:,.2f}",
                    "Pago na Função (R$)": "R$ {:,.2f}",
                    f"Montante Geral do Mês ({q4_metrica})": "R$ {:,.2f}",
                    "% sobre Montante Geral": "{:.2f}%",
                },
                thousands=".",
                decimal=",",
            ),
            width="stretch",
            hide_index=True,
        )

        with st.expander("🔍 Ver Consulta SQL executada no Data Warehouse"):
            st.code(q4_sql, language="sql")


# ------------------------------------------------------------------------------
# ABA 5: RISCO FISCAL E RETENÇÃO DE RESTOS A PAGAR
# ------------------------------------------------------------------------------
with tabs[4]:
    st.subheader("5. Risco Fiscal e Retenção de Restos a Pagar")
    st.info(
        "**Pergunta de Negócio:** *Quais órgãos governamentais acumularam os maiores saldos empenhados "
        "e ainda não pagos no semestre e qual o seu índice percentual de execução financeira?*"
    )

    c1, c2, c3, c4 = st.columns([1.8, 1.5, 1.8, 1.5])
    with c1:
        q5_entidade = st.selectbox(
            "Nível de Órgão Governamental:",
            options=[
                "Unidade Gestora (dimUnidadeGestora)",
                "Município / Ente (dimLocal)",
            ],
            index=0,
            key="q5_ent",
        )
    with c2:
        q5_top_n = st.number_input(
            "Quantidade de Órgãos (Top N):",
            min_value=1,
            max_value=500,
            value=int(top_n_default),
            step=5,
            key="q5_topn",
        )
    with c3:
        q5_ordem = st.selectbox(
            "Ordenar Ranking por:",
            options=[
                "Maior Saldo Empenhado Não Pago (R$)",
                "Maior Passivo Liquidado Não Pago (R$)",
                "Menor Índice de Execução Financeira (%)",
            ],
            index=0,
            key="q5_ord",
        )
    with c4:
        q5_max_exec = st.slider(
            "Filtrar Execução Financeira Máxima (%):",
            min_value=5,
            max_value=100,
            value=100,
            step=5,
            help="Permite filtrar apenas órgãos com baixa execução financeira (ex: <= 70%).",
            key="q5_max_exec",
        )

    if q5_entidade.startswith("Unidade Gestora"):
        req_dims_q5 = ["ug", "loc"]
        grp_cols = "ug.codigo_unidade_gestora AS codigo_orgao, ug.nome_unidade_gestora AS nome_orgao, loc.nome_municipio AS municipio_vinculado"
        grp_by = "ug.`key`, ug.codigo_unidade_gestora, ug.nome_unidade_gestora, loc.nome_municipio"
        sent_filter = "AND f.unidadeGestoraKey > 0" if ocultar_sentinelas else ""
    else:
        req_dims_q5 = ["loc"]
        grp_cols = "loc.id_municipio AS codigo_orgao, loc.nome_municipio AS nome_orgao, 'Consolidado Municipal' AS municipio_vinculado"
        grp_by = "loc.`key`, loc.id_municipio, loc.nome_municipio"
        sent_filter = "AND f.localKey > 0" if ocultar_sentinelas else ""

    ord_q5_map = {
        "Maior Saldo Empenhado Não Pago (R$)": "saldo_a_pagar DESC",
        "Maior Passivo Liquidado Não Pago (R$)": "liquidado_nao_pago DESC",
        "Menor Índice de Execução Financeira (%)": "indice_execucao_pct ASC, saldo_a_pagar DESC",
    }

    joins_q5, where_q5, params_q5 = build_star_query_parts(
        required_dims=req_dims_q5,
        meses_sel=meses_sel,
        trimestres_sel=trimestres_sel,
        municipios_sel=municipios_sel,
        categorias_sel=categorias_sel,
        funcoes_sel=funcoes_sel,
        modalidades_sel=modalidades_sel,
    )
    params_q5["max_exec"] = float(q5_max_exec)
    params_q5["limit_n"] = int(q5_top_n)

    q5_sql = f"""
    SELECT
        {grp_cols},
        SUM(f.valorEmpenhado) AS valor_empenhado,
        SUM(f.valorLiquidado) AS valor_liquidado,
        SUM(f.valorPago) AS valor_pago,
        SUM(f.saldoAPagar) AS saldo_a_pagar,
        SUM(f.valorLiquidado - f.valorPago) AS liquidado_nao_pago,
        SUM(f.valorEmpenhado - f.valorLiquidado) AS empenhado_nao_liquidado,
        ROUND(SUM(f.valorPago) / NULLIF(SUM(f.valorEmpenhado), 0) * 100, 2) AS indice_execucao_pct,
        ROUND(SUM(f.saldoAPagar) / NULLIF(SUM(f.valorEmpenhado), 0) * 100, 2) AS indice_retencao_pct
    FROM fatodespesa f
    {joins_q5}
    WHERE {where_q5} {sent_filter}
    GROUP BY {grp_by}
    HAVING valor_empenhado > 0 AND indice_execucao_pct <= :max_exec
    ORDER BY {ord_q5_map[q5_ordem]}
    LIMIT :limit_n
    """
    q5_df = run_query(q5_sql, params_q5)

    if q5_df.empty:
        st.warning("Nenhum órgão encontrado para os parâmetros de risco fiscal informados.")
    else:
        q5_df["orgao_curto"] = q5_df["nome_orgao"].str.slice(0, 42)

        col_r1, col_r2 = st.columns([1.3, 1])
        with col_r1:
            fig_q5_bar = go.Figure()
            fig_q5_bar.add_trace(
                go.Bar(
                    y=q5_df.iloc[::-1]["orgao_curto"],
                    x=q5_df.iloc[::-1]["liquidado_nao_pago"],
                    name="RAP Processado (Liquidado e Não Pago)",
                    orientation="h",
                    marker_color="#d62728",
                )
            )
            fig_q5_bar.add_trace(
                go.Bar(
                    y=q5_df.iloc[::-1]["orgao_curto"],
                    x=q5_df.iloc[::-1]["empenhado_nao_liquidado"],
                    name="RAP Não Processado (Empenhado e Não Liquidado)",
                    orientation="h",
                    marker_color="#ffbb78",
                )
            )
            fig_q5_bar.update_layout(
                barmode="stack",
                title=f"Composição do Saldo a Pagar nos Top {len(q5_df)} Órgãos",
                xaxis_title="Saldo Empenhado Não Pago (R$)",
                yaxis_title="Órgão Governamental",
                height=max(430, min(900, len(q5_df) * 28)),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_q5_bar, width="stretch")

        with col_r2:
            fig_q5_sc = px.scatter(
                q5_df,
                x="indice_execucao_pct",
                y="saldo_a_pagar",
                size="valor_empenhado",
                color="indice_retencao_pct",
                color_continuous_scale="Reds",
                hover_name="nome_orgao",
                hover_data={
                    "municipio_vinculado": True,
                    "valor_empenhado": ":,.2f",
                    "valor_pago": ":,.2f",
                    "saldo_a_pagar": ":,.2f",
                },
                labels={
                    "indice_execucao_pct": "Índice de Execução Financeira (%)",
                    "saldo_a_pagar": "Saldo Total a Pagar (R$)",
                    "indice_retencao_pct": "% Retido",
                },
                title="Matriz de Risco Fiscal: Execução (%) vs. Saldo Retido (R$)",
            )
            fig_q5_sc.update_layout(height=max(430, min(900, len(q5_df) * 28)))
            st.plotly_chart(fig_q5_sc, width="stretch")

        q5_disp = q5_df[
            [
                "codigo_orgao",
                "nome_orgao",
                "municipio_vinculado",
                "valor_empenhado",
                "valor_liquidado",
                "valor_pago",
                "liquidado_nao_pago",
                "empenhado_nao_liquidado",
                "saldo_a_pagar",
                "indice_execucao_pct",
                "indice_retencao_pct",
            ]
        ].copy()
        q5_disp.columns = [
            "Cód.",
            "Órgão Governamental",
            "Município",
            "Total Empenhado (R$)",
            "Total Liquidado (R$)",
            "Total Pago (R$)",
            "Liquidado Não Pago (R$)",
            "Empenhado Não Liq. (R$)",
            "Saldo a Pagar Total (R$)",
            "Execução Financeira (%)",
            "Retenção / Risco (%)",
        ]
        st.dataframe(
            q5_disp.style.format(
                {
                    "Total Empenhado (R$)": "R$ {:,.2f}",
                    "Total Liquidado (R$)": "R$ {:,.2f}",
                    "Total Pago (R$)": "R$ {:,.2f}",
                    "Liquidado Não Pago (R$)": "R$ {:,.2f}",
                    "Empenhado Não Liq. (R$)": "R$ {:,.2f}",
                    "Saldo a Pagar Total (R$)": "R$ {:,.2f}",
                    "Execução Financeira (%)": "{:.2f}%",
                    "Retenção / Risco (%)": "{:.2f}%",
                },
                thousands=".",
                decimal=",",
            ),
            width="stretch",
            hide_index=True,
        )

        with st.expander("🔍 Ver Consulta SQL executada no Data Warehouse"):
            st.code(q5_sql, language="sql")


# ------------------------------------------------------------------------------
# ABA 6: FORNECEDORES COM AMPLA PENETRAÇÃO INTERMUNICIPAL
# ------------------------------------------------------------------------------
with tabs[5]:
    st.subheader("6. Fornecedores com Ampla Penetração Intermunicipal")
    st.info(
        "**Pergunta de Negócio:** *Quais credores prestaram serviços para múltiplos municípios distintos "
        "no estado, evidenciando alta capilaridade de atuação pública?*"
    )

    c1, c2, c3 = st.columns([1.8, 1.5, 2])
    with c1:
        q6_min_mun = st.slider(
            "Mínimo de Municípios Distintos Atendidos:",
            min_value=2,
            max_value=150,
            value=5,
            step=1,
            key="q6_min_mun",
        )
    with c2:
        q6_top_n = st.number_input(
            "Quantidade de Fornecedores (Top N):",
            min_value=1,
            max_value=500,
            value=int(top_n_default),
            step=5,
            key="q6_topn",
        )
    with c3:
        q6_ordem = st.selectbox(
            "Ordenar Capilaridade por:",
            options=[
                "Maior Nº de Municípios Distintos",
                "Maior Volume Total Pago (R$)",
                "Maior Média Paga por Município (R$)",
            ],
            index=0,
            key="q6_ord",
        )

    ord_q6_map = {
        "Maior Nº de Municípios Distintos": "municipios_distintos DESC, valor_pago DESC",
        "Maior Volume Total Pago (R$)": "valor_pago DESC, municipios_distintos DESC",
        "Maior Média Paga por Município (R$)": "media_paga_por_municipio DESC",
    }

    joins_q6, where_q6, params_q6 = build_star_query_parts(
        required_dims=[],
        meses_sel=meses_sel,
        trimestres_sel=trimestres_sel,
        municipios_sel=municipios_sel,
        categorias_sel=categorias_sel,
        funcoes_sel=funcoes_sel,
        modalidades_sel=modalidades_sel,
    )
    params_q6["min_mun"] = int(q6_min_mun)
    params_q6["limit_n"] = int(q6_top_n)

    q6_sql = f"""
    SELECT
        cr.cpf_cnpj,
        cr.nome_credor,
        agg.municipios_distintos,
        agg.cobertura_estadual_pct,
        agg.ugs_distintas,
        agg.valor_empenhado,
        agg.valor_liquidado,
        agg.valor_pago,
        agg.media_paga_por_municipio
    FROM (
        SELECT
            f.credorKey,
            COUNT(DISTINCT NULLIF(f.localKey, 0)) AS municipios_distintos,
            ROUND(COUNT(DISTINCT NULLIF(f.localKey, 0)) / 223.0 * 100, 2) AS cobertura_estadual_pct,
            COUNT(DISTINCT NULLIF(f.unidadeGestoraKey, 0)) AS ugs_distintas,
            SUM(f.valorEmpenhado) AS valor_empenhado,
            SUM(f.valorLiquidado) AS valor_liquidado,
            SUM(f.valorPago) AS valor_pago,
            ROUND(SUM(f.valorPago) / NULLIF(COUNT(DISTINCT NULLIF(f.localKey, 0)), 0), 2) AS media_paga_por_municipio
        FROM fatodespesa f
        {joins_q6}
        WHERE {where_q6} {"AND f.credorKey > 0" if ocultar_sentinelas else ""}
        GROUP BY f.credorKey
        HAVING municipios_distintos >= :min_mun
        ORDER BY {ord_q6_map[q6_ordem]}
        LIMIT :limit_n
    ) agg
    INNER JOIN dimcredor cr ON agg.credorKey = cr.`key`
    ORDER BY {ord_q6_map[q6_ordem]}
    """
    q6_df = run_query(q6_sql, params_q6)

    if q6_df.empty:
        st.warning("Nenhum fornecedor atingiu o número mínimo de municípios selecionado.")
    else:
        q6_df["credor_curto"] = (
            q6_df["nome_credor"].str.slice(0, 36) + " (" + q6_df["municipios_distintos"].astype(str) + " mun.)"
        )

        fig_q6 = px.bar(
            q6_df.iloc[::-1],
            x="municipios_distintos",
            y="credor_curto",
            orientation="h",
            color="valor_pago",
            color_continuous_scale="Tealgrn",
            text=[
                f"{int(r['municipios_distintos'])} mun. ({r['cobertura_estadual_pct']:.1f}% PB) | {fmt_brl_compact(r['valor_pago'])}"
                for _, r in q6_df.iloc[::-1].iterrows()
            ],
            labels={
                "municipios_distintos": "Nº de Municípios Atendidos (de 223)",
                "credor_curto": "Fornecedor",
                "valor_pago": "Total Pago (R$)",
            },
            title=f"Top {len(q6_df)} Fornecedores com Maior Capilaridade Intermunicipal na Paraíba",
        )
        fig_q6.update_layout(height=max(430, min(900, len(q6_df) * 28)))
        st.plotly_chart(fig_q6, width="stretch")

        q6_disp = q6_df[
            [
                "cpf_cnpj",
                "nome_credor",
                "municipios_distintos",
                "cobertura_estadual_pct",
                "ugs_distintas",
                "valor_empenhado",
                "valor_pago",
                "media_paga_por_municipio",
            ]
        ].copy()
        q6_disp.columns = [
            "CPF / CNPJ",
            "Nome do Credor",
            "Municípios Atendidos",
            "Cobertura PB (% de 223)",
            "UGs Distintas",
            "Total Empenhado (R$)",
            "Total Pago (R$)",
            "Média Paga / Município (R$)",
        ]
        st.dataframe(
            q6_disp.style.format(
                {
                    "Municípios Atendidos": "{:,.0f}",
                    "Cobertura PB (% de 223)": "{:.2f}%",
                    "UGs Distintas": "{:,.0f}",
                    "Total Empenhado (R$)": "R$ {:,.2f}",
                    "Total Pago (R$)": "R$ {:,.2f}",
                    "Média Paga / Município (R$)": "R$ {:,.2f}",
                },
                thousands=".",
                decimal=",",
            ),
            width="stretch",
            hide_index=True,
        )

        st.markdown("#### 🔎 Drill-Down: Detalhar Municípios Atendidos por um Fornecedor")
        credor_escolhido = st.selectbox(
            "Selecione um fornecedor da lista acima para listar os municípios onde ele recebeu pagamentos:",
            options=q6_df["cpf_cnpj"].tolist(),
            format_func=lambda doc: f"{q6_df.loc[q6_df['cpf_cnpj'] == doc, 'nome_credor'].values[0]} ({doc})",
            key="q6_drill",
        )
        if credor_escolhido:
            joins_dr, where_dr, params_drill = build_star_query_parts(
                required_dims=["loc", "cr"],
                meses_sel=meses_sel,
                trimestres_sel=trimestres_sel,
                municipios_sel=municipios_sel,
                categorias_sel=categorias_sel,
                funcoes_sel=funcoes_sel,
                modalidades_sel=modalidades_sel,
            )
            params_drill["doc_cr"] = credor_escolhido
            drill_sql = f"""
            SELECT
                loc.nome_municipio AS Municipio,
                COUNT(DISTINCT NULLIF(f.unidadeGestoraKey, 0)) AS UGs,
                SUM(f.valorEmpenhado) AS Empenhado,
                SUM(f.valorPago) AS Pago
            FROM fatodespesa f
            {joins_dr}
            WHERE {where_dr} AND cr.cpf_cnpj = :doc_cr AND loc.`key` > 0
            GROUP BY loc.nome_municipio
            ORDER BY Pago DESC
            """
            drill_df = run_query(drill_sql, params_drill)
            st.dataframe(
                drill_df.style.format(
                    {"UGs": "{:,.0f}", "Empenhado": "R$ {:,.2f}", "Pago": "R$ {:,.2f}"},
                    thousands=".",
                    decimal=",",
                ),
                width="stretch",
                hide_index=True,
            )

        with st.expander("🔍 Ver Consulta SQL executada no Data Warehouse"):
            st.code(q6_sql, language="sql")


# ------------------------------------------------------------------------------
# ABA 7: ANÁLISE DE DISPERSÃO E HIERARQUIA CATEGORIA / NATUREZA (WITH ROLLUP)
# ------------------------------------------------------------------------------
with tabs[6]:
    st.subheader("7. Análise de Dispersão Mensal e Distribuição por Categoria Econômica e Natureza (ROLLUP)")
    st.info(
        "**Pergunta de Negócio:** *Como o total empenhado e pago se distribui entre as categorias econômicas "
        "(despesas correntes e de capital) e os grupos de natureza da despesa, incluindo os subtotais de cada "
        "categoria e o total geral, bem como sua dispersão e valores extremos por mês?*"
    )

    joins_q7_r, where_q7_r, params_q7_r = build_star_query_parts(
        required_dims=["cla"],
        meses_sel=meses_sel,
        trimestres_sel=trimestres_sel,
        municipios_sel=municipios_sel,
        categorias_sel=categorias_sel,
        funcoes_sel=funcoes_sel,
        modalidades_sel=modalidades_sel,
    )

    q7_rollup_sql = f"""
    SELECT
        IF(GROUPING(cla.nome_categoria_economica), 'TOTAL GERAL', cla.nome_categoria_economica) AS categoria_economica,
        IF(
            GROUPING(cla.nome_categoria_economica),
            '— Total Geral Consolidado —',
            IF(GROUPING(cla.nome_natureza_despesa), '▸ SUBTOTAL DA CATEGORIA', cla.nome_natureza_despesa)
        ) AS grupo_natureza,
        GROUPING(cla.nome_categoria_economica) AS is_total_geral,
        GROUPING(cla.nome_natureza_despesa) AS is_subtotal_cat,
        COUNT(*) AS qtd_alocacoes,
        SUM(f.valorEmpenhado) AS total_empenhado,
        SUM(f.valorLiquidado) AS total_liquidado,
        SUM(f.valorPago) AS total_pago,
        SUM(f.saldoAPagar) AS saldo_a_pagar,
        ROUND(AVG(f.valorPago), 2) AS media_alocacao_paga,
        MAX(f.valorPago) AS maior_alocacao_paga
    FROM fatodespesa f
    {joins_q7_r}
    WHERE {where_q7_r} {"AND cla.codigo_categoria_economica > 0" if ocultar_sentinelas else ""}
    GROUP BY cla.nome_categoria_economica, cla.nome_natureza_despesa WITH ROLLUP
    """
    q7_rollup_df = run_query(q7_rollup_sql, params_q7_r)

    joins_q7_m, where_q7_m, params_q7_m = build_star_query_parts(
        required_dims=["dt", "cla"],
        meses_sel=meses_sel,
        trimestres_sel=trimestres_sel,
        municipios_sel=municipios_sel,
        categorias_sel=categorias_sel,
        funcoes_sel=funcoes_sel,
        modalidades_sel=modalidades_sel,
    )

    q7_mes_sql = f"""
    SELECT
        CONCAT(dt.mes_nome, ' - ', dt.mes_texto) AS mes_label,
        cla.nome_categoria_economica AS categoria_economica,
        cla.nome_natureza_despesa AS grupo_natureza,
        SUM(f.valorEmpenhado) AS total_empenhado,
        SUM(f.valorPago) AS total_pago,
        AVG(f.valorPago) AS media_pago,
        MIN(CASE WHEN f.valorPago > 0 THEN f.valorPago END) AS min_pago_positivo,
        MAX(f.valorPago) AS max_pago
    FROM fatodespesa f
    {joins_q7_m}
    WHERE {where_q7_m} AND dt.keyData > 0 {"AND cla.codigo_categoria_economica > 0" if ocultar_sentinelas else ""}
    GROUP BY dt.mes_id, dt.mes_nome, dt.mes_texto, cla.nome_categoria_economica, cla.nome_natureza_despesa
    ORDER BY dt.mes_id ASC
    """
    q7_mes_df = run_query(q7_mes_sql, params_q7_m)

    if q7_rollup_df.empty:
        st.warning("Sem dados para exibir na análise de Categorias e Naturezas.")
    else:
        detalhe_q7 = q7_rollup_df[
            (q7_rollup_df["is_total_geral"] == 0) & (q7_rollup_df["is_subtotal_cat"] == 0)
        ].copy()

        col_t1, col_t2 = st.columns([1.1, 1.2])
        with col_t1:
            fig_q7_sun = px.sunburst(
                detalhe_q7,
                path=["categoria_economica", "grupo_natureza"],
                values="total_pago",
                color="categoria_economica",
                title="Hierarquia Orçamentária: Categoria Econômica ➔ Grupo de Natureza (Valor Pago)",
            )
            fig_q7_sun.update_layout(height=450)
            st.plotly_chart(fig_q7_sun, width="stretch")

        with col_t2:
            if not q7_mes_df.empty:
                fig_q7_box = px.box(
                    q7_mes_df,
                    x="mes_label",
                    y="total_pago",
                    color="categoria_economica",
                    points="all",
                    hover_name="grupo_natureza",
                    labels={
                        "mes_label": "Mês (2025)",
                        "total_pago": "Volume Mensal Pago por Natureza (R$)",
                        "categoria_economica": "Categoria Econômica",
                    },
                    title="Dispersão e Valores Extremos por Mês entre Grupos de Natureza",
                )
                fig_q7_box.update_layout(height=450)
                st.plotly_chart(fig_q7_box, width="stretch")

        st.markdown("#### 📋 Tabela Hierárquica com Subtotais por Categoria e Total Geral (`GROUP BY ... WITH ROLLUP`)")
        total_geral_pag_q7 = float(
            q7_rollup_df.loc[q7_rollup_df["is_total_geral"] == 1, "total_pago"].values[0]
        )

        q7_rollup_df["pct_pago_total"] = (
            q7_rollup_df["total_pago"] / total_geral_pag_q7 * 100.0 if total_geral_pag_q7 > 0 else 0.0
        )
        q7_rollup_df["conversao_pct"] = (
            q7_rollup_df["total_pago"] / q7_rollup_df["total_empenhado"] * 100.0
        ).fillna(0.0)

        q7_disp = q7_rollup_df[
            [
                "categoria_economica",
                "grupo_natureza",
                "qtd_alocacoes",
                "total_empenhado",
                "total_liquidado",
                "total_pago",
                "saldo_a_pagar",
                "conversao_pct",
                "pct_pago_total",
                "maior_alocacao_paga",
            ]
        ].copy()
        q7_disp.columns = [
            "Categoria Econômica",
            "Grupo de Natureza da Despesa",
            "Registros Fato",
            "Total Empenhado (R$)",
            "Total Liquidado (R$)",
            "Total Pago (R$)",
            "Saldo a Pagar (R$)",
            "Conversão Pago/Emp (%)",
            "% do Total Geral Pago",
            "Valor Máximo Alocado (R$)",
        ]

        st.dataframe(
            q7_disp.style.format(
                {
                    "Registros Fato": "{:,.0f}",
                    "Total Empenhado (R$)": "R$ {:,.2f}",
                    "Total Liquidado (R$)": "R$ {:,.2f}",
                    "Total Pago (R$)": "R$ {:,.2f}",
                    "Saldo a Pagar (R$)": "R$ {:,.2f}",
                    "Conversão Pago/Emp (%)": "{:.2f}%",
                    "% do Total Geral Pago": "{:.2f}%",
                    "Valor Máximo Alocado (R$)": "R$ {:,.2f}",
                },
                thousands=".",
                decimal=",",
            ),
            width="stretch",
            hide_index=True,
        )

        with st.expander("🔍 Ver Consultas SQL (`WITH ROLLUP` e Dispersão) executadas no Data Warehouse"):
            st.code(q7_rollup_sql, language="sql")


# ------------------------------------------------------------------------------
# ABA 8: RASTREABILIDADE ORÇAMENTÁRIA (DESPESAS DE CAPITAL: ELEMENTOS X FONTES)
# ------------------------------------------------------------------------------
with tabs[7]:
    st.subheader("8. Rastreabilidade Orçamentária (Despesas de Capital: Elementos x Fontes de Recursos)")
    st.info(
        "**Pergunta de Negócio:** *Nas despesas de capital do 1º semestre de 2025, quais elementos de despesa "
        "concentraram os maiores volumes pagos e quais fontes de recursos os financiaram?*"
    )

    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    with c1:
        q8_cat_foco = st.selectbox(
            "Escopo de Categoria Econômica:",
            options=[
                "Apenas Despesas de Capital (Código 4)",
                "Apenas Despesas Correntes (Código 3)",
                "Todas as Categorias Econômicas",
            ],
            index=0,
            key="q8_cat",
        )
    with c2:
        q8_top_elem = st.number_input(
            "Top N Elementos de Despesa:",
            min_value=1,
            max_value=100,
            value=min(10, int(top_n_default)),
            step=1,
            key="q8_top_el",
        )
    with c3:
        q8_top_fontes = st.number_input(
            "Top N Fontes de Recursos:",
            min_value=1,
            max_value=100,
            value=min(10, int(top_n_default)),
            step=1,
            key="q8_top_fn",
        )

    joins_q8, where_q8, params_q8 = build_star_query_parts(
        required_dims=["cla"],
        meses_sel=meses_sel,
        trimestres_sel=trimestres_sel,
        municipios_sel=municipios_sel,
        categorias_sel=categorias_sel,
        funcoes_sel=funcoes_sel,
        modalidades_sel=modalidades_sel,
        ignore_categoria_filter=True,
    )

    if q8_cat_foco.startswith("Apenas Despesas de Capital"):
        cat_clause_q8 = "AND cla.codigo_categoria_economica = 4"
    elif q8_cat_foco.startswith("Apenas Despesas Correntes"):
        cat_clause_q8 = "AND cla.codigo_categoria_economica = 3"
    else:
        cat_clause_q8 = "AND cla.codigo_categoria_economica > 0" if ocultar_sentinelas else ""

    q8_sql = f"""
    SELECT
        cla.codigo_elemento_despesa,
        cla.nome_elemento_despesa,
        cla.codigo_fonte_recurso,
        cla.nome_fonte_recurso,
        COUNT(*) AS qtd_alocacoes,
        SUM(f.valorEmpenhado) AS valor_empenhado,
        SUM(f.valorLiquidado) AS valor_liquidado,
        SUM(f.valorPago) AS valor_pago
    FROM fatodespesa f
    {joins_q8}
    WHERE {where_q8} {cat_clause_q8}
    GROUP BY
        cla.codigo_elemento_despesa,
        cla.nome_elemento_despesa,
        cla.codigo_fonte_recurso,
        cla.nome_fonte_recurso
    ORDER BY valor_pago DESC
    """
    q8_df = run_query(q8_sql, params_q8)

    if q8_df.empty:
        st.warning("Nenhum registro encontrado para o escopo selecionado.")
    else:
        tot_pago_q8 = float(q8_df["valor_pago"].sum())

        elem_rank = (
            q8_df.groupby(["codigo_elemento_despesa", "nome_elemento_despesa"], as_index=False)[
                ["valor_empenhado", "valor_liquidado", "valor_pago"]
            ]
            .sum()
            .sort_values(by="valor_pago", ascending=False)
            .head(int(q8_top_elem))
        )
        elem_rank["share_pct"] = elem_rank["valor_pago"] / tot_pago_q8 * 100.0 if tot_pago_q8 > 0 else 0.0

        fonte_rank = (
            q8_df.groupby(["codigo_fonte_recurso", "nome_fonte_recurso"], as_index=False)[
                ["valor_empenhado", "valor_liquidado", "valor_pago"]
            ]
            .sum()
            .sort_values(by="valor_pago", ascending=False)
            .head(int(q8_top_fontes))
        )
        fonte_rank["share_pct"] = fonte_rank["valor_pago"] / tot_pago_q8 * 100.0 if tot_pago_q8 > 0 else 0.0

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            fig_q8_el = px.bar(
                elem_rank.iloc[::-1],
                x="valor_pago",
                y="nome_elemento_despesa",
                orientation="h",
                text=[
                    f"{fmt_brl_compact(v)} ({p:.1f}%)"
                    for v, p in zip(elem_rank.iloc[::-1]["valor_pago"], elem_rank.iloc[::-1]["share_pct"])
                ],
                color="valor_pago",
                color_continuous_scale="Blues",
                labels={
                    "valor_pago": "Volume Pago (R$)",
                    "nome_elemento_despesa": "Elemento de Despesa",
                },
                title=f"Top {len(elem_rank)} Elementos de Despesa ({q8_cat_foco})",
            )
            fig_q8_el.update_layout(height=420, coloraxis_showscale=False)
            st.plotly_chart(fig_q8_el, width="stretch")

        with col_e2:
            fonte_rank["fonte_curta"] = fonte_rank["nome_fonte_recurso"].str.slice(0, 42)
            fig_q8_fn = px.bar(
                fonte_rank.iloc[::-1],
                x="valor_pago",
                y="fonte_curta",
                orientation="h",
                text=[
                    f"{fmt_brl_compact(v)} ({p:.1f}%)"
                    for v, p in zip(fonte_rank.iloc[::-1]["valor_pago"], fonte_rank.iloc[::-1]["share_pct"])
                ],
                color="valor_pago",
                color_continuous_scale="Greens",
                labels={
                    "valor_pago": "Volume Pago (R$)",
                    "fonte_curta": "Fonte de Recurso",
                },
                title=f"Top {len(fonte_rank)} Fontes Financiadoras ({q8_cat_foco})",
            )
            fig_q8_fn.update_layout(height=420, coloraxis_showscale=False)
            st.plotly_chart(fig_q8_fn, width="stretch")

        sankey_df = q8_df[
            q8_df["nome_elemento_despesa"].isin(elem_rank["nome_elemento_despesa"])
            & q8_df["nome_fonte_recurso"].isin(fonte_rank["nome_fonte_recurso"])
            & (q8_df["valor_pago"] > 0)
        ].copy()

        if not sankey_df.empty:
            fontes_nodes = [f"Fonte: {n[:40]}" for n in sankey_df["nome_fonte_recurso"].unique()]
            elem_nodes = [f"Elemento: {n[:40]}" for n in sankey_df["nome_elemento_despesa"].unique()]
            all_nodes = fontes_nodes + elem_nodes
            node_idx = {name: i for i, name in enumerate(all_nodes)}

            sources = [node_idx[f"Fonte: {n[:40]}"] for n in sankey_df["nome_fonte_recurso"]]
            targets = [node_idx[f"Elemento: {n[:40]}"] for n in sankey_df["nome_elemento_despesa"]]
            values = sankey_df["valor_pago"].astype(float).tolist()

            fig_sankey = go.Figure(
                data=[
                    go.Sankey(
                        node=dict(
                            pad=15,
                            thickness=18,
                            line=dict(color="black", width=0.5),
                            label=all_nodes,
                        ),
                        link=dict(source=sources, target=targets, value=values),
                    )
                ]
            )
            fig_sankey.update_layout(
                title_text="Fluxo de Rastreabilidade Orçamentária: Fonte de Recurso ➔ Elemento de Despesa (Valor Pago)",
                height=500,
            )
            st.plotly_chart(fig_sankey, width="stretch")

        q8_disp = q8_df.head(max(30, int(top_n_default) * 2)).copy()
        q8_disp["share_pago_pct"] = q8_disp["valor_pago"] / tot_pago_q8 * 100.0 if tot_pago_q8 > 0 else 0.0
        q8_disp = q8_disp[
            [
                "codigo_elemento_despesa",
                "nome_elemento_despesa",
                "codigo_fonte_recurso",
                "nome_fonte_recurso",
                "qtd_alocacoes",
                "valor_empenhado",
                "valor_liquidado",
                "valor_pago",
                "share_pago_pct",
            ]
        ]
        q8_disp.columns = [
            "Cód. Elem.",
            "Elemento de Despesa",
            "Cód. Fonte",
            "Fonte de Recurso Financiadora",
            "Alocações",
            "Valor Empenhado (R$)",
            "Valor Liquidado (R$)",
            "Valor Pago (R$)",
            "% do Pago na Categoria",
        ]
        st.dataframe(
            q8_disp.style.format(
                {
                    "Alocações": "{:,.0f}",
                    "Valor Empenhado (R$)": "R$ {:,.2f}",
                    "Valor Liquidado (R$)": "R$ {:,.2f}",
                    "Valor Pago (R$)": "R$ {:,.2f}",
                    "% do Pago na Categoria": "{:.2f}%",
                },
                thousands=".",
                decimal=",",
            ),
            width="stretch",
            hide_index=True,
        )

        with st.expander("🔍 Ver Consulta SQL executada no Data Warehouse"):
            st.code(q8_sql, language="sql")


# ------------------------------------------------------------------------------
# ABA 9: EXPLORADOR DE CUBO OLAP LIVRE (PIVOT / DICE / DRILL-DOWN CUSTOMIZADO)
# ------------------------------------------------------------------------------
with tabs[8]:
    st.subheader("🧊 Explorador de Cubo OLAP Livre (Cruzamento Multidimensional Dinâmico)")
    st.markdown(
        "Monte sua própria análise OLAP escolhendo livremente qual **Dimensão** colocar nas **Linhas**, "
        "qual **Dimensão** colocar nas **Colunas**, a **Métrica Financeira** e o **Limite de Resultados**."
    )

    dim_meta = {
        "Mês (dimData)": ("dt", "CONCAT(dt.mes_nome, ' - ', dt.mes_texto)"),
        "Trimestre (dimData)": ("dt", "dt.trimestre_texto"),
        "Município (dimLocal)": ("loc", "loc.nome_municipio"),
        "Unidade Gestora (dimUnidadeGestora)": ("ug", "ug.nome_unidade_gestora"),
        "Função Orçamentária (dimClassificacao)": ("cla", "cla.nome_funcao"),
        "Programa de Governo (dimClassificacao)": ("cla", "cla.nome_programa"),
        "Categoria Econômica (dimClassificacao)": ("cla", "cla.nome_categoria_economica"),
        "Grupo de Natureza (dimClassificacao)": ("cla", "cla.nome_natureza_despesa"),
        "Elemento de Despesa (dimClassificacao)": ("cla", "cla.nome_elemento_despesa"),
        "Fonte de Recurso (dimClassificacao)": ("cla", "cla.nome_fonte_recurso"),
        "Modalidade de Licitação (dimLicitacao)": ("lic", "lic.modalidade_licitacao"),
        "Credor (dimCredor)": ("cr", "cr.nome_credor"),
    }

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        dim_linha = st.selectbox("Dimensão nas Linhas:", options=list(dim_meta.keys()), index=4, key="olap_row")
    with c2:
        opcoes_col = ["(Nenhuma — Ranking Simples)"] + [k for k in dim_meta.keys() if k != dim_linha]
        dim_coluna = st.selectbox("Dimensão nas Colunas (Pivot):", options=opcoes_col, index=1, key="olap_col")
    with c3:
        met_olap = st.selectbox(
            "Métrica do Cubo:",
            options=["Valor Pago (R$)", "Valor Empenhado (R$)", "Valor Liquidado (R$)", "Saldo a Pagar (R$)"],
            index=0,
            key="olap_met",
        )
    with c4:
        limite_olap = st.number_input(
            "Limite de Linhas (Top N):",
            min_value=5,
            max_value=300,
            value=20,
            step=5,
            key="olap_lim",
        )

    met_sql_col = {
        "Valor Pago (R$)": "f.valorPago",
        "Valor Empenhado (R$)": "f.valorEmpenhado",
        "Valor Liquidado (R$)": "f.valorLiquidado",
        "Saldo a Pagar (R$)": "f.saldoAPagar",
    }[met_olap]

    row_alias, row_expr = dim_meta[dim_linha]
    if dim_coluna == "(Nenhuma — Ranking Simples)":
        joins_olap, where_olap, params_olap = build_star_query_parts(
            required_dims=[row_alias],
            meses_sel=meses_sel,
            trimestres_sel=trimestres_sel,
            municipios_sel=municipios_sel,
            categorias_sel=categorias_sel,
            funcoes_sel=funcoes_sel,
            modalidades_sel=modalidades_sel,
        )
        olap_sql = f"""
        SELECT
            {row_expr} AS dimensao_linha,
            COUNT(*) AS qtd_alocacoes,
            SUM(f.valorEmpenhado) AS valor_empenhado,
            SUM(f.valorLiquidado) AS valor_liquidado,
            SUM(f.valorPago) AS valor_pago,
            SUM(f.saldoAPagar) AS saldo_a_pagar,
            SUM({met_sql_col}) AS metrica_selecionada
        FROM fatodespesa f
        {joins_olap}
        WHERE {where_olap}
        GROUP BY dimensao_linha
        ORDER BY metrica_selecionada DESC
        LIMIT {int(limite_olap)}
        """
        olap_df = run_query(olap_sql, params_olap)
        fig_olap = px.bar(
            olap_df.iloc[::-1],
            x="metrica_selecionada",
            y="dimensao_linha",
            orientation="h",
            text=[fmt_brl_compact(v) for v in olap_df.iloc[::-1]["metrica_selecionada"]],
            labels={"dimensao_linha": dim_linha, "metrica_selecionada": met_olap},
            title=f"Cubo OLAP: {met_olap} por {dim_linha} (Top {len(olap_df)})",
        )
        fig_olap.update_layout(height=max(420, len(olap_df) * 26))
        st.plotly_chart(fig_olap, width="stretch")
        st.dataframe(olap_df, width="stretch", hide_index=True)
    else:
        col_alias, col_expr = dim_meta[dim_coluna]
        joins_olap, where_olap, params_olap = build_star_query_parts(
            required_dims=[row_alias, col_alias],
            meses_sel=meses_sel,
            trimestres_sel=trimestres_sel,
            municipios_sel=municipios_sel,
            categorias_sel=categorias_sel,
            funcoes_sel=funcoes_sel,
            modalidades_sel=modalidades_sel,
        )
        olap_sql = f"""
        SELECT
            {row_expr} AS dimensao_linha,
            {col_expr} AS dimensao_coluna,
            SUM({met_sql_col}) AS valor_metrica
        FROM fatodespesa f
        {joins_olap}
        WHERE {where_olap}
        GROUP BY dimensao_linha, dimensao_coluna
        ORDER BY valor_metrica DESC
        """
        olap_df = run_query(olap_sql, params_olap)
        if not olap_df.empty:
            top_rows = (
                olap_df.groupby("dimensao_linha")["valor_metrica"]
                .sum()
                .nlargest(int(limite_olap))
                .index.tolist()
            )
            olap_sub = olap_df[olap_df["dimensao_linha"].isin(top_rows)]
            pivot_tb = olap_sub.pivot_table(
                index="dimensao_linha",
                columns="dimensao_coluna",
                values="valor_metrica",
                aggfunc="sum",
                fill_value=0.0,
            )
            pivot_tb["TOTAL LINHA"] = pivot_tb.sum(axis=1)
            pivot_tb = pivot_tb.sort_values(by="TOTAL LINHA", ascending=False)

            fig_heat = px.imshow(
                pivot_tb.drop(columns=["TOTAL LINHA"]),
                aspect="auto",
                color_continuous_scale="YlGnBu",
                labels=dict(x=dim_coluna, y=dim_linha, color=met_olap),
                title=f"Mapa de Calor OLAP (Slice & Dice): {dim_linha} x {dim_coluna} ({met_olap})",
            )
            fig_heat.update_layout(height=500)
            st.plotly_chart(fig_heat, width="stretch")

            st.dataframe(
                pivot_tb.style.format("R$ {:,.2f}", thousands=".", decimal=","),
                width="stretch",
            )
