from flask import Flask, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import pyodbc
from dotenv import load_dotenv
import os

# Inicializando o Flask
app = Flask(__name__)

# Carregando variáveis de ambiente
load_dotenv()

db_server = os.getenv('SERVER')
db_name = os.getenv('DATABASE_BASELINE')

# Configuração para se conectar ao SQL Server
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'mssql+pyodbc://{db_server}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definindo o modelo da tabela de códigos postais
class CodigoPostal(db.Model):
    __tablename__ = 'codigo_postal_base_consolidado'
    
    # Usando 'codigo_postal_clean' como chave primária
    codigo_postal_clean = db.Column(db.String(100), primary_key=True, unique=True, nullable=False)
    codigo_postal_baseline = db.Column(db.String(100), unique=True, nullable=False)
    concelho = db.Column(db.String(100), nullable=False)
    distrito = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<CodigoPostal {self.codigo_postal_clean}>'

    def to_dict(self):
        return {
            'codigo_postal_clean': self.codigo_postal_clean,
            'codigo_postal_baseline': self.codigo_postal_baseline,
            'concelho': self.concelho,
            'distrito': self.distrito
        }

# Endpoint para retornar todos os códigos postais
@app.route('/codigos_postais', methods=['GET'])
def obter_codigos_postais():
    codigos = CodigoPostal.query.all()
    return jsonify([codigo.to_dict() for codigo in codigos])

@app.route('/codigos_postais/<codigo_postal>', methods=['GET'])
def obter_codigo_postal(codigo_postal):
    
    print(f"Consultando código postal: {codigo_postal}")
    
    codigo = CodigoPostal.query.filter(CodigoPostal.codigo_postal_clean == codigo_postal).first()

    if codigo is None:
        
        codigo = CodigoPostal.query.filter(CodigoPostal.codigo_postal_baseline == codigo_postal).first()

    if codigo is None:
        abort(404)  
    
    return jsonify(codigo.to_dict())


# Página de erro personalizada para quando o código postal não for encontrado
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Código postal não encontrado"}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
