import streamlit as st
import pandas as pd
from sqlalchemy import text

conn = st.connection("postgres", type="sql")

# Inicializações de sessão (garantir tipos e flag de proteção contra double-submit)
if "cart" not in st.session_state or not isinstance(st.session_state.get("cart"), list):
    st.session_state.cart = []
if "venda_in_progress" not in st.session_state:
    st.session_state.venda_in_progress = False


@st.dialog("Finalizar Venda")
def finalizar_venda_dialog():
    cart = st.session_state.get("cart", [])
    # Normalize cart to be a list (protect against older code that may have set an int)
    if not isinstance(cart, list):
        st.session_state.cart = []
        cart = []
    if not cart:
        st.info("Carrinho vazio.")
        return

    # Proteção contra submissões concorrentes
    if st.session_state.get("venda_in_progress"):
        st.warning("Uma venda já está sendo processada. Aguarde e tente novamente.")
        return

    metodo = st.selectbox("Método de pagamento", options=["dinheiro", "cartao", "misto"])
    # carregar funcionários para opcionalmente atribuir a venda
    with conn.session as session:
        result = session.execute(text("SELECT id, nome_completo FROM funcionarios ORDER BY nome_completo;"))
        funcionarios = result.mappings().all()
    funcionario_options = {"(Nenhum)": None}
    for f in funcionarios:
        funcionario_options[f"{f['nome_completo']} (ID:{f['id']})"] = f["id"]
    funcionario_label = st.selectbox("Funcionário (opcional)", options=list(funcionario_options.keys()))
    nota = st.text_area("Nota (opcional)")

    if st.button("Confirmar venda"):
        func_id = funcionario_options[funcionario_label]
        # marca que a venda está em processamento para evitar loops/duplicatas
        st.session_state.venda_in_progress = True
        try:
            with conn.session as session:
                # cria venda com total = 0; triggers de itens_venda atualizarão o total
                res = session.execute(
                    text(
                        "INSERT INTO vendas (total, metodo_pagamento, funcionario_id, nota) "
                        "VALUES (0, :metodo, :func_id, :nota) RETURNING id;"
                    ),
                    {"metodo": metodo, "func_id": func_id, "nota": nota or None},
                )
                venda_id = res.scalar_one()

                # insere itens; triggers irão checar estoque e atualizar total
                # iterar sobre uma cópia do carrinho por segurança
                for it in list(cart):
                    session.execute(
                        text(
                            "INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario) "
                            "VALUES (:venda_id, :produto_id, :quantidade, :preco_unitario);"
                        ),
                        {
                            "venda_id": venda_id,
                            "produto_id": it["id"],
                            "quantidade": int(it["qty"]),
                            "preco_unitario": float(it["price"]),
                        },
                    )

                session.commit()

            st.success(f"Venda registrada com sucesso (ID: {venda_id}).")
            # limpa carrinho antes do rerun para evitar re-submissões
            st.session_state.cart = []
            st.rerun()
        except Exception as e:
            # se a trigger lançar erro (estoque insuficiente) a transação será revertida
            st.error(f"Erro ao registrar venda: {e}")
        finally:
            # garante que o lock seja removido mesmo em caso de erro
            st.session_state.venda_in_progress = False


def render_products():
    st.set_page_config(page_title="Vendas", layout="wide")
    st.title("Vendas — Produtos")

    # initialize/normalize cart in session state (ensure it's a list)
    if "cart" not in st.session_state or not isinstance(st.session_state.get("cart"), list):
        st.session_state.cart = []

    # Carregar produtos/estoque via view
    with conn.session as session:
        result = session.execute(
            text(
                """
                SELECT produto_id, produto_nome, sku, quantidade, preco, categoria, quantidade_minima
                FROM vw_estoque_atual
                ORDER BY produto_nome;
                """
            )
        )
        produtos = result.mappings().all()

    cols_per_row = 3
    for i in range(0, len(produtos), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, col in enumerate(cols):
            product_index = i + idx
            if product_index >= len(produtos):
                break
            p = produtos[product_index]
            with col:
                st.subheader(p["produto_nome"])
                st.write(f"SKU: {p['sku']}" if p.get("sku") else "")
                st.write(f"Categoria: {p.get('categoria') or '-'}")
                st.write(f"Preço: R${p['preco']:.2f}")
                st.write(f"Disponível: {p['quantidade']}")
                # quantidade para adicionar (até o disponível)
                max_q = max(int(p["quantidade"]), 1)
                qty = st.number_input(
                    "Qtd",
                    min_value=1,
                    max_value=max_q,
                    value=1,
                    step=1,
                    key=f"qty_{p['produto_id']}",
                )
                if st.button(f"Adicionar ao carrinho — R${p['preco']:.2f}", key=f"buy_{p['produto_id']}"):
                    # use the normalized cart
                    cart = st.session_state.cart
                    # safe lookup for existing item
                    existing = next((c for c in cart if isinstance(c, dict) and c.get("id") == p["produto_id"]), None)
                    if existing:
                        # respeitar limite do estoque
                        new_qty = existing["qty"] + int(qty)
                        if new_qty > p["quantidade"]:
                            st.error("Quantidade solicitada excede o disponível em estoque.")
                        else:
                            existing["qty"] = new_qty
                            st.success(f"Atualizado {p['produto_nome']} no carrinho (qtd: {existing['qty']}).")
                    else:
                        if int(qty) > p["quantidade"]:
                            st.error("Quantidade solicitada excede o disponível em estoque.")
                        else:
                            cart.append(
                                {"id": p["produto_id"], "name": p["produto_nome"], "price": float(p["preco"]), "qty": int(qty)}
                            )
                            st.success(f"Adicionado {p['produto_nome']} ao carrinho.")

    st.divider()
    st.subheader("Carrinho")
    cart = st.session_state.get("cart", [])
    # normalize again before using
    if not isinstance(cart, list):
        st.session_state.cart = []
        cart = []

    if not cart:
        st.info("Carrinho vazio.")
    else:
        # Mostrar resumo do carrinho
        df = pd.DataFrame(
            [
                {
                    "Produto": it["name"],
                    "Quantidade": it["qty"],
                    "Preço unit. (R$)": f"{it['price']:.2f}",
                    "Subtotal (R$)": f"{it['qty'] * it['price']:.2f}",
                }
                for it in cart
            ]
        )
        st.table(df)

        total = sum(it["qty"] * it["price"] for it in cart)
        st.markdown(f"**Total: R${total:.2f}**")

        # Remover item
        options = {f"{it['name']} (qtd: {it['qty']})": idx for idx, it in enumerate(cart)}
        remove_choice = st.selectbox("Remover item", options=list(options.keys()))
        if st.button("Remover item"):
            idx = options[remove_choice]
            removed = st.session_state.cart.pop(idx)
            st.success(f"Removido {removed['name']} do carrinho.")
            st.experimental_rerun()

        # Finalizar venda (abre diálogo)
        if st.button("Finalizar Venda"):
            finalizar_venda_dialog()