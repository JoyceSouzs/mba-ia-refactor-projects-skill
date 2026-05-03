from src.config.database import get_db
from src.config.settings import (
    DISCOUNT_TIER_HIGH, DISCOUNT_TIER_MID, DISCOUNT_TIER_LOW,
    DISCOUNT_RATE_HIGH, DISCOUNT_RATE_MID, DISCOUNT_RATE_LOW,
)


def criar_pedido(usuario_id, itens):
    db = get_db()
    cursor = db.cursor()
    total = 0
    for item in itens:
        cursor.execute("SELECT id, nome, preco, estoque FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        total += produto["preco"] * item["quantidade"]

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        cursor.execute("SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],))
        preco_unit = cursor.fetchone()["preco"]
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], preco_unit),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )
    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def _get_pedido_com_itens(cursor, row):
    pedido = dict(row)
    cursor.execute("""
        SELECT ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome AS produto_nome
        FROM itens_pedido ip
        JOIN produtos pr ON pr.id = ip.produto_id
        WHERE ip.pedido_id = ?
    """, (row["id"],))
    pedido["itens"] = [dict(item) for item in cursor.fetchall()]
    return pedido


def get_pedidos_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    return [_get_pedido_com_itens(db.cursor(), row) for row in cursor.fetchall()]


def get_todos_pedidos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos")
    return [_get_pedido_com_itens(db.cursor(), row) for row in cursor.fetchall()]


def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True


def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    faturamento = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    if faturamento > DISCOUNT_TIER_HIGH:
        desconto = faturamento * DISCOUNT_RATE_HIGH
    elif faturamento > DISCOUNT_TIER_MID:
        desconto = faturamento * DISCOUNT_RATE_MID
    elif faturamento > DISCOUNT_TIER_LOW:
        desconto = faturamento * DISCOUNT_RATE_LOW
    else:
        desconto = 0

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
