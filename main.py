import streamlit as st
import os


ALL_PAGES = ["Home", "Produtos", "Funcionarios", "Vendas", "Admin"]

# URL FOR ADMIN: http://localhost:8501/?page=Admin&token=my-secret-admin
# env:ADMIN_KEY="my-secret-admin" in powershell, why is it not working


def render_sidebar():
    # Admin is hidden from the radio options
    visible_pages = [p for p in ALL_PAGES if p != "Admin"]

    with st.sidebar:
        st.title("Café e prosa!")
        st.markdown(
            "Um lugar onde você pode comprar produtos relacionados a café.")
        page = st.radio("Go to", visible_pages)
    return page


def main():
    page = render_sidebar()

    # Use non-experimental API when available, fallback to experimental for older Streamlit versions
    try:
        params = st.get_query_params()
    except AttributeError:
        params = st.experimental_get_query_params()

    # Check URL query params for page override and token for the hidden page
    if "page" in params:
        requested = params["page"][0]
        if requested in ALL_PAGES:
            if requested == "Admin":
                # Only allow access to Admin when token matches ADMIN_KEY env var
                token = params.get("token", [None])[0]
                admin_key = os.environ.get("ADMIN_KEY")
                if admin_key is None:
                    st.error(
                        "ADMIN_KEY environment variable is not set. Admin access is misconfigured.")
                elif token is not None and token == admin_key:
                    page = "Admin"
                else:
                    st.warning("Access denied to hidden page.")
            else:
                page = requested

    # Route to pages
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
    elif page == "Admin":
        from pages.admin import render_admin
        render_admin()

    # Cart state
    if "cart" not in st.session_state:
        st.session_state.cart = 0

    st.sidebar.header("Cart")
    st.sidebar.write(f"Items: {st.session_state.cart}")


if __name__ == "__main__":
    main()
