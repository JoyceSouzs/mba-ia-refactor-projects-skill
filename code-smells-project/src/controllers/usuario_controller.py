import logging
from src.models import usuario_model

logger = logging.getLogger(__name__)


def listar_usuarios():
    usuarios = usuario_model.get_todos_usuarios()
    return {"dados": usuarios, "sucesso": True}, 200


def buscar_usuario(usuario_id):
    usuario = usuario_model.get_usuario_por_id(usuario_id)
    if not usuario:
        return {"erro": "Usuário não encontrado"}, 404
    return {"dados": usuario, "sucesso": True}, 200


def criar_usuario(dados):
    if not dados:
        return {"erro": "Dados inválidos"}, 400
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        return {"erro": "Nome, email e senha são obrigatórios"}, 400
    usuario_id = usuario_model.criar_usuario(nome, email, senha)
    logger.info("Usuário criado: %s", email)
    return {"dados": {"id": usuario_id}, "sucesso": True}, 201


def login(dados):
    if not dados:
        return {"erro": "Dados inválidos"}, 400
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        return {"erro": "Email e senha são obrigatórios"}, 400
    usuario = usuario_model.autenticar_usuario(email, senha)
    if usuario:
        logger.info("Login bem-sucedido: %s", email)
        return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
    logger.warning("Login falhou: %s", email)
    return {"erro": "Email ou senha inválidos", "sucesso": False}, 401
