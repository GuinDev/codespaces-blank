import streamlit as st


def render_products():
    st.set_page_config(page_title="Produtos", layout="wide")
    st.title("Produtos")

    produtos = [
        {"id": 1, "name": "Classic Mug", "price": 12.0, "desc": "Ceramic, 300ml ☕"},
        {"id": 2, "name": "Espresso", "price": 8.5, "desc": "A5, 80 pages 📝"},
        {"id": 3, "name": "Sticker Pack", "price": 4.0,
            "desc": "10 vinyl stickers ✨"},
        {"id": 4, "name": "café com leite", "price": 15.0, "desc": "Cotton, spacious 🛍️"},
    ]

    # initialize cart in session state
    if "cart" not in st.session_state:
        st.session_state.cart = 0

    cols_per_row = 3
    for i in range(0, len(produtos), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, col in enumerate(cols):
            product_index = i + idx
            if product_index >= len(produtos):
                break
            p = produtos[product_index]
            with col:
                st.subheader(p["name"])
                st.write(p["desc"])
                st.write(f"Preço: R${p['price']:.2f}")
                if st.button(f"Adicionar ao carrinho — R${p['price']:.2f}", key=f"buy_{p['id']}"):
                    st.session_state.cart += 1
                    st.success(
                        f"Adicionado {p['name']} ao carrinho (total: {st.session_state.cart})")

    
    left, middle, right = st.columns(3)
    if left.button("Adicionar produto", width="stretch"):
        left.markdown("You clicked the adicionar button.")
    if middle.button("Editar produto", width="stretch"):
        middle.markdown("You clicked the edit button.")
    if right.button("Excluir produto", width="stretch"):
        right.markdown("You clicked the excluir button.") 
