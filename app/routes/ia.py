import json
import urllib.request
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Gasto, Categoria

ia_bp = Blueprint('ia', __name__)


def _chamar_claude(prompt: str) -> str:
    """Chama a API do Claude Sonnet e retorna a resposta em texto."""
    api_key = current_app.config.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return "⚠️ Configure a variável ANTHROPIC_API_KEY para usar análises com IA."

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['content'][0]['text']
    except Exception as e:
        return f"Erro ao contatar a IA: {str(e)}"


@ia_bp.route('/analisar', methods=['POST'])
def analisar_gastos():
    """
    Analisa os gastos do mês com IA e retorna insights personalizados.
    Body JSON: { mes (int), ano (int) }
    """
    body = request.get_json() or {}
    agora = datetime.utcnow()
    mes = body.get('mes', agora.month)
    ano = body.get('ano', agora.year)

    gastos = Gasto.query.filter(
        db.extract('month', Gasto.data) == mes,
        db.extract('year',  Gasto.data) == ano,
    ).all()

    if not gastos:
        return jsonify({'analise': 'Nenhum gasto registrado neste mês para analisar.'}), 200

    total = sum(g.valor for g in gastos)

    por_cat = {}
    for g in gastos:
        nome = g.categoria.nome
        por_cat[nome] = por_cat.get(nome, 0) + g.valor

    categorias_texto = '\n'.join(
        f"  - {nome}: R${valor:.2f} ({valor/total*100:.1f}%)"
        for nome, valor in sorted(por_cat.items(), key=lambda x: -x[1])
    )

    limites = {c.nome: c.limite_mensal for c in Categoria.query.all() if c.limite_mensal > 0}
    alertas_limite = []
    for nome, valor in por_cat.items():
        if nome in limites and limites[nome] > 0:
            pct = valor / limites[nome] * 100
            if pct >= 80:
                alertas_limite.append(f"{nome}: {pct:.0f}% do limite utilizado")

    prompt = f"""Você é um consultor financeiro pessoal amigável e direto. Analise os gastos abaixo e forneça um feedback em português brasileiro.

GASTOS DE {mes:02d}/{ano}:
Total gasto: R${total:.2f}
Quantidade de transações: {len(gastos)}

Por categoria:
{categorias_texto}

{"Limites próximos ou ultrapassados: " + ", ".join(alertas_limite) if alertas_limite else "Todos os limites estão sob controle."}

Forneça:
1. Uma avaliação geral dos gastos (2-3 frases)
2. O ponto mais preocupante (1-2 frases)
3. 2 dicas práticas e específicas para economizar
4. Uma mensagem motivacional curta

Seja direto, use linguagem informal mas profissional. Não use markdown excessivo."""

    analise = _chamar_claude(prompt)
    return jsonify({'analise': analise, 'mes': mes, 'ano': ano}), 200


@ia_bp.route('/dica', methods=['GET'])
def dica_do_dia():
    """Retorna uma dica financeira rápida gerada pela IA."""
    prompt = ("Dê uma dica financeira prática e objetiva em 2-3 frases, "
              "em português brasileiro informal. Seja criativo e útil para o dia a dia.")
    dica = _chamar_claude(prompt)
    return jsonify({'dica': dica}), 200
