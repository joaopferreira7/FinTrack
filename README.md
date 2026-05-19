# FinTrack — Sistema de Controle de Gastos Pessoais

Sistema web para rastreamento e análise de gastos pessoais, com categorização automática, alertas de limite e análise por Inteligência Artificial.

---

## 🚀 Como Rodar

### Com Docker (recomendado)
```bash
# 1. Clone o projeto
git clone <repo>
cd fintrack

# 2. (Opcional) Configure a API do Groq para análises com IA
export GROQ_API_KEY=sua_chave_aqui
# No Windows PowerShell (opcional):
# $env:GROQ_API_KEY="sua_chave_aqui"

# 3. Suba o container
docker compose up --build

# 4. Acesse http://localhost:5000
```

### Sem Docker (desenvolvimento)
```bash
pip install -r requirements.txt
python run.py
```

> Observação: existe um arquivo `.env.example` com as variáveis necessárias. Copie para `.env` e preencha os valores (ex.: `SECRET_KEY`, `DATABASE_URL`, `GROQ_API_KEY`).

---

## 🏗️ Arquitetura

```
fintrack/
├── app/
│   ├── __init__.py         # App factory + seed de categorias
│   ├── models.py           # Entidades: Gasto, Categoria, Alerta
│   └── routes/
│       ├── gastos.py       # CRUD de gastos + alertas automáticos
│       ├── categorias.py   # CRUD de categorias
│       ├── dashboard.py    # Analytics e alertas
│       ├── ia.py           # Integração Groq API (usa GROQ_API_KEY)
│       └── views.py        # Serve o frontend
├── templates/index.html    # SPA responsiva (tema dark fintech)
├── static/js/app.js        # Lógica frontend (Vanilla JS + Chart.js)
├── config.py               # Configurações
├── run.py                  # Entrypoint
├── Dockerfile
└── docker-compose.yml
```

---

## 🗄️ Entidades (Banco de Dados)

### Categoria
| Campo         | Tipo    | Descrição                        |
|---------------|---------|----------------------------------|
| id            | Integer | PK                               |
| nome          | String  | Nome da categoria                |
| icone         | String  | Emoji representativo             |
| cor           | String  | Cor hex para visualizações       |
| limite_mensal | Float   | Teto de gasto mensal (R$)        |

### Gasto
| Campo        | Tipo    | Descrição                        |
|--------------|---------|----------------------------------|
| id           | Integer | PK                               |
| descricao    | String  | Descrição do gasto               |
| valor        | Float   | Valor em R$                      |
| data         | Date    | Data do gasto                    |
| categoria_id | Integer | FK → Categoria                   |

### Alerta
| Campo     | Tipo    | Descrição                         |
|-----------|---------|-----------------------------------|
| id        | Integer | PK                                |
| mensagem  | String  | Texto do alerta                   |
| tipo      | String  | aviso / critico / info            |
| lido      | Boolean | Status de leitura                 |

---

## 📡 API REST — Endpoints

### Gastos `/api/gastos/`

| Método | Endpoint              | Descrição                                |
|--------|-----------------------|------------------------------------------|
| GET    | `/api/gastos/`        | Lista gastos (filtros: mes, ano, cat)    |
| GET    | `/api/gastos/<id>`    | Retorna um gasto                         |
| POST   | `/api/gastos/`        | Cria novo gasto                          |
| PUT    | `/api/gastos/<id>`    | Atualiza gasto                           |
| DELETE | `/api/gastos/<id>`    | Remove gasto                             |

**POST /api/gastos/ — Body:**
```json
{
  "descricao": "Almoço restaurante",
  "valor": 35.90,
  "data": "2026-03-22",
  "categoria_id": 1
}
```

---

### Categorias `/api/categorias/`

| Método | Endpoint                  | Descrição             |
|--------|---------------------------|-----------------------|
| GET    | `/api/categorias/`        | Lista categorias      |
| POST   | `/api/categorias/`        | Cria categoria        |
| PUT    | `/api/categorias/<id>`    | Atualiza categoria    |
| DELETE | `/api/categorias/<id>`    | Remove categoria      |

**POST /api/categorias/ — Body:**
```json
{
  "nome": "Academia",
  "icone": "🏋️",
  "cor": "#f59e0b",
  "limite_mensal": 150.00
}
```

---

### Dashboard `/api/dashboard/`

| Método | Endpoint                           | Descrição                      |
|--------|------------------------------------|--------------------------------|
| GET    | `/api/dashboard/?mes=3&ano=2026`   | Resumo financeiro do mês       |
| GET    | `/api/dashboard/alertas`           | Lista alertas                  |
| PATCH  | `/api/dashboard/alertas/<id>/lido` | Marca alerta como lido         |
| DELETE | `/api/dashboard/alertas/limpar`    | Remove alertas lidos           |

---

### IA `/api/ia/`

| Método | Endpoint          | Descrição                              |
|--------|-------------------|----------------------------------------|
| POST   | `/api/ia/analisar`| Análise dos gastos do mês com Groq     |
| GET    | `/api/ia/dica`    | Dica financeira gerada por IA          |

**POST /api/ia/analisar — Body:**
```json
{ "mes": 3, "ano": 2026 }
```

---

## ⚡ Funcionalidades

- ✅ Registro de gastos com data e categoria
- ✅ 8 categorias padrão (alimentação, transporte, lazer, etc.)
- ✅ Dashboard com gráfico de linha (gastos por dia) e pizza (por categoria)
- ✅ Limites mensais por categoria com barra de progresso
- ✅ **Alertas automáticos** ao atingir 80% e 100% do limite
- ✅ Análise de gastos com **Groq (Llama 3.3)** (dicas e insights personalizados)
- ✅ Interface responsiva (dark theme fintech)
- ✅ Containerização com Docker

---

## 🤖 IA — Como funciona

Ao clicar em **"Analisar Gastos do Mês"**, o sistema:
1. Coleta todos os gastos do mês atual
2. Calcula totais por categoria e percentuais de uso dos limites
3. Envia um prompt estruturado para o **Groq (Llama 3.3)**
4. Exibe na tela: avaliação geral, pontos críticos, dicas práticas e mensagem motivacional

Requer `GROQ_API_KEY` configurada (via variável de ambiente ou `.env`).

---

## 🛠️ Stack Tecnológica

| Camada      | Tecnologia                     |
|-------------|-------------------------------|
| Backend     | Python 3.12 + Flask 3.0       |
| ORM         | SQLAlchemy 2.0                 |
| Banco       | SQLite (dev) / PostgreSQL (prod)|
| IA          | Groq (Llama 3.3, via Groq API)  |
| Frontend    | HTML5 + CSS3 + Vanilla JS      |
| Gráficos    | Chart.js 4                     |
| Container   | Docker + Docker Compose        |
