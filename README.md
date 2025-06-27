
# **Sistema de Recomendação de Imóveis para Aluguel e Venda** 🏠

## **Resumo do Projeto**

Este projeto visa simplificar e agilizar a busca por imóveis para aluguel e venda, atendendo às necessidades dos clientes de corretores.  
A solução foi desenvolvida como um **sistema web simples e responsivo**, permitindo que corretores cadastrem imóveis e que clientes recebam **recomendações personalizadas** com base em suas preferências.

O diferencial do sistema é o uso de **aprendizado de máquina (KNN - K-Nearest Neighbors)** para recomendar imóveis semelhantes ao perfil informado pelo cliente.

---

## **Tecnologias Utilizadas**

- **Python com Flask**: para desenvolvimento do backend.  
- **HTML, CSS e Jinja2**: para renderização das páginas web.  
- **Pandas e Scikit-learn**: para manipulação de dados e treinamento do modelo de recomendação.  
- **Joblib**: para persistência do modelo treinado.  
- **Render.com**: para hospedagem do sistema.  
- **GitHub**: para versionamento e código-fonte.  

---

## **Funcionalidades Principais**

### **Área do Corretor (com login)**

- Cadastro de imóveis com título, localização, número de quartos, vagas, área, valores e fotos.  
- Upload de múltiplas imagens por imóvel.  
- Listagem e exclusão de imóveis cadastrados.  
- Menu de navegação para acesso rápido às funcionalidades.  

### **Recomendação para o Cliente**

- Formulário de preferência: bairro, número de quartos, valor máximo e se aceita pets.  
- Sistema retorna até **3 imóveis semelhantes usando algoritmo KNN**.  

### **Treinamento de IA**

- Com um clique, é possível treinar o modelo de recomendação com os dados atuais dos imóveis.  

---

## **Segurança**

- Sistema de login simples com usuário e senha.  
- Sessão protegida para evitar acesso não autorizado.  

---

## **Estrutura de Arquivos**

- `app.py`: script principal do Flask.  
- `templates/`: contém os arquivos HTML.  
- `static/`: imagens e CSS.  
- `imoveis.csv`: banco de dados local dos imóveis.  
- `modelo_knn.joblib`, `scaler_knn.joblib`, `X_columns_knn.joblib`: arquivos gerados do modelo de ML.  

---

## **Possibilidades de Melhorias Futuras**

- Criptografia de senha (**bcrypt**)  
- Cadastro de usuários (corretores diferentes)  
- Paginação dos imóveis cadastrados  
- Upload de vídeos  
- Comentários ou avaliações dos imóveis  
- Filtros adicionais no formulário do cliente  

---

## **Como Rodar Localmente**

```bash
# Instale as dependências
pip install flask pandas scikit-learn joblib

# Execute no terminal
cd "C:\Users\danie\OneDrive\Área de Trabalho\RecomendacaoImoveis"
python3.12 -m pip install -r requirements.txt
python app.py


# Acesse em seu navegador
http://localhost:5000/login
```

**Usuário padrão:** `admin`  
**Senha:** `1234`

---

## **Link de Demonstração**

🔗 https://recomendacaoimoveis.onrender.com/login

---

## **Autores**

**Daniel Borba Soares e Bruno Fonseca** 
Este sistema foi desenvolvido como **projeto pessoal e acadêmico** para praticar conceitos de desenvolvimento web, aprendizado de máquina.
