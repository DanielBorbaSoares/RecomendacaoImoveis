from flask import Flask, render_template, request, redirect, session
import csv
import os
import joblib
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'chave-super-secreta'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Usuário e senha simples
USERNAME = 'admin'
PASSWORD = '1234'

# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != USERNAME or request.form['password'] != PASSWORD:
            error = 'Usuário ou senha incorretos'
        else:
            session['logged_in'] = True
            return redirect('/corretor')
    return render_template('login.html', error=error)

# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

# Proteger rotas
@app.before_request
def require_login():
    if request.endpoint not in ('login', 'static', 'formulariocliente') and not session.get('logged_in'):
        return redirect('/login')

# Página do corretor (cadastrar imóveis)
@app.route('/corretor', methods=['GET', 'POST'])
def corretor():
    if request.method == 'POST':
        tipo = request.form['tipo']
        titulo = request.form['titulo']
        cidade = request.form['cidade']
        bairro = request.form['bairro']
        quartos = request.form['quartos']
        vagas = request.form['vagas']
        area = request.form['area']
        aceita_pets = request.form.get('aceita_pets', 'Não')
        valor_condominio = request.form['valor_condominio']
        valor_aluguel = request.form['valor_aluguel']
        valor_compra = request.form['valor_compra']
        fotos = request.files.getlist('fotos')

        nomes_fotos = []
        for foto in fotos:
            if foto and foto.filename:
                filename = secure_filename(foto.filename)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                nomes_fotos.append(filename)

        with open('imoveis.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if os.path.getsize('imoveis.csv') == 0:
                writer.writerow(['tipo', 'titulo', 'cidade', 'bairro', 'quartos', 'vagas', 'area', 'aceita_pets', 
                                 'valor_condominio', 'valor_aluguel', 'valor_compra', 'fotos'])
            writer.writerow([tipo, titulo, cidade, bairro, quartos, vagas, area, aceita_pets, 
                             valor_condominio, valor_aluguel, valor_compra, ';'.join(nomes_fotos)])
        return redirect('/corretor')

    return render_template('corretor.html')

# Página imóveis cadastrados
@app.route('/imoveiscadastrados')
def imoveiscadastrados():
    imoveis = []
    if os.path.exists('imoveis.csv'):
        with open('imoveis.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                imoveis.append(row)

    venda = [(i, imovel) for i, imovel in enumerate(imoveis) if imovel['tipo'] == 'Venda']
    aluguel = [(i, imovel) for i, imovel in enumerate(imoveis) if imovel['tipo'] == 'Aluguel']

    return render_template('imoveiscadastrados.html', venda=venda, aluguel=aluguel)

# Excluir imóvel
@app.route('/excluir_imovel/<int:index>')
def excluir_imovel(index):
    imoveis = []
    if os.path.exists('imoveis.csv'):
        with open('imoveis.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                imoveis.append(row)

    if 0 <= index < len(imoveis):
        imoveis.pop(index)

    with open('imoveis.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['tipo', 'titulo', 'cidade', 'bairro', 'quartos', 'vagas', 'area', 
                                               'aceita_pets', 'valor_condominio', 'valor_aluguel', 'valor_compra', 'fotos'])
        writer.writeheader()
        writer.writerows(imoveis)

    return redirect('/imoveiscadastrados')

# Formulário cliente (preferências)
@app.route('/formulariocliente', methods=['GET', 'POST'])
def formulariocliente():
    mensagem = None
    recomendados = []

    if request.method == 'POST':
        bairro = request.form['bairro']
        preco_max = float(request.form['preco_max'])
        quartos = int(request.form['quartos'])
        aceita_pets = 'Sim' if request.form.get('aceita_pets') == 'on' else 'Não'

        if os.path.exists('modelo_knn.joblib'):
            modelo = joblib.load('modelo_knn.joblib')
            scaler = joblib.load('scaler_knn.joblib')
            X_columns = joblib.load('X_columns_knn.joblib')

            data_cliente = pd.DataFrame([{
                'bairro': bairro,
                'valor_aluguel': preco_max,
                'quartos': quartos,
                'aceita_pets': aceita_pets
            }])

            data_cliente_encoded = pd.get_dummies(data_cliente).reindex(columns=X_columns, fill_value=0)
            X_cliente_scaled = scaler.transform(data_cliente_encoded)

            pred = modelo.kneighbors(X_cliente_scaled, n_neighbors=3, return_distance=False)

            imoveis = []
            with open('imoveis.csv', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    imoveis.append(row)

            for i in pred[0]:
                if i < len(imoveis):
                    recomendados.append(imoveis[i])

            mensagem = "Imóveis recomendados para você:"
        else:
            mensagem = "Modelo não treinado. Clique em 'Treinar IA' no menu do corretor."

    return render_template('formulariocliente.html', mensagem=mensagem, recomendados=recomendados)

# Treinar o modelo (KNN)
@app.route('/treinar')
def treinar():
    if os.path.exists('imoveis.csv'):
        df = pd.read_csv('imoveis.csv')

        df = df[df['tipo'] == 'Aluguel']

        df['valor_aluguel'] = df['valor_aluguel'].fillna(0).astype(float)
        df['quartos'] = df['quartos'].astype(int)
        df['aceita_pets'] = df['aceita_pets'].fillna('Não')

        X = df[['bairro', 'valor_aluguel', 'quartos', 'aceita_pets']]
        y = df['bairro']

        X_encoded = pd.get_dummies(X)
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_encoded)

        modelo_knn = KNeighborsClassifier(n_neighbors=3)
        modelo_knn.fit(X_scaled, y)

        joblib.dump(modelo_knn, 'modelo_knn.joblib')
        joblib.dump(scaler, 'scaler_knn.joblib')
        joblib.dump(X_encoded.columns.tolist(), 'X_columns_knn.joblib')

        return "<h2>Modelo treinado com sucesso!</h2><a href='/corretor'>Voltar</a>"
    else:
        return "<h2>Não existem imóveis cadastrados ainda.</h2><a href='/corretor'>Voltar</a>"

# Main
if __name__ == '__main__':
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
