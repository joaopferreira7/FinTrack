from datetime import datetime
from app import db

class Categoria(db.Model):
    __tablename__ = 'categorias'

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(50), nullable=False, unique=True)
    icone         = db.Column(db.String(10), default='📦')
    cor           = db.Column(db.String(7), default='#6b7280')
    limite_mensal = db.Column(db.Float, default=0.0)
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)

    gastos = db.relationship('Gasto', backref='categoria', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':            self.id,
            'nome':          self.nome,
            'icone':         self.icone,
            'cor':           self.cor,
            'limite_mensal': self.limite_mensal,
        }


class Gasto(db.Model):
    __tablename__ = 'gastos'

    id           = db.Column(db.Integer, primary_key=True)
    descricao    = db.Column(db.String(200), nullable=False)
    valor        = db.Column(db.Float, nullable=False)
    data         = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':            self.id,
            'descricao':     self.descricao,
            'valor':         self.valor,
            'data':          self.data.isoformat(),
            'categoria_id':  self.categoria_id,
            'categoria':     self.categoria.to_dict() if self.categoria else None,
            'criado_em':     self.criado_em.isoformat(),
        }


class Alerta(db.Model):
    __tablename__ = 'alertas'

    id         = db.Column(db.Integer, primary_key=True)
    mensagem   = db.Column(db.String(300), nullable=False)
    tipo       = db.Column(db.String(20), default='aviso')   # aviso | critico | info
    lido       = db.Column(db.Boolean, default=False)
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'mensagem':  self.mensagem,
            'tipo':      self.tipo,
            'lido':      self.lido,
            'criado_em': self.criado_em.isoformat(),
        }
