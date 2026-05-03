import logging
from src.config.settings import VALID_ORDER_STATUSES
from src.models import pedido_model

logger = logging.getLogger(__name__)


def criar_pedido(dados):
    if not dados:
        return {"erro": "Dados inválidos"}, 400
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return {"erro": "Usuario ID é obrigatório"}, 400
    if not itens:
        return {"erro": "Pedido deve ter pelo menos 1 item"}, 400
    resultado = pedido_model.criar_pedido(usuario_id, itens)
    if "erro" in resultado:
        return {"erro": resultado["erro"], "sucesso": False}, 400
    logger.info("Pedido criado: id=%s usuario=%s", resultado["pedido_id"], usuario_id)
    return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_model.get_pedidos_usuario(usuario_id)
    return {"dados": pedidos, "sucesso": True}, 200


def listar_todos_pedidos():
    pedidos = pedido_model.get_todos_pedidos()
    return {"dados": pedidos, "sucesso": True}, 200


def atualizar_status_pedido(pedido_id, dados):
    if not dados:
        return {"erro": "Dados inválidos"}, 400
    novo_status = dados.get("status", "")
    if novo_status not in VALID_ORDER_STATUSES:
        return {"erro": f"Status inválido. Válidos: {VALID_ORDER_STATUSES}"}, 400
    pedido_model.atualizar_status_pedido(pedido_id, novo_status)
    logger.info("Status do pedido %s atualizado para %s", pedido_id, novo_status)
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200


def relatorio_vendas():
    relatorio = pedido_model.relatorio_vendas()
    return {"dados": relatorio, "sucesso": True}, 200
