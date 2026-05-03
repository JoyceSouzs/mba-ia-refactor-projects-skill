from src.config.database import get_db


def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos")
    return [dict(row) for row in cursor.fetchall()]


def get_produto_por_id(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos WHERE id = ?",
        (produto_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def criar_produto(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar_produto(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE produtos SET nome=?, descricao=?, preco=?, estoque=?, categoria=? WHERE id=?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()
    return True


def deletar_produto(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()
    return True


def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    cursor = db.cursor()
    query = "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]
