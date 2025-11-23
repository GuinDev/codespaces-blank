import streamlit as st
from sqlalchemy import text

conn = st.connection("postgres", type="sql")

if "df" not in st.session_state:
    with conn.session as session:
        result = session.execute(text("SELECT * FROM people;"))
        rows = result.fetchall()
        if rows:
            import pandas as pd
            st.session_state.df = pd.DataFrame(rows, columns=result.keys())
        else:
            st.session_state.df = None


@st.dialog("Adicionar Usuário")
def add_user_dialog():
    st.write("Formulário para adicionar um novo usuário.")
    name = st.text_input("Nome")
    phone = st.text_input("Telefone")
    email = st.text_input("Email")
    with conn.session as session:
        if st.button("Adicionar"):
            session.execute(
                text(
                    "INSERT INTO people (name, phone, email) VALUES (:name, :phone, :email);"),
                {"name": name, "phone": phone, "email": email}
            )
            session.commit()
            st.success("Usuário adicionado com sucesso!")
            # Refresh the dataframe in session state
            result = session.execute(text("SELECT * FROM people;"))
            rows = result.fetchall()
            if rows:
                import pandas as pd
                st.session_state.df = pd.DataFrame(rows, columns=result.keys())
            else:
                st.session_state.df = None
            st.rerun()


def render_admin():
    st.set_page_config(page_title="Administração", layout="wide")
    st.title("Administração")
    st.write("Bem-vindo ao painel de administração. Aqui você pode gerenciar produtos, visualizar estatísticas e configurar o sistema.")

    # Display users from the database
    st.header("Usuários")
    if st.session_state.df is not None:
        st.dataframe(st.session_state.df)
    else:
        st.info("Nenhum usuário encontrado no banco de dados.")

    st.button("Adicionar Usuário", on_click=add_user_dialog)
