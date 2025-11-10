import streamlit as st
import os


def render_sidebar():
    with st.sidebar:
        st.title("Example App")
        st.markdown("A simple multi-page Streamlit app template.")

        page = st.radio("Go to", ["Home", "Produtos"])
    return page


def main():

    page = render_sidebar()

    if page == "Home":
        from pages.home import render_home
        render_home()
    elif page == "Produtos":
        from pages.products import render_products
        render_products()
    if "cart" not in st.session_state:
        st.session_state.cart = 0

    st.sidebar.header("Cart")
    st.sidebar.write(f"Items: {st.session_state.cart}")


if __name__ == "__main__":
    main()
