from flask import Blueprint, request, jsonify
from src.controllers import produto_controller, usuario_controller, pedido_controller
from src.config.database import get_db

bp = Blueprint("api", __name__)


# ── Produtos ──────────────────────────────────────────────────────────────────

@bp.route("/produtos", methods=["GET"])
def listar_produtos():
    result, status = produto_controller.listar_produtos()
    return jsonify(result), status


@bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = float(request.args["preco_min"]) if request.args.get("preco_min") else None
    preco_max = float(request.args["preco_max"]) if request.args.get("preco_max") else None
    result, status = produto_controller.buscar_produtos(termo, categoria, preco_min, preco_max)
    return jsonify(result), status


@bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    result, status = produto_controller.buscar_produto(produto_id)
    return jsonify(result), status


@bp.route("/produtos", methods=["POST"])
def criar_produto():
    result, status = produto_controller.criar_produto(request.get_json())
    return jsonify(result), status


@bp.route("/produtos/<int:produto_id>", methods=["PUT"])
def atualizar_produto(produto_id):
    result, status = produto_controller.atualizar_produto(produto_id, request.get_json())
    return jsonify(result), status


@bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
def deletar_produto(produto_id):
    result, status = produto_controller.deletar_produto(produto_id)
    return jsonify(result), status


# ── Usuários ──────────────────────────────────────────────────────────────────

@bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    result, status = usuario_controller.listar_usuarios()
    return jsonify(result), status


@bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    result, status = usuario_controller.buscar_usuario(usuario_id)
    return jsonify(result), status


@bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    result, status = usuario_controller.criar_usuario(request.get_json())
    return jsonify(result), status


@bp.route("/login", methods=["POST"])
def login():
    result, status = usuario_controller.login(request.get_json())
    return jsonify(result), status


# ── Pedidos ───────────────────────────────────────────────────────────────────

@bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    result, status = pedido_controller.criar_pedido(request.get_json())
    return jsonify(result), status


@bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    result, status = pedido_controller.listar_todos_pedidos()
    return jsonify(result), status


@bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    result, status = pedido_controller.listar_pedidos_usuario(usuario_id)
    return jsonify(result), status


@bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    result, status = pedido_controller.atualizar_status_pedido(pedido_id, request.get_json())
    return jsonify(result), status


# ── Relatórios ────────────────────────────────────────────────────────────────

@bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    result, status = pedido_controller.relatorio_vendas()
    return jsonify(result), status


# ── Health ────────────────────────────────────────────────────────────────────

@bp.route("/health", methods=["GET"])
def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) FROM produtos")
        n_produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        n_usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        n_pedidos = cursor.fetchone()[0]
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {"produtos": n_produtos, "usuarios": n_usuarios, "pedidos": n_pedidos},
        }), 200
    except Exception as e:
        return jsonify({"status": "erro", "detalhes": str(e)}), 500


@bp.route("/", methods=["GET"])
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "2.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }), 200
