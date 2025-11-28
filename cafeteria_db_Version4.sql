-- cafeteria_db.sql
-- Esquema PostgreSQL em Português para o "Sistema de Administração de Cafeteria"
-- Observação: removida a tabela de movimentações de estoque conforme solicitado.
-- Uso: psql -d sua_base -f cafeteria_db.sql

-- ======================================================
-- 1) Tipos enumerados (em Português)
-- ======================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'metodo_pagamento') THEN
    CREATE TYPE metodo_pagamento AS ENUM ('dinheiro', 'cartao', 'misto');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_funcionario') THEN
    CREATE TYPE tipo_funcionario AS ENUM ('gerente', 'barista', 'caixa', 'cozinha', 'outro');
  END IF;
END$$;

-- ======================================================
-- 2) Tabelas principais (nomes e colunas em Português)
--    Usando IDs sequenciais (BIGINT GENERATED AS IDENTITY)
-- ======================================================

-- Funcionários
CREATE TABLE IF NOT EXISTS funcionarios (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  nome_completo TEXT NOT NULL,
  cargo tipo_funcionario NOT NULL DEFAULT 'outro',
  telefone TEXT,
  email TEXT,
  contratado_em DATE,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Categorias de produtos (cafés, chás, alimentos, etc.)
CREATE TABLE IF NOT EXISTS categorias (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  nome TEXT NOT NULL UNIQUE,
  descricao TEXT,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Produtos
CREATE TABLE IF NOT EXISTS produtos (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  nome TEXT NOT NULL,
  descricao TEXT,
  sku TEXT,
  preco NUMERIC(10,2) NOT NULL CHECK (preco >= 0),
  categoria_id BIGINT REFERENCES categorias(id) ON DELETE SET NULL,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
  atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (nome, categoria_id)
);

-- Estoque: tabela que guarda a quantidade atual por produto
CREATE TABLE IF NOT EXISTS estoque (
  produto_id BIGINT PRIMARY KEY REFERENCES produtos(id) ON DELETE CASCADE,
  quantidade INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
  quantidade_minima INTEGER NOT NULL DEFAULT 0 CHECK (quantidade_minima >= 0),
  atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Vendas (cabeçalho)
CREATE TABLE IF NOT EXISTS vendas (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  data_venda TIMESTAMPTZ NOT NULL DEFAULT now(),
  total NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total >= 0),
  metodo_pagamento metodo_pagamento NOT NULL DEFAULT 'dinheiro',
  funcionario_id BIGINT REFERENCES funcionarios(id) ON DELETE SET NULL,
  nota TEXT
);

-- Itens da venda
CREATE TABLE IF NOT EXISTS itens_venda (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  venda_id BIGINT NOT NULL REFERENCES vendas(id) ON DELETE CASCADE,
  produto_id BIGINT NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
  quantidade INTEGER NOT NULL CHECK (quantidade > 0),
  preco_unitario NUMERIC(10,2) NOT NULL CHECK (preco_unitario >= 0),
  subtotal NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0),
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT itens_venda_subtotal_calc CHECK (subtotal = (quantidade * preco_unitario))
);

-- ======================================================
-- 3) Índices para desempenho
-- ======================================================
CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_vendas_funcionario ON vendas(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_itens_venda_venda ON itens_venda(venda_id);

-- ======================================================
-- 4) FUNÇÕES E TRIGGERS (em Português)
--    - Atualiza atualizado_em em produtos
--    - Calcula subtotal ao inserir item de venda
--    - Ao inserir item de venda: atualiza total da venda e diminui estoque (verifica disponibilidade)
--    - Ao deletar item de venda: reverte total da venda e aumenta estoque (restaura)
-- ======================================================

-- Atualiza atualizado_em da tabela produtos ao alterar
CREATE OR REPLACE FUNCTION fn_produtos_atualiza_atualizado_em()
RETURNS trigger AS $$
BEGIN
  NEW.atualizado_em := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_produtos_atualizado_em ON produtos;
CREATE TRIGGER trg_produtos_atualizado_em
  BEFORE UPDATE ON produtos
  FOR EACH ROW
  EXECUTE FUNCTION fn_produtos_atualiza_atualizado_em();

-- BEFORE INSERT: calcula subtotal automaticamente para itens_venda
CREATE OR REPLACE FUNCTION fn_itens_venda_calcula_subtotal()
RETURNS trigger AS $$
BEGIN
  NEW.subtotal := (NEW.quantidade * NEW.preco_unitario);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_itens_venda_before_insert ON itens_venda;
CREATE TRIGGER trg_itens_venda_before_insert
  BEFORE INSERT ON itens_venda
  FOR EACH ROW
  EXECUTE FUNCTION fn_itens_venda_calcula_subtotal();

-- AFTER INSERT: atualiza total em vendas e diminui estoque (verificando disponibilidade)
CREATE OR REPLACE FUNCTION fn_itens_venda_after_insert()
RETURNS trigger AS $$
DECLARE
  estoque_atual INTEGER;
BEGIN
  -- Atualiza total na tabela vendas
  UPDATE vendas
  SET total = COALESCE(total,0) + (NEW.subtotal)
  WHERE id = NEW.venda_id;

  -- Verifica disponibilidade e bloqueia a linha do estoque para evitar condições de corrida
  SELECT quantidade INTO estoque_atual
  FROM estoque
  WHERE produto_id = NEW.produto_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Estoque não cadastrado para o produto %', NEW.produto_id;
  END IF;

  IF estoque_atual < NEW.quantidade THEN
    RAISE EXCEPTION 'Estoque insuficiente para o produto %. Disponível: %, requisitado: %', NEW.produto_id, estoque_atual, NEW.quantidade;
  END IF;

  -- Atualiza estoque
  UPDATE estoque
  SET quantidade = quantidade - NEW.quantidade,
      atualizado_em = now()
  WHERE produto_id = NEW.produto_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_itens_venda_after_insert ON itens_venda;
CREATE TRIGGER trg_itens_venda_after_insert
  AFTER INSERT ON itens_venda
  FOR EACH ROW
  EXECUTE FUNCTION fn_itens_venda_after_insert();

-- AFTER DELETE: reverte total em vendas e aumenta estoque (restaura)
CREATE OR REPLACE FUNCTION fn_itens_venda_after_delete()
RETURNS trigger AS $$
BEGIN
  -- Atualiza total da venda subtraindo o subtotal do item removido
  UPDATE vendas
  SET total = COALESCE(total,0) - (OLD.subtotal)
  WHERE id = OLD.venda_id;

  -- Restaura quantidade no estoque (insere se não existir)
  INSERT INTO estoque (produto_id, quantidade, atualizado_em)
    VALUES (OLD.produto_id, OLD.quantidade, now())
  ON CONFLICT (produto_id)
    DO UPDATE SET quantidade = estoque.quantidade + OLD.quantidade,
                  atualizado_em = now();

  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_itens_venda_after_delete ON itens_venda;
CREATE TRIGGER trg_itens_venda_after_delete
  AFTER DELETE ON itens_venda
  FOR EACH ROW
  EXECUTE FUNCTION fn_itens_venda_after_delete();

-- ======================================================
-- 5) VIEWS ÚTEIS (em Português)
-- ======================================================
CREATE OR REPLACE VIEW vw_estoque_atual AS
SELECT
  p.id AS produto_id,
  p.nome AS produto_nome,
  p.sku,
  COALESCE(e.quantidade, 0) AS quantidade,
  p.preco,
  c.nome AS categoria,
  e.quantidade_minima
FROM produtos p
LEFT JOIN estoque e ON p.id = e.produto_id
LEFT JOIN categorias c ON p.categoria_id = c.id;

-- ======================================================
-- 6) DADOS EXEMPLO (opcional, em Português)
-- ======================================================
-- Categorias
INSERT INTO categorias (nome, descricao)
VALUES
  ('Cafés', 'Variedades de cafés e bebidas à base de café'),
  ('Chás', 'Chás quentes e gelados'),
  ('Alimentos', 'Sanduíches, doces e lanches')
ON CONFLICT (nome) DO NOTHING;

-- Exemplo de produtos (associa por nome da categoria)
INSERT INTO produtos (nome, descricao, sku, preco, categoria_id)
SELECT 'Café Expresso', 'Café expresso simples', 'CAF-ESP-001', 3.50, c.id
FROM categorias c WHERE c.nome = 'Cafés'
ON CONFLICT (nome, categoria_id) DO NOTHING;

INSERT INTO produtos (nome, descricao, sku, preco, categoria_id)
SELECT 'Cappuccino', 'Cappuccino com leite', 'CAF-CAP-001', 6.00, c.id
FROM categorias c WHERE c.nome = 'Cafés'
ON CONFLICT (nome, categoria_id) DO NOTHING;

INSERT INTO produtos (nome, descricao, sku, preco, categoria_id)
SELECT 'Bolo de Chocolate', 'Pedaço de bolo fresco', 'ALM-BOC-001', 4.50, c.id
FROM categorias c WHERE c.nome = 'Alimentos'
ON CONFLICT (nome, categoria_id) DO NOTHING;

-- Exemplo de registro de estoque inicial (opcional)
-- Associa produtos já inseridos e define quantidades iniciais
INSERT INTO estoque (produto_id, quantidade)
SELECT p.id, 50
FROM produtos p
WHERE p.nome IN ('Café Expresso', 'Cappuccino', 'Bolo de Chocolate')
ON CONFLICT (produto_id) DO NOTHING;

-- Exemplo de funcionário
INSERT INTO funcionarios (nome_completo, cargo, telefone, email, contratado_em)
VALUES ('João Silva', 'barista', '+55 11 91234-5678', 'joao@cafeteria.local', '2024-01-10')
ON CONFLICT DO NOTHING;

-- ======================================================
-- 7) Notas e recomendações (em Português)
-- ======================================================
-- - Removi a tabela de movimentações de estoque e suas triggers. O sistema agora atualiza diretamente
--   a tabela "estoque" ao registrar/remover itens em "itens_venda".
-- - Ao inserir um item de venda a trigger verifica disponibilidade e bloqueia a linha do estoque (FOR UPDATE)
--   para evitar condições de corrida. Se o estoque for insuficiente, a trigger lança uma exceção e a transação é abortada.
-- - Ao remover um item de venda a trigger restaura a quantidade no estoque (faz INSERT ON CONFLICT para criar a linha se necessário).
-- - Recomendo que a aplicação faça a criação de vendas (venda + itens) dentro de uma transação única para garantir atomicidade.
-- - Se preferir que a aplicação seja responsável por atualizar o estoque (sem triggers), posso remover também essas triggers.
-- - Se desejar manter histórico de movimentações no futuro, posso recriar uma tabela de histórico separada (movimentacoes_estoque) sem ativá-la por padrão.

-- Fim do arquivo