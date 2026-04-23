from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app)

    from app.routes.gastos import gastos_bp
    from app.routes.categorias import categorias_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.ia import ia_bp
    from app.routes.views import views_bp

    app.register_blueprint(gastos_bp, url_prefix='/api/gastos')
    app.register_blueprint(categorias_bp, url_prefix='/api/categorias')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(ia_bp, url_prefix='/api/ia')
    app.register_blueprint(views_bp)

    with app.app_context():
        db.create_all()
        _seed_categorias()

    return app

def _seed_categorias():
    from app.models import Categoria
    if Categoria.query.count() == 0:
        defaults = [
            Categoria(nome='Alimentação',  icone='🍔', cor='#f59e0b', limite_mensal=800.0),
            Categoria(nome='Transporte',   icone='🚗', cor='#3b82f6', limite_mensal=400.0),
            Categoria(nome='Lazer',        icone='🎮', cor='#8b5cf6', limite_mensal=300.0),
            Categoria(nome='Saúde',        icone='💊', cor='#ef4444', limite_mensal=500.0),
            Categoria(nome='Educação',     icone='📚', cor='#06b6d4', limite_mensal=600.0),
            Categoria(nome='Moradia',      icone='🏠', cor='#10b981', limite_mensal=1500.0),
            Categoria(nome='Roupas',       icone='👕', cor='#ec4899', limite_mensal=200.0),
            Categoria(nome='Outros',       icone='📦', cor='#6b7280', limite_mensal=200.0),
        ]
        from app import db
        db.session.add_all(defaults)
        db.session.commit()
