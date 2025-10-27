import streamlit as st


def main():

    with st.sidebar:
        st.title("Sidebar Title")
        st.write("This is the sidebar content.")
    import pages.home as home
    home.render_home()


main()
