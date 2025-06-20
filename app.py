from flask import Flask, render_template, request, redirect
import csv
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Página do corretor
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
        aceita_pets = 'Sim' if request.form.get('aceita_pets') else 'Não'
        valor_condominio = request.form['valor_condominio']
        valor_aluguel = request.form['valor_aluguel']
        valor_compra = request.form['valor_compra']

        fotos = request.files.getlist('fotos')
        foto_nomes = []

        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        for foto in fotos:
            if foto.filename != '':
                filename = secure_filename(foto.filename)
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                foto.save(foto_path)
                foto_nomes.append(filename)

        with open('imoveis.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if os.path.getsize('imoveis.csv') == 0:
                writer.writerow([
                    'tipo', 'titulo', 'cidade', 'bairro', 'quartos', 'vagas',
                    'area', 'aceita_pets', 'valor_condominio',
                    'valor_aluguel', 'valor_compra', 'fotos'
                ])
            writer.writerow([
                tipo, titulo, cidade, bairro, quartos, vagas,
                area, aceita_pets, valor_condominio,
                valor_aluguel, valor_compra, ';'.join(foto_nomes)
            ])

        return redirect('/corretor')

    return render_template('corretor.html')

# Página de visualização dos imóveis cadastrados (Venda / Aluguel)
@app.route('/imoveiscadastrados')
def imoveiscadastrados():
    imoveis = []
    if os.path.exists('imoveis.csv'):
        with open('imoveis.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                imoveis.append(row)

    venda = []
    aluguel = []

    for index, imovel in enumerate(imoveis):
        if imovel['tipo'] == 'Venda':
            venda.append((index, imovel))
        elif imovel['tipo'] == 'Aluguel':
            aluguel.append((index, imovel))

    return render_template('imoveiscadastrados.html', venda=venda, aluguel=aluguel)

# Excluir imóvel
@app.route('/excluir_imovel/<int:index>')
def excluir_imovel(index):
    imoveis = []
    if os.path.exists('imoveis.csv'):
        with open('imoveis.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            imoveis = list(reader)

    if 0 <= index < len(imoveis):
        imoveis.pop(index)
        with open('imoveis.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'tipo', 'titulo', 'cidade', 'bairro', 'quartos', 'vagas',
                'area', 'aceita_pets', 'valor_condominio',
                'valor_aluguel', 'valor_compra', 'fotos'
            ])
            writer.writeheader()
            writer.writerows(imoveis)

    return redirect('/imoveiscadastrados')

# Formulário do cliente + KNN
@app.route('/formulariocliente', methods=['GET', 'POST'])
def formulariocliente():
    recomendacoes = []

    if request.method == 'POST':
        tipo = request.form['tipo']
        cidade = request.form['cidade']
        bairro = request.form['bairro']
        quartos = int(request.form['quartos'])
        vagas = int(request.form['vagas'])
        area = int(request.form['area'])
        aceita_pets = 'Sim' if request.form.get('aceita_pets') else 'Não'

        if os.path.exists('imoveis.csv') and os.path.exists('modelo_knn.joblib'):
            import joblib
            modelo_knn = joblib.load('modelo_knn.joblib')
            scaler = joblib.load('scaler_knn.joblib')
            X_columns = joblib.load('X_columns_knn.joblib')

            df = pd.read_csv('imoveis.csv')
            features = ['quartos', 'vagas', 'area']
            df_encoded = pd.get_dummies(df[['tipo', 'cidade', 'bairro', 'aceita_pets']])
            X = pd.concat([df[features], df_encoded], axis=1)

            input_dict = {
                'quartos': quartos,
                'vagas': vagas,
                'area': area,
                f'tipo_{tipo}': 1,
                f'cidade_{cidade}': 1,
                f'bairro_{bairro}': 1,
                f'aceita_pets_{aceita_pets}': 1
            }

            input_data = []
            for col in X_columns:
                input_data.append(input_dict.get(col, 0))

            input_scaled = scaler.transform([input_data])
            distances, indices = modelo_knn.kneighbors(input_scaled)

            for idx in indices[0]:
                recomendacoes.append(df.iloc[idx])

    return render_template('formulariocliente.html', recomendacoes=recomendacoes)

# Treinar KNN com clique
@app.route('/treinar')
def treinar():
    import pandas as pd
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler
    import joblib

    if not os.path.exists('imoveis.csv'):
        return "<h3>⚠️ Nenhum imóvel cadastrado!</h3><a href='/corretor'>Cadastrar imóveis</a>"

    df = pd.read_csv('imoveis.csv')

    features = ['quartos', 'vagas', 'area']
    df_encoded = pd.get_dummies(df[['tipo', 'cidade', 'bairro', 'aceita_pets']])
    X = pd.concat([df[features], df_encoded], axis=1)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    modelo_knn = NearestNeighbors(n_neighbors=5, metric='euclidean')
    modelo_knn.fit(X_scaled)

    import joblib
    joblib.dump(modelo_knn, 'modelo_knn.joblib')
    joblib.dump(scaler, 'scaler_knn.joblib')
    joblib.dump(X.columns, 'X_columns_knn.joblib')

    return "<h2>✅ Modelo KNN treinado com sucesso!</h2><a href='/imoveiscadastrados'>Voltar</a>"

# Rodar o app
if __name__ == '__main__':
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')

    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
