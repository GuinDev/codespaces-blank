import streamlit as st
from sqlalchemy import text

conn = st.connection("postgres", type="sql")


@st.dialog("Adicionar Usuário")
def add_user_dialog():
    st.write("Formulário para adicionar um novo usuário.")
    name = st.text_input("Nome")
    phone = st.text_input("Telefone")
    email = st.text_input("Email")
    if st.button("Adicionar"):
        with conn.session as session:
            session.execute(
                text(
                    "INSERT INTO people (name, phone, email) VALUES (:name, :phone, :email);"
                ),
                {"name": name, "phone": phone, "email": email},
            )
            session.commit()
            # Refresh cached list as a list of mappings so we can access by column name
            result = session.execute(text("SELECT * FROM people;"))
            st.session_state.people = result.mappings().all()
        st.success("Usuário adicionado com sucesso!")
        st.rerun()


@st.dialog("Remover Usuário")
def remove_user_dialog():
    # Select box containing user names and their IDs
    user_options = {
        f"{user['name']} (ID: {user['id']})": user['id']
        for user in st.session_state.get('people', [])
    }
    selected_user = st.selectbox(
        "Selecione o usuário para remover", options=list(user_options.keys()))
    if st.button("Remover"):
        remove_user(user_options[selected_user])
        st.rerun()


def remove_user(user_id):
    with conn.session as session:
        session.execute(
            text("DELETE FROM people WHERE id = :id;"),
            {"id": user_id},
        )
        session.commit()
        # Refresh cached list as mappings so we can index by column name
        result = session.execute(text("SELECT * FROM people;"))
        st.session_state.people = result.mappings().all()
    st.success("Usuário removido com sucesso!")
    st.rerun()


def render_admin():
    # Always refresh (or do it conditionally if performance matters)
    with conn.session as session:
        result = session.execute(text("SELECT * FROM people;"))
        st.session_state.people = result.mappings().all()

    st.set_page_config(page_title="Administração", layout="wide")
    st.title("Administração")
    st.write("Bem-vindo ao painel de administração. Aqui você pode gerenciar produtos, visualizar estatísticas e configurar o sistema.")

    st.subheader("Usuários")
    st.dataframe(st.session_state['people'])

    st.button("Adicionar Usuário", on_click=add_user_dialog)
    st.button("Remover Usuário", on_click=remove_user_dialog)
