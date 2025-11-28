# Café e Prosa — Sistema de PDV e Administração (Streamlit)

Pequena aplicação em Streamlit para gestão de produtos, estoque e vendas de uma cafeteria.  
Inclui: página de vendas (carrinho e finalização), relatórios com gráficos, e painel administrativo.

Principais arquivos
- pages/home.py — Home / imagem
- pages/products.py — Tela de vendas (carrinho, finalização)
- pages/sales.py — Relatórios e gráficos
- pages/admin.py — Cadastro/ajuste de produtos, estoque e funcionários
- cafeteria_db_Version4.sql — esquema e dados iniciais do PostgreSQL

Rápido setup (local)
1. Criar e ativar ambiente virtual:
   - Windows (PowerShell):
     python -m venv .venv
     .venv\Scripts\Activate.ps1

2. Instalar dependências:
   pip install streamlit sqlalchemy psycopg2-binary pandas plotly

Configurar o banco de dados
1. Crie um banco PostgreSQL (ex: `cafeteria`) e execute o script SQL:
   

2. Configure uma conexão chamada `postgres` para a aplicação Streamlit:
   - Se estiver usando Streamlit Cloud / GUI de conexões: crie uma conexão PostgreSQL com o nome `postgres`.
   - Se rodando localmente, garanta que sua aplicação consiga acessar o Postgres (por exemplo, via variável de ambiente ou arquivo de secrets). O código usa `st.connection("postgres", type="sql")`.

Configurar acesso ao Admin
Configurar a chave de administrador (ADMIN_KEY)
- Defina a variável de ambiente `ADMIN_KEY` com uma chave secreta antes de iniciar a aplicação. Substitua `my-secret-admin` por um valor forte e mantenha-o privado.

Exemplos:
- Windows (PowerShell):
```powershell
$env:ADMIN_KEY = "my-secret-admin"
```

- Para acessar a página Admin use a URL: `http://localhost:8501/?page=Admin&token=<ADMIN_KEY>` (substitua `<ADMIN_KEY>` pelo valor real).

Executar a aplicação
- No diretório do projeto:
  streamlit run main.py

Notas úteis
- As vendas são criadas em transação: primeiro é criado o registro em `vendas` e em seguida são inseridos os itens em `itens_venda`. Triggers no DB atualizam total e estoque; se houver estoque insuficiente, a operação aborta.
- Há proteção contra submissões duplicadas no frontend (`venda_in_progress`) para evitar sobrecarga do banco.
- Relatórios (pages/sales.py) trazem série temporal, distribuição por método de pagamento e top produtos com exportação CSV.
- Se quiser personalizar a conexão ao banco, ajuste o método de conexão no código (`st.connection`) ou substitua por uma URL SQLAlchemy conforme sua preferência.

Problemas comuns
- Se estiver recebendo erros de conexão, verifique host/porta/usuário/senha e se o Postgres aceita conexões externas.
- Se o Admin não abre, confirme `ADMIN_KEY` e o token na query string.

Fim.
