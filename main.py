import streamlit as st
import os


def render_sidebar():
    with st.sidebar:
        st.title("Café e prosa!")
        st.markdown("Um lugar onde você pode comprar produtos relacionados a café.")

        page = st.radio("Go to", ["Home", "Produtos", "Funcionarios", "Vendas"])
    return page


def main():

    page = render_sidebar()

    if page == "Home":
        from pages.home import render_home
        render_home()
    elif page == "Produtos":
        from pages.products import render_products
        render_products()
    elif page == "Funcionarios":
        from pages.employees import render_employees
        render_employees()
    elif page == "Vendas":
        from pages.sales import render_sales
        render_sales()        
    if "cart" not in st.session_state:
        st.session_state.cart = 0

    st.sidebar.header("Cart")
    st.sidebar.write(f"Items: {st.session_state.cart}")
    

if __name__ == "__main__":
    main()
