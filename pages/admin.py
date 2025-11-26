import streamlit as st
from sqlalchemy import text

conn = st.connection("postgres", type="sql")


# ===============================
# FUNCIONÁRIOS
# ===============================
@st.dialog("Adicionar Funcionário")
def add_funcionario_dialog():
    nome = st.text_input("Nome completo")
    cargo = st.selectbox(
        "Cargo",
        options=["gerente", "barista", "caixa", "cozinha", "outro"],
        index=1,
    )
    telefone = st.text_input("Telefone")
    email = st.text_input("Email")
    contratado_em = st.date_input(
        "Data de contratação (opcional)", format="YYYY-MM-DD"
    )

    if st.button("Salvar funcionário"):
        with conn.session as session:
            session.execute(
                text(
                    """
                    INSERT INTO funcionarios
                        (nome_completo, cargo, telefone, email, contratado_em)
                    VALUES
                        (:nome, :cargo, :telefone, :email, :contratado_em)
                    """
                ),
                {
                    "nome": nome,
                    "cargo": cargo,
                    "telefone": telefone or None,
                    "email": email or None,
                    "contratado_em": contratado_em if contratado_em else None,
                },
            )
            session.commit()
        st.success("Funcionário adicionado com sucesso!")
        st.rerun()


@st.dialog("Remover Funcionário")
def remove_funcionario_dialog():
    with conn.session as session:
        result = session.execute(
            text("SELECT id, nome_completo FROM funcionarios ORDER BY nome_completo;")
        )
        funcionarios = result.mappings().all()

    if not funcionarios:
        st.info("Não há funcionários cadastrados.")
        return

    options = {
        f"{f['nome_completo']} (ID: {f['id']})": f["id"] for f in funcionarios
    }
    label = st.selectbox("Selecione o funcionário",
                         options=list(options.keys()))

    if st.button("Remover"):
        funcionario_id = options[label]
        with conn.session as session:
            session.execute(
                text("DELETE FROM funcionarios WHERE id = :id;"),
                {"id": funcionario_id},
            )
            session.commit()
        st.success("Funcionário removido com sucesso!")
        st.rerun()


# ===============================
# PRODUTOS + ESTOQUE
# ===============================
@st.dialog("Adicionar Produto")
def add_produto_dialog():
    with conn.session as session:
        # carregar categorias existentes
        result = session.execute(
            text("SELECT id, nome FROM categorias ORDER BY nome;")
        )
        categorias = result.mappings().all()

    categoria_map = {c["nome"]: c["id"] for c in categorias}
    nome = st.text_input("Nome do produto")
    descricao = st.text_area("Descrição", "")
    sku = st.text_input("SKU (código interno)", "")
    preco = st.number_input("Preço (R$)", min_value=0.0,
                            step=0.5, format="%.2f")

    categoria_nome = st.selectbox(
        "Categoria",
        options=list(categoria_map.keys()) if categoria_map else [],
    )

    quantidade_inicial = st.number_input(
        "Quantidade inicial em estoque",
        min_value=0,
        step=1,
        value=0,
    )
    quantidade_minima = st.number_input(
        "Quantidade mínima (alerta)",
        min_value=0,
        step=1,
        value=0,
    )

    if st.button("Salvar produto"):
        if not nome:
            st.error("O nome do produto é obrigatório.")
            return
        if not categoria_map:
            st.error(
                "Nenhuma categoria cadastrada. Cadastre pelo menos uma categoria.")
            return

        categoria_id = categoria_map.get(categoria_nome)

        with conn.session as session:
            # cria produto
            result = session.execute(
                text(
                    """
                    INSERT INTO produtos (nome, descricao, sku, preco, categoria_id)
                    VALUES (:nome, :descricao, :sku, :preco, :categoria_id)
                    RETURNING id;
                    """
                ),
                {
                    "nome": nome,
                    "descricao": descricao or None,
                    "sku": sku or None,
                    "preco": preco,
                    "categoria_id": categoria_id,
                },
            )
            novo_produto_id = result.scalar_one()

            # cria registro de estoque
            session.execute(
                text(
                    """
                    INSERT INTO estoque (produto_id, quantidade, quantidade_minima)
                    VALUES (:produto_id, :quantidade, :quantidade_minima)
                    ON CONFLICT (produto_id) DO UPDATE
                    SET quantidade = EXCLUDED.quantidade,
                        quantidade_minima = EXCLUDED.quantidade_minima,
                        atualizado_em = now();
                    """
                ),
                {
                    "produto_id": novo_produto_id,
                    "quantidade": int(quantidade_inicial),
                    "quantidade_minima": int(quantidade_minima),
                },
            )
            session.commit()

        st.success("Produto e estoque inicial cadastrados com sucesso!")
        st.rerun()


@st.dialog("Ajustar Estoque")
def ajustar_estoque_dialog():
    # usa view vw_estoque_atual
    with conn.session as session:
        result = session.execute(
            text(
                """
                SELECT produto_id, produto_nome, quantidade
                FROM vw_estoque_atual
                ORDER BY produto_nome;
                """
            )
        )
        itens = result.mappings().all()

    if not itens:
        st.info("Nenhum produto em estoque.")
        return

    options = {
        f"{i['produto_nome']} (Qtd atual: {i['quantidade']})": i["produto_id"]
        for i in itens
    }
    label = st.selectbox("Selecione o produto", options=list(options.keys()))
    qtd_nova = st.number_input(
        "Nova quantidade em estoque", min_value=0, step=1
    )

    if st.button("Salvar ajuste"):
        produto_id = options[label]
        with conn.session as session:
            session.execute(
                text(
                    """
                    UPDATE estoque
                    SET quantidade = :qtd, atualizado_em = now()
                    WHERE produto_id = :produto_id;
                    """
                ),
                {"qtd": int(qtd_nova), "produto_id": produto_id},
            )
            session.commit()
        st.success("Estoque atualizado com sucesso!")
        st.rerun()


def render_admin():
    # Se der erro de set_page_config múltiplo, remova esta linha.
    st.set_page_config(page_title="Administração", layout="wide")
    st.title("Administração da Cafeteria")

    tab_func, tab_prod, tab_estoque = st.tabs(
        ["Funcionários", "Produtos", "Estoque"]
    )

    # --- Aba Funcionários ---
    with tab_func:
        st.subheader("Funcionários cadastrados")

        with conn.session as session:
            result = session.execute(
                text(
                    """
                    SELECT id, nome_completo, cargo, telefone, email,
                           contratado_em, ativo, criado_em
                    FROM funcionarios
                    ORDER BY nome_completo;
                    """
                )
            )
            funcionarios = result.mappings().all()

        if funcionarios:
            st.dataframe(funcionarios, use_container_width=True)
        else:
            st.info("Nenhum funcionário cadastrado.")

        col1, col2 = st.columns(2)
        if col1.button("Adicionar Funcionário"):
            add_funcionario_dialog()
        if col2.button("Remover Funcionário"):
            remove_funcionario_dialog()

    # --- Aba Produtos ---
    with tab_prod:
        st.subheader("Produtos cadastrados")

        with conn.session as session:
            result = session.execute(
                text(
                    """
                    SELECT
                      p.id,
                      p.nome,
                      p.descricao,
                      p.sku,
                      p.preco,
                      c.nome AS categoria,
                      p.ativo,
                      p.criado_em,
                      p.atualizado_em
                    FROM produtos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    ORDER BY p.nome;
                    """
                )
            )
            produtos = result.mappings().all()

        if produtos:
            st.dataframe(produtos, use_container_width=True)
        else:
            st.info("Nenhum produto cadastrado.")

        if st.button("Adicionar Produto"):
            add_produto_dialog()

    # --- Aba Estoque ---
    with tab_estoque:
        st.subheader("Estoque Atual")

        with conn.session as session:
            result = session.execute(
                text(
                    """
                    SELECT
                      produto_id,
                      produto_nome,
                      sku,
                      quantidade,
                      preco,
                      categoria,
                      quantidade_minima
                    FROM vw_estoque_atual
                    ORDER BY produto_nome;
                    """
                )
            )
            estoque = result.mappings().all()

        if estoque:
            st.dataframe(estoque, use_container_width=True)
        else:
            st.info("Nenhum item de estoque cadastrado.")

        if st.button("Ajustar Estoque"):
            ajustar_estoque_dialog()
