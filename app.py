from flask import Flask, render_template, request, redirect, session
import csv, os, joblib, pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'chave-super-secreta'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

USERNAME = 'admin'
PASSWORD = '1234'

# Autenticação
@app.route('/login', methods=['GET','POST'])
def login():
    err = None
    if request.method=='POST':
        if request.form['username']!=USERNAME or request.form['password']!=PASSWORD:
            err='Usuário ou senha incorretos'
        else:
            session['logged_in']=True
            return redirect('/corretor')
    return render_template('login.html', error=err)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

@app.before_request
def require_login():
    if request.endpoint not in ('login', 'static', 'formulariocliente', 'treinar') \
       and not session.get('logged_in'):
        return redirect('/login')


# Cadastro de imóveis
@app.route('/corretor', methods=['GET','POST'])
def corretor():
    if request.method=='POST':
        f = request.files.getlist('fotos')
        fotos=[]
        for img in f:
            if img and img.filename:
                fn=secure_filename(img.filename)
                img.save(os.path.join(app.config['UPLOAD_FOLDER'],fn))
                fotos.append(fn)

        novo = [
            request.form['tipo'], request.form['titulo'], request.form['cidade'], request.form['bairro'],
            request.form['quartos'], request.form['vagas'], request.form['area'],
            request.form.get('aceita_pets','Não'),
            request.form['valor_condominio'], request.form['valor_aluguel'], request.form['valor_compra'],
            ";".join(fotos)
        ]
        cabe = not os.path.exists('imoveis.csv') or os.path.getsize('imoveis.csv')==0
        with open('imoveis.csv','a', newline='', encoding='utf-8') as arq:
            wr=csv.writer(arq)
            if cabe:
                wr.writerow(['tipo','titulo','cidade','bairro','quartos','vagas','area',
                             'aceita_pets','valor_condominio','valor_aluguel','valor_compra','fotos'])
            wr.writerow(novo)
        return redirect('/corretor')
    return render_template('corretor.html')

# Listar e excluir
@app.route('/imoveiscadastrados')
def listagem():
    itens=[]
    if os.path.exists('imoveis.csv'):
        with open('imoveis.csv', newline='', encoding='utf-8') as arq:
            itens=list(csv.DictReader(arq))
    venda = [(i,im) for i,im in enumerate(itens) if im['tipo']=='Venda']
    alug  = [(i,im) for i,im in enumerate(itens) if im['tipo']=='Aluguel']
    return render_template('imoveiscadastrados.html', venda=venda, aluguel=alug)

@app.route('/excluir_imovel/<int:i>')
def excluir(i):
    arr=[]
    if os.path.exists('imoveis.csv'):
        with open('imoveis.csv', newline='', encoding='utf-8') as arq:
            arr=list(csv.DictReader(arq))
    if 0<=i<len(arr):
        arr.pop(i)
    with open('imoveis.csv','w', newline='', encoding='utf-8') as arq:
        w=csv.DictWriter(arq, fieldnames=arr[0].keys() if arr else [])
        w.writeheader()
        w.writerows(arr)
    return redirect('/imoveiscadastrados')

# Formulário & recomendação
@app.route('/formulariocliente', methods=['GET','POST'])
def formulário():
    recs=[]
    if request.method=='POST':
        tipo      = request.form['tipo']
        bairro    = request.form['bairro']
        preco_max = float(request.form['preco_max'])
        quartos   = int(request.form['quartos'])
        pets      = 'Sim' if request.form.get('aceita_pets')=='on' else 'Não'

        df=pd.read_csv('imoveis.csv')
        df = df[df['tipo']==tipo]
        df['aceita_pets']=df['aceita_pets'].map({'Sim':1,'Não':0,'on':1}).fillna(0).astype(int)
        df['valor_aluguel']=pd.to_numeric(df['valor_aluguel'], errors='coerce').fillna(0)
        df['valor_compra']=pd.to_numeric(df['valor_compra'], errors='coerce').fillna(0)
        df['quartos']=df['quartos'].astype(int)
        df['vagas']=df['vagas'].astype(int)
        df['area']=pd.to_numeric(df['area'], errors='coerce').fillna(0)

        price_col = 'valor_aluguel' if tipo=='Aluguel' else 'valor_compra'
        df = df[(df['bairro'].str.lower()==bairro.lower())
                & (df[price_col]<=preco_max)
                & (df['quartos']>=quartos)
                & (df['aceita_pets']==pets)]

        if not df.empty:
            modelo = joblib.load(f'modelo_knn_{tipo.lower()}.pkl')
            X = df[['quartos','vagas','area','aceita_pets',
                    price_col]]
            neigh = modelo.kneighbors(X, n_neighbors=min(3,len(X)), return_distance=False)
            for idx in neigh[0]:
                recs.append(df.iloc[idx].to_dict())

    return render_template('formulariocliente.html', recomendacoes=recs)

# Rota de treinamento (opcional)
@app.route('/treinar')
def treinar():
    os.system('python treinar_modelo_recomendacao.ipynb')  # ou chame diretamente o script .py
    return "<h2>Treinamento disparado!</h2><a href='/corretor'>Voltar</a>"

if __name__=='__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
