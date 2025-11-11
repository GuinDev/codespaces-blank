import streamlit as st


def render_sales():
    st.set_page_config(page_title="Vendas", layout="wide")
    st.title("Vendas")

    produtos = [
        {"id": 1, "name": "Classic Mug", "price": 12.0, "desc": "Ceramic, 300ml ☕", "categoria": "caneca"},
        {"id": 2, "name": "Espresso", "price": 8.5, "desc": "A5, 80 pages 📝", "categoria": "caneca"},
        {"id": 3, "name": "Sticker Pack", "price": 4.0, "desc": "10 vinyl stickers ✨", "categoria": "caneca"},
        {"id": 4, "name": "café com leite", "price": 15.0, "desc": "Cotton, spacious 🛍️", "categoria": "caneca"},
    ]

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
                st.write(f"Categoria: {p['categoria']}")
                if st.button(f"Adicionar ao carrinho — R${p['price']:.2f}", key=f"buy_{p['id']}"):
                    st.session_state.cart += 1
                    st.success(
                        f"Adicionado {p['name']} ao carrinho (total: {st.session_state.cart})")