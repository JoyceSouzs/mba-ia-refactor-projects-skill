import sqlite3
from src.config.settings import DATABASE_PATH

_db_connection = None


def get_db():
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        _db_connection.row_factory = sqlite3.Row
        _init_schema(_db_connection)
    return _db_connection


def _init_schema(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL DEFAULT 0,
            categoria TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            total REAL NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    """)
    conn.commit()
    _seed_if_empty(cursor, conn)


def _seed_if_empty(cursor, conn):
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] > 0:
        return

    from werkzeug.security import generate_password_hash
    produtos = [
        ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
        ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
        ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
        ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
        ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
        ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
        ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
        ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
        ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
        ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
    ]
    cursor.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        produtos,
    )
    usuarios = [
        ("Admin", "admin@loja.com", generate_password_hash("admin123"), "admin"),
        ("João Silva", "joao@email.com", generate_password_hash("123456"), "cliente"),
        ("Maria Santos", "maria@email.com", generate_password_hash("senha123"), "cliente"),
    ]
    cursor.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        usuarios,
    )
    conn.commit()
