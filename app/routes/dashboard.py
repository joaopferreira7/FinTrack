from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import Gasto, Categoria, Alerta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/', methods=['GET'])
def resumo():
    """
    Retorna resumo financeiro do mês.
    Query params: mes (int), ano (int)
    """
    agora = datetime.utcnow()
    mes = request.args.get('mes', agora.month, type=int)
    ano = request.args.get('ano', agora.year, type=int)

    gastos_mes = Gasto.query.filter(
        db.extract('month', Gasto.data) == mes,
        db.extract('year',  Gasto.data) == ano,
    ).all()

    total_mes = sum(g.valor for g in gastos_mes)

    # Agrupamento por categoria
    por_categoria = {}
    for g in gastos_mes:
        cat = g.categoria
        if cat.id not in por_categoria:
            por_categoria[cat.id] = {
                'categoria': cat.to_dict(),
                'total': 0,
                'quantidade': 0,
                'percentual': 0,
            }
        por_categoria[cat.id]['total'] += g.valor
        por_categoria[cat.id]['quantidade'] += 1

    for item in por_categoria.values():
        item['percentual'] = round((item['total'] / total_mes * 100), 1) if total_mes > 0 else 0
        item['limite_mensal'] = item['categoria']['limite_mensal']
        item['uso_limite_pct'] = round(
            (item['total'] / item['limite_mensal'] * 100), 1
        ) if item['limite_mensal'] > 0 else 0

    # Gastos por dia (para gráfico de linha)
    por_dia = {}
    for g in gastos_mes:
        dia = g.data.isoformat()
        por_dia[dia] = por_dia.get(dia, 0) + g.valor

    # Alertas não lidos
    alertas_pendentes = Alerta.query.filter_by(lido=False).count()

    return jsonify({
        'mes':               mes,
        'ano':               ano,
        'total_mes':         round(total_mes, 2),
        'quantidade_gastos': len(gastos_mes),
        'por_categoria':     list(por_categoria.values()),
        'por_dia':           [{'data': k, 'total': round(v, 2)} for k, v in sorted(por_dia.items())],
        'alertas_pendentes': alertas_pendentes,
    }), 200


@dashboard_bp.route('/alertas', methods=['GET'])
def listar_alertas():
    """Lista todos os alertas, ordenados do mais recente."""
    alertas = Alerta.query.order_by(Alerta.criado_em.desc()).limit(20).all()
    return jsonify([a.to_dict() for a in alertas]), 200


@dashboard_bp.route('/alertas/<int:id>/lido', methods=['PATCH'])
def marcar_lido(id):
    """Marca um alerta como lido."""
    alerta = Alerta.query.get_or_404(id)
    alerta.lido = True
    db.session.commit()
    return jsonify(alerta.to_dict()), 200


@dashboard_bp.route('/alertas/limpar', methods=['DELETE'])
def limpar_alertas():
    """Remove todos os alertas lidos."""
    Alerta.query.filter_by(lido=True).delete()
    db.session.commit()
    return jsonify({'mensagem': 'Alertas lidos removidos'}), 200
