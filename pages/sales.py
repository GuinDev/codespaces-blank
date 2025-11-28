import streamlit as st
import pandas as pd
from sqlalchemy import text
import plotly.express as px
from datetime import date, timedelta

conn = st.connection("postgres", type="sql")


def render_sales():
    st.set_page_config(page_title="Relatórios de Vendas", layout="wide")
    st.title("Relatórios de Vendas")

    # filtros
    today = date.today()
    default_start = today - timedelta(days=30)
    colf1, colf2, colf3 = st.columns([1, 1, 1])
    with colf1:
        start_date = st.date_input("Início", value=default_start)
    with colf2:
        end_date = st.date_input("Fim", value=today)
    with colf3:
        # opções em Português: dia, semana, ano
        gran_choice = st.selectbox("Granularidade", options=["dia", "semana", "ano"], index=0)

    if start_date > end_date:
        st.error("A data de início deve ser anterior ou igual à data final.")
        return

    # mapeamentos: string do usuário -> date_trunc param / pandas resample rule
    gran_to_date_trunc = {"dia": "day", "semana": "week", "ano": "year"}
    gran_to_resample = {"dia": "D", "semana": "W-MON", "ano": "Y"}
    gran_param = gran_to_date_trunc.get(gran_choice, "day")
    resample_rule = gran_to_resample.get(gran_choice, "D")

    # --- consulta: vendas agregadas por período ---
    try:
        with conn.session as session:
            qry_period = text(
                """
                SELECT date_trunc(:gran, data_venda) AT TIME ZONE 'UTC' AS period, COALESCE(SUM(total),0) AS total
                FROM vendas
                WHERE data_venda::date BETWEEN :start AND :end
                GROUP BY period
                ORDER BY period;
                """
            )
            res = session.execute(qry_period, {"gran": gran_param, "start": start_date, "end": end_date})
            df_period = pd.DataFrame(res.mappings().all())

            qry_method = text(
                """
                SELECT metodo_pagamento, COUNT(*) AS vendas, COALESCE(SUM(total),0) AS total
                FROM vendas
                WHERE data_venda::date BETWEEN :start AND :end
                GROUP BY metodo_pagamento;
                """
            )
            res2 = session.execute(qry_method, {"start": start_date, "end": end_date})
            df_method = pd.DataFrame(res2.mappings().all())

            qry_top = text(
                """
                SELECT p.nome AS produto, SUM(iv.quantidade) AS quantidade, SUM(iv.subtotal) AS receita
                FROM itens_venda iv
                JOIN produtos p ON iv.produto_id = p.id
                JOIN vendas v ON iv.venda_id = v.id
                WHERE v.data_venda::date BETWEEN :start AND :end
                GROUP BY p.nome
                ORDER BY receita DESC
                LIMIT 10;
                """
            )
            res3 = session.execute(qry_top, {"start": start_date, "end": end_date})
            df_top = pd.DataFrame(res3.mappings().all())

            qry_recent = text(
                """
                SELECT v.id, v.data_venda, v.total, v.metodo_pagamento,
                       f.nome_completo AS funcionario
                FROM vendas v
                LEFT JOIN funcionarios f ON v.funcionario_id = f.id
                WHERE v.data_venda::date BETWEEN :start AND :end
                ORDER BY v.data_venda DESC
                LIMIT 50;
                """
            )
            res4 = session.execute(qry_recent, {"start": start_date, "end": end_date})
            df_recent = pd.DataFrame(res4.mappings().all())
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    # normalizações de data/colunas
    if not df_period.empty:
        df_period["period"] = pd.to_datetime(df_period["period"])
        # usa a regra de resample correspondente à escolha em português
        df_period = df_period.set_index("period").resample(resample_rule).sum().fillna(0)
    else:
        df_period = pd.DataFrame({"total": []})

    if df_method.empty:
        df_method = pd.DataFrame(columns=["metodo_pagamento", "vendas", "total"])

    if df_top.empty:
        df_top = pd.DataFrame(columns=["produto", "quantidade", "receita"])

    # --- layout: gráficos no topo ---
    gcol1, gcol2 = st.columns([2, 1])

    with gcol1:
        st.subheader("Evolução do faturamento")
        if not df_period.empty and not df_period["total"].empty:
            fig_ts = px.area(df_period, y="total", title="Faturamento ao longo do tempo")
            fig_ts.update_layout(yaxis_title="Total (R$)", xaxis_title="")
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.info("Sem dados de faturamento no período selecionado.")

    with gcol2:
        st.subheader("Método de Pagamento")
        if not df_method.empty:
            fig_pie = px.pie(df_method, names="metodo_pagamento", values="total",
                             title="Receita por método de pagamento", hole=0.35)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem vendas no período para mostrar métodos de pagamento.")

    st.markdown("---")
    # Top produtos e métricas rápidas
    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.subheader("Top produtos (por receita)")
        if not df_top.empty:
            fig_bar = px.bar(df_top, x="produto", y="receita", title="Top produtos (receita)", text="quantidade")
            fig_bar.update_layout(xaxis_title="", yaxis_title="Receita (R$)", uniformtext_minsize=8)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum item vendido no período selecionado.")
    with mcol2:
        # indicadores
        total_revenue = float(df_period["total"].sum()) if "total" in df_period.columns else 0.0
        total_orders = int(df_method["vendas"].sum()) if "vendas" in df_method.columns and not df_method.empty else 0
        total_items = int(df_top["quantidade"].sum()) if "quantidade" in df_top.columns and not df_top.empty else 0
        st.subheader("Resumo")
        st.metric("Receita total (R$)", f"{total_revenue:,.2f}")
        st.metric("Número de vendas", f"{total_orders}")
        st.metric("Itens vendidos", f"{total_items}")

    st.markdown("---")
    # tabela de vendas recentes e CSV export
    st.subheader("Vendas recentes")
    if not df_recent.empty:
        # formata colunas
        df_recent_display = df_recent.copy()
        df_recent_display["data_venda"] = pd.to_datetime(df_recent_display["data_venda"])
        st.dataframe(df_recent_display, use_container_width=True)
        csv = df_recent_display.to_csv(index=False).encode("utf-8")
        st.download_button("Exportar vendas recentes (CSV)", data=csv, file_name="vendas_recentes.csv", mime="text/csv")
    else:
        st.info("Sem vendas recentes no período selecionado.")