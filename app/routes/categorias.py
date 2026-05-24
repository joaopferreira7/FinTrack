from flask import Blueprint, request, jsonify
from app import db
from app.models import Categoria

categorias_bp = Blueprint('categorias', __name__)


@categorias_bp.route('/', methods=['GET'])
def listar_categorias():
    """Lista todas as categorias disponíveis."""
    cats = Categoria.query.order_by(Categoria.nome).all()
    return jsonify([c.to_dict() for c in cats]), 200


@categorias_bp.route('/<int:id>', methods=['GET'])
def obter_categoria(id):
    """Retorna uma categoria pelo ID."""
    cat = Categoria.query.get_or_404(id)
    return jsonify(cat.to_dict()), 200


@categorias_bp.route('/', methods=['POST'])
def criar_categoria():
    """
    Cria uma nova categoria.
    Body JSON: { nome, icone (emoji), cor (hex), limite_mensal }
    """
    data = request.get_json()
    if not data or 'nome' not in data:
        return jsonify({'erro': 'Campo nome é obrigatório'}), 400

    if Categoria.query.filter_by(nome=data['nome']).first():
        return jsonify({'erro': 'Categoria já existe'}), 409

    cat = Categoria(
        nome=data['nome'],
        icone=data.get('icone', '📦'),
        cor=data.get('cor', '#6b7280'),
        limite_mensal=float(data.get('limite_mensal', 0)),
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@categorias_bp.route('/<int:id>', methods=['PUT'])
def atualizar_categoria(id):
    """Atualiza os dados de uma categoria."""
    cat = Categoria.query.get_or_404(id)
    data = request.get_json()

    if 'nome' in data:
        cat.nome = data['nome']
    if 'icone' in data:
        cat.icone = data['icone']
    if 'cor' in data:
        cat.cor = data['cor']
    if 'limite_mensal' in data:
        cat.limite_mensal = float(data['limite_mensal'])

    db.session.commit()
    return jsonify(cat.to_dict()), 200


@categorias_bp.route('/<int:id>', methods=['DELETE'])
def deletar_categoria(id):
    """Remove uma categoria (falha se houver gastos vinculados)."""
    cat = Categoria.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'mensagem': 'Categoria removida'}), 200
