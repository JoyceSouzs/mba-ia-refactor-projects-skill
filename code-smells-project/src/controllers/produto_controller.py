import logging
from src.config.settings import VALID_CATEGORIES
from src.models import produto_model

logger = logging.getLogger(__name__)


def _validate_produto(dados, require_all=True):
    required = ["nome", "preco", "estoque"]
    for field in required:
        if require_all and field not in dados:
            return f"{field.capitalize()} é obrigatório"
    if "nome" in dados:
        if len(str(dados["nome"])) < 2:
            return "Nome muito curto"
        if len(str(dados["nome"])) > 200:
            return "Nome muito longo"
    if "preco" in dados and float(dados["preco"]) < 0:
        return "Preço não pode ser negativo"
    if "estoque" in dados and int(dados["estoque"]) < 0:
        return "Estoque não pode ser negativo"
    if "categoria" in dados and dados["categoria"] not in VALID_CATEGORIES:
        return f"Categoria inválida. Válidas: {VALID_CATEGORIES}"
    return None


def listar_produtos():
    produtos = produto_model.get_todos_produtos()
    logger.info("Listando %d produtos", len(produtos))
    return {"dados": produtos, "sucesso": True}, 200


def buscar_produto(produto_id):
    produto = produto_model.get_produto_por_id(produto_id)
    if not produto:
        return {"erro": "Produto não encontrado", "sucesso": False}, 404
    return {"dados": produto, "sucesso": True}, 200


def criar_produto(dados):
    if not dados:
        return {"erro": "Dados inválidos"}, 400
    error = _validate_produto(dados, require_all=True)
    if error:
        return {"erro": error}, 400
    produto_id = produto_model.criar_produto(
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    logger.info("Produto criado: id=%s", produto_id)
    return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201


def atualizar_produto(produto_id, dados):
    if not produto_model.get_produto_por_id(produto_id):
        return {"erro": "Produto não encontrado"}, 404
    if not dados:
        return {"erro": "Dados inválidos"}, 400
    error = _validate_produto(dados, require_all=True)
    if error:
        return {"erro": error}, 400
    produto_model.atualizar_produto(
        produto_id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar_produto(produto_id):
    if not produto_model.get_produto_por_id(produto_id):
        return {"erro": "Produto não encontrado"}, 404
    produto_model.deletar_produto(produto_id)
    logger.info("Produto deletado: id=%s", produto_id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200


def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    resultados = produto_model.buscar_produtos(termo, categoria, preco_min, preco_max)
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
