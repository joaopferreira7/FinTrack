from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import Gasto, Categoria, Alerta

gastos_bp = Blueprint('gastos', __name__)


@gastos_bp.route('/', methods=['GET'])
def listar_gastos():
    """
    Lista todos os gastos com filtros opcionais.
    Query params: mes (int), ano (int), categoria_id (int)
    """
    query = Gasto.query

    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    categoria_id = request.args.get('categoria_id', type=int)

    if mes:
        query = query.filter(db.extract('month', Gasto.data) == mes)
    if ano:
        query = query.filter(db.extract('year', Gasto.data) == ano)
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)

    gastos = query.order_by(Gasto.data.desc()).all()
    return jsonify([g.to_dict() for g in gastos]), 200


@gastos_bp.route('/<int:id>', methods=['GET'])
def obter_gasto(id):
    """Retorna um gasto específico pelo ID."""
    gasto = Gasto.query.get_or_404(id)
    return jsonify(gasto.to_dict()), 200


@gastos_bp.route('/', methods=['POST'])
def criar_gasto():
    """
    Cria um novo gasto.
    Body JSON: { descricao, valor, data (YYYY-MM-DD), categoria_id }
    """
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados inválidos'}), 400

    campos = ['descricao', 'valor', 'categoria_id']
    for campo in campos:
        if campo not in data:
            return jsonify({'erro': f'Campo obrigatório ausente: {campo}'}), 400

    if not Categoria.query.get(data['categoria_id']):
        return jsonify({'erro': 'Categoria não encontrada'}), 404

    try:
        data_gasto = datetime.strptime(data.get('data', datetime.utcnow().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

    gasto = Gasto(
        descricao=data['descricao'],
        valor=float(data['valor']),
        data=data_gasto,
        categoria_id=data['categoria_id'],
    )
    db.session.add(gasto)
    db.session.commit()

    _verificar_limite(gasto)

    return jsonify(gasto.to_dict()), 201


@gastos_bp.route('/<int:id>', methods=['PUT'])
def atualizar_gasto(id):
    """Atualiza um gasto existente."""
    gasto = Gasto.query.get_or_404(id)
    data = request.get_json()

    if 'descricao' in data:
        gasto.descricao = data['descricao']
    if 'valor' in data:
        gasto.valor = float(data['valor'])
    if 'data' in data:
        try:
            gasto.data = datetime.strptime(data['data'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido'}), 400
    if 'categoria_id' in data:
        if not Categoria.query.get(data['categoria_id']):
            return jsonify({'erro': 'Categoria não encontrada'}), 404
        gasto.categoria_id = data['categoria_id']

    db.session.commit()
    return jsonify(gasto.to_dict()), 200


@gastos_bp.route('/<int:id>', methods=['DELETE'])
def deletar_gasto(id):
    """Remove um gasto pelo ID."""
    gasto = Gasto.query.get_or_404(id)
    db.session.delete(gasto)
    db.session.commit()
    return jsonify({'mensagem': 'Gasto removido com sucesso'}), 200


def _verificar_limite(gasto: Gasto):
    """Gera alertas automáticos quando o limite mensal for ultrapassado."""
    cat = gasto.categoria
    if not cat or cat.limite_mensal <= 0:
        return

    mes = gasto.data.month
    ano = gasto.data.year

    total = db.session.query(db.func.sum(Gasto.valor)).filter(
        Gasto.categoria_id == cat.id,
        db.extract('month', Gasto.data) == mes,
        db.extract('year',  Gasto.data) == ano,
    ).scalar() or 0

    pct = (total / cat.limite_mensal) * 100

    if pct >= 100:
        msg = (f'{cat.icone} Limite ESTOURADO em {cat.nome}! '
               f'Gasto R${total:.2f} de R${cat.limite_mensal:.2f} ({pct:.0f}%)')
        alerta = Alerta(mensagem=msg, tipo='critico')
        db.session.add(alerta)
        db.session.commit()
    elif pct >= 80:
        msg = (f'{cat.icone} Atenção! Você usou {pct:.0f}% do limite de {cat.nome} '
               f'(R${total:.2f} / R${cat.limite_mensal:.2f})')
        alerta = Alerta(mensagem=msg, tipo='aviso')
        db.session.add(alerta)
        db.session.commit()
