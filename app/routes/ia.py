import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Gasto, Categoria

ia_bp = Blueprint('ia', __name__)

GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL   = 'llama-3.3-70b-versatile'


def _chamar_groq(messages: list, max_tokens: int = 1000) -> str:
    """Chama a API do Groq e retorna a resposta em texto."""
    api_key = current_app.config.get('GROQ_API_KEY', '')
    if not api_key:
        return "⚠️ Configure a variável GROQ_API_KEY no arquivo .env para usar análises com IA."

    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            json={
                "model": GROQ_MODEL,
                "max_tokens": max_tokens,
                "messages": messages,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except requests.HTTPError as e:
        return f"Erro HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"Erro ao contatar a IA: {str(e)}"


def _montar_contexto_financeiro(mes: int, ano: int) -> dict:
    """Monta resumo financeiro do mês para contextualizar a IA."""
    gastos = Gasto.query.filter(
        db.extract('month', Gasto.data) == mes,
        db.extract('year',  Gasto.data) == ano,
    ).all()

    total = sum(g.valor for g in gastos)
    por_cat = {}
    for g in gastos:
        nome = g.categoria.nome
        por_cat[nome] = por_cat.get(nome, 0) + g.valor

    categorias_texto = '\n'.join(
        f"  - {nome}: R${valor:.2f} ({valor/total*100:.1f}%)"
        for nome, valor in sorted(por_cat.items(), key=lambda x: -x[1])
    ) if total > 0 else "  Nenhum gasto registrado."

    limites = {c.nome: c.limite_mensal for c in Categoria.query.all() if c.limite_mensal > 0}
    alertas = []
    for nome, valor in por_cat.items():
        if nome in limites and limites[nome] > 0:
            pct = valor / limites[nome] * 100
            if pct >= 80:
                alertas.append(f"{nome}: {pct:.0f}% do limite utilizado")

    return {
        'mes': mes, 'ano': ano,
        'total': total,
        'qtd': len(gastos),
        'por_cat_texto': categorias_texto,
        'alertas': alertas,
    }


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

    ctx = _montar_contexto_financeiro(mes, ano)
    if ctx['total'] == 0:
        return jsonify({'analise': 'Nenhum gasto registrado neste mês para analisar.'}), 200

    system_msg = (
        "Você é um consultor financeiro pessoal amigável e direto. "
        "Responda sempre em português brasileiro. Não use markdown excessivo."
    )
    user_msg = f"""Analise os gastos de {mes:02d}/{ano}:

Total gasto: R${ctx['total']:.2f}
Transações: {ctx['qtd']}

Por categoria:
{ctx['por_cat_texto']}

{("Limites próximos ou ultrapassados: " + ", ".join(ctx['alertas'])) if ctx['alertas'] else "Todos os limites sob controle."}

Forneça:
1. Avaliação geral (2-3 frases)
2. Ponto mais preocupante (1-2 frases)
3. 2 dicas práticas para economizar
4. Mensagem motivacional curta"""

    analise = _chamar_groq([
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": user_msg},
    ])
    return jsonify({'analise': analise, 'mes': mes, 'ano': ano}), 200


@ia_bp.route('/dica', methods=['GET'])
def dica_do_dia():
    """Retorna uma dica financeira rápida gerada pela IA."""
    dica = _chamar_groq([{
        "role": "user",
        "content": ("Dê uma dica financeira prática e objetiva em 2-3 frases, "
                    "em português brasileiro informal. Seja criativo e útil.")
    }], max_tokens=300)
    return jsonify({'dica': dica}), 200


@ia_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat interativo com IA financeira.
    Body JSON: {
        mes (int), ano (int),
        historico: [ { role: "user"|"assistant", content: str } ],
        mensagem: str
    }
    """
    body = request.get_json() or {}
    agora = datetime.utcnow()
    mes = body.get('mes', agora.month)
    ano = body.get('ano', agora.year)
    historico = body.get('historico', [])
    mensagem = body.get('mensagem', '').strip()

    if not mensagem:
        return jsonify({'erro': 'Mensagem vazia'}), 400

    ctx = _montar_contexto_financeiro(mes, ano)

    system_msg = f"""Você é o FinBot, assistente financeiro pessoal do FinTrack. \
Responda sempre em português brasileiro de forma clara e amigável. \
Não use markdown excessivo — apenas texto simples com emojis quando adequado.

Contexto financeiro atual do usuário ({mes:02d}/{ano}):
- Total gasto: R${ctx['total']:.2f} em {ctx['qtd']} transações
- Por categoria:
{ctx['por_cat_texto']}
{("- Alertas: " + "; ".join(ctx['alertas'])) if ctx['alertas'] else "- Todos os limites sob controle."}

Responda perguntas sobre finanças pessoais, análise de gastos e dicas de economia."""

    # Montar histórico (máx. 10 turnos para não estourar tokens)
    messages = [{"role": "system", "content": system_msg}]
    for h in historico[-10:]:
        if h.get('role') in ('user', 'assistant') and h.get('content'):
            messages.append({"role": h['role'], "content": h['content']})
    messages.append({"role": "user", "content": mensagem})

    resposta = _chamar_groq(messages, max_tokens=600)
    return jsonify({'resposta': resposta}), 200