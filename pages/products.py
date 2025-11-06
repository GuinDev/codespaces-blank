import streamlit as st


def render_products():
    st.set_page_config(page_title="Products", layout="wide")
    st.title("Products")

    products = [
        {"id": 1, "name": "Classic Mug", "price": 12.0, "desc": "Ceramic, 300ml ☕"},
        {"id": 2, "name": "Notebook", "price": 8.5, "desc": "A5, 80 pages 📝"},
        {"id": 3, "name": "Sticker Pack", "price": 4.0,
            "desc": "10 vinyl stickers ✨"},
        {"id": 4, "name": "Tote Bag", "price": 15.0, "desc": "Cotton, spacious 🛍️"},
    ]

    # initialize cart in session state
    if "cart" not in st.session_state:
        st.session_state.cart = 0

    cols_per_row = 3
    for i in range(0, len(products), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, col in enumerate(cols):
            product_index = i + idx
            if product_index >= len(products):
                break
            p = products[product_index]
            with col:
                st.subheader(p["name"])
                st.write(p["desc"])
                st.write(f"Price: ${p['price']:.2f}")
                if st.button(f"Add to cart — ${p['price']:.2f}", key=f"buy_{p['id']}"):
                    st.session_state.cart += 1
                    st.success(
                        f"Added {p['name']} to cart (total: {st.session_state.cart})")
