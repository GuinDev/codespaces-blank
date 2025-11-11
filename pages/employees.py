import streamlit as st


def render_employees():
    st.set_page_config(page_title="Funcionarios", layout="wide")
    st.title("Funcionarios")

    funcionarios = [
        {"id": 1, "name": "Ana Silva", "position": "Barista", "telefone": "(11) 91234-5678", "Data de contratação": "2021-03-15"},
        {"id": 2, "name": "Bruno Souza", "position": "Atendente", "telefone": "(11) 92345-6789", "Data de contratação": "2022-05-10"},
        {"id": 3, "name": "Carla Mendes", "position": "Gerente", "telefone": "(11) 93456-7890", "Data de contratação": "2020-11-20"},
        ]
    
    for emp in funcionarios:
        st.subheader(emp["name"])
        st.write(f"Posição: {emp['position']}")
        st.write(f"Telefone: {emp['telefone']}")
        st.write(f"Data de contratação: {emp['Data de contratação']}")
        st.markdown("---")

    left, middle, right = st.columns(3)
    if left.button("Adicionar funcionario", width="stretch"):
        left.markdown("You clicked the adicionar button.")
    if middle.button("Editar funcionario", width="stretch"):
        middle.markdown("You clicked the edit button.")
    if right.button("Excluir funcionario", width="stretch"):
        right.markdown("You clicked the excluir button.")     