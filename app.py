from flask import Flask, render_template, request, redirect
import csv
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Página inicial (cliente) → corretor vê os imóveis
@app.route('/cliente')
def cliente():
    imoveis = []
    if os.path.exists('imoveis.csv'):
        with open('imoveis.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                imoveis.append(row)
    bairros = {}
    for imovel in imoveis:
        bairro = imovel['bairro']
        if bairro not in bairros:
            bairros[bairro] = []
        if len(bairros[bairro]) < 3:
            bairros[bairro].append(imovel)
    return render_template('cliente.html', bairros=bairros)

# Página do corretor → cadastrar imóveis
@app.route('/corretor', methods=['GET', 'POST'])
def corretor():
    if request.method == 'POST':
        titulo = request.form['titulo']
        bairro = request.form['bairro']
        preco = request.form['preco']
        imagem = request.files['imagem']
        if imagem:
            filename = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with open('imoveis.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if os.path.getsize('imoveis.csv') == 0:
                    writer.writerow(['titulo', 'bairro', 'preco', 'imagem'])
                writer.writerow([titulo, bairro, preco, filename])
        return redirect('/corretor')
    return render_template('corretor.html')

# Nova página → formulário para o cliente preencher preferências
@app.route('/formulariocliente', methods=['GET', 'POST'])
def formulariocliente():
    mensagem = ''
    if request.method == 'POST':
        bairro = request.form['bairro']
        preco_max = request.form['preco_max']
        quartos = request.form['quartos']
        aceita_pets = 'sim' if request.form.get('aceita_pets') else 'nao'

        # Salva as preferências no arquivo
        with open('preferencias.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if os.path.getsize('preferencias.csv') == 0:
                writer.writerow(['bairro', 'preco_max', 'quartos', 'aceita_pets'])
            writer.writerow([bairro, preco_max, quartos, aceita_pets])

        mensagem = 'Obrigado! Suas preferências foram registradas.'

    return render_template('formulariocliente.html', mensagem=mensagem)


# Página de sucesso ao treinar
@app.route('/treinar')
def treinar():
    return "<h2>Modelo treinado com sucesso! (Exemplo estático)</h2><a href='/corretor'>Voltar</a>"

if __name__ == '__main__':
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
