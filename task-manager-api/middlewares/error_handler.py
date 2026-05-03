from flask import jsonify


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Requisição inválida', 'details': str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Método não permitido'}), 405

    @app.errorhandler(409)
    def conflict(e):
        return jsonify({'error': 'Conflito de dados', 'details': str(e)}), 409

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Erro interno do servidor'}), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        return jsonify({'error': 'Erro inesperado', 'details': str(e)}), 500
