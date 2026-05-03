from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import datetime
from utils.helpers import is_overdue


def _task_to_dict_with_overdue(task):
    """Serializa task incluindo campo overdue e nomes relacionados."""
    data = {}
    data['id'] = task.id
    data['title'] = task.title
    data['description'] = task.description
    data['status'] = task.status
    data['priority'] = task.priority
    data['user_id'] = task.user_id
    data['category_id'] = task.category_id
    data['created_at'] = str(task.created_at)
    data['updated_at'] = str(task.updated_at)
    data['due_date'] = str(task.due_date) if task.due_date else None
    data['tags'] = task.tags.split(',') if task.tags else []
    data['overdue'] = is_overdue(task)

    if task.user_id:
        user = User.query.get(task.user_id)
        data['user_name'] = user.name if user else None
    else:
        data['user_name'] = None

    if task.category_id:
        cat = Category.query.get(task.category_id)
        data['category_name'] = cat.name if cat else None
    else:
        data['category_name'] = None

    return data


def get_all_tasks():
    tasks = Task.query.all()
    return [_task_to_dict_with_overdue(t) for t in tasks], 200


def get_task_by_id(task_id):
    task = Task.query.get(task_id)
    if not task:
        return {'error': 'Task não encontrada'}, 404

    data = task.to_dict()
    data['overdue'] = is_overdue(task)
    return data, 200


def create_task(data):
    if not data:
        return {'error': 'Dados inválidos'}, 400

    title = data.get('title')
    if not title:
        return {'error': 'Título é obrigatório'}, 400
    if len(title) < 3:
        return {'error': 'Título muito curto'}, 400
    if len(title) > 200:
        return {'error': 'Título muito longo'}, 400

    status = data.get('status', 'pending')
    if status not in ['pending', 'in_progress', 'done', 'cancelled']:
        return {'error': 'Status inválido'}, 400

    priority = data.get('priority', 3)
    if priority < 1 or priority > 5:
        return {'error': 'Prioridade deve ser entre 1 e 5'}, 400

    user_id = data.get('user_id')
    if user_id:
        if not User.query.get(user_id):
            return {'error': 'Usuário não encontrado'}, 404

    category_id = data.get('category_id')
    if category_id:
        if not Category.query.get(category_id):
            return {'error': 'Categoria não encontrada'}, 404

    task = Task()
    task.title = title
    task.description = data.get('description', '')
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    due_date = data.get('due_date')
    if due_date:
        try:
            task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
        except Exception:
            return {'error': 'Formato de data inválido. Use YYYY-MM-DD'}, 400

    tags = data.get('tags')
    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    try:
        db.session.add(task)
        db.session.commit()
        return task.to_dict(), 201
    except Exception as e:
        db.session.rollback()
        return {'error': 'Erro ao criar task'}, 500


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        return {'error': 'Task não encontrada'}, 404

    if not data:
        return {'error': 'Dados inválidos'}, 400

    if 'title' in data:
        if len(data['title']) < 3:
            return {'error': 'Título muito curto'}, 400
        if len(data['title']) > 200:
            return {'error': 'Título muito longo'}, 400
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        if data['status'] not in ['pending', 'in_progress', 'done', 'cancelled']:
            return {'error': 'Status inválido'}, 400
        task.status = data['status']

    if 'priority' in data:
        if data['priority'] < 1 or data['priority'] > 5:
            return {'error': 'Prioridade deve ser entre 1 e 5'}, 400
        task.priority = data['priority']

    if 'user_id' in data:
        if data['user_id'] and not User.query.get(data['user_id']):
            return {'error': 'Usuário não encontrado'}, 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not Category.query.get(data['category_id']):
            return {'error': 'Categoria não encontrada'}, 404
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except Exception:
                return {'error': 'Formato de data inválido'}, 400
        else:
            task.due_date = None

    if 'tags' in data:
        task.tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']

    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return task.to_dict(), 200
    except Exception:
        db.session.rollback()
        return {'error': 'Erro ao atualizar'}, 500


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return {'error': 'Task não encontrada'}, 404

    try:
        db.session.delete(task)
        db.session.commit()
        return {'message': 'Task deletada com sucesso'}, 200
    except Exception:
        db.session.rollback()
        return {'error': 'Erro ao deletar'}, 500


def search_tasks(query='', status='', priority='', user_id=''):
    tasks_query = Task.query

    if query:
        tasks_query = tasks_query.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )
    if status:
        tasks_query = tasks_query.filter(Task.status == status)
    if priority:
        tasks_query = tasks_query.filter(Task.priority == int(priority))
    if user_id:
        tasks_query = tasks_query.filter(Task.user_id == int(user_id))

    return [t.to_dict() for t in tasks_query.all()], 200


def get_task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = sum(1 for t in Task.query.all() if is_overdue(t))

    stats = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }
    return stats, 200
