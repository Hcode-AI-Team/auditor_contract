# 🔧 Guia de Instalação Completo

Instruções detalhadas para configurar o ambiente do Auditor de Contratos.

---

## 📋 Pré-requisitos

### 1. Python 3.9 ou superior

**Verificar versão:**
```bash
python --version
# ou
python3 --version
```

**Instalar Python (se necessário):**
- **Windows**: [python.org/downloads](https://www.python.org/downloads/)
- **Linux**: `sudo apt install python3 python3-pip python3-venv`
- **Mac**: `brew install python3`

### 2. Chave API da OpenAI

1. Acesse [platform.openai.com](https://platform.openai.com/)
2. Faça login ou crie uma conta
3. Vá em **API Keys** no menu
4. Clique em **Create new secret key**
5. Copie a chave (começa com `sk-`)

⚠️ **Importante**: Mantenha sua chave segura e nunca compartilhe publicamente!

---

## 🚀 Instalação Passo a Passo

### Passo 1: Clonar/Baixar o Projeto

```bash
# Se estiver usando Git
git clone <url-do-repositorio>
cd aula2

# Ou simplesmente navegue até a pasta do projeto
cd C:\projects\fiap\itau\ai-agents\aula2
```

### Passo 2: Criar Ambiente Virtual

O ambiente virtual isola as dependências do projeto.

**Windows:**
```bash
python -m venv venv
```

**Linux/Mac:**
```bash
python3 -m venv venv
```

### Passo 3: Ativar Ambiente Virtual

**Windows (CMD):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

✅ Você verá `(venv)` no início da linha do terminal quando ativado.

### Passo 4: Instalar Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Tempo estimado**: 2-3 minutos

### Passo 5: Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

**Windows (CMD):**
```bash
echo OPENAI_API_KEY=sk-sua-chave-aqui > .env
```

**Linux/Mac:**
```bash
echo "OPENAI_API_KEY=sk-sua-chave-aqui" > .env
```

**Ou edite manualmente:**
1. Crie arquivo `.env` na raiz do projeto
2. Adicione a linha: `OPENAI_API_KEY=sk-sua-chave-aqui`
3. Salve o arquivo

### Passo 6: Testar Instalação

```bash
python test_setup.py
```

**Output esperado:**
```
🐍 Testando versão do Python...
   ✅ Python 3.11.5

📦 Testando imports...
   ✅ python-dotenv
   ✅ langchain
   ✅ langchain-openai
   ✅ langchain-community
   ✅ chromadb
   ✅ pydantic
   ✅ pypdf

🔑 Testando configuração API Key...
   ✅ OPENAI_API_KEY configurada (sk-proj-...)

📄 Testando arquivo de contrato...
   ✅ contrato_mutuo_exemplo.txt encontrado

✅ TODOS OS TESTES PASSARAM!
```

---

## ✅ Verificação Final

Execute o auditor pela primeira vez:

```bash
python auditor_contratos.py
```

**Output esperado:**
```
======================================================================
🏦 AUDITOR DE CONTRATOS - BANCO ITAÚ
======================================================================

📥 ETAPA 1: Ingestão de Documento

📄 Carregando documento: contrato_mutuo_exemplo.txt
   ✓ 1 página(s) carregada(s)
   ✓ 12 chunks criados
🔄 Gerando embeddings e indexando no ChromaDB...
✅ Indexados 12 chunks no ChromaDB (coleção: contratos)

🤖 ETAPA 2: Criação do Agente ReAct
✅ Agente auditor criado e pronto!

🔍 ETAPA 3: Análise do Contrato
...
```

---

## 🐛 Problemas Comuns

### Erro: "python não é reconhecido"

**Solução**: Python não está no PATH.

**Windows:**
1. Reinstale Python marcando "Add Python to PATH"
2. Ou adicione manualmente: `C:\Python311\` ao PATH

**Linux/Mac:**
```bash
# Use python3 em vez de python
python3 -m venv venv
```

### Erro: "pip não é reconhecido"

**Solução**:
```bash
python -m pip install --upgrade pip
```

### Erro: "cannot activate venv"

**Windows PowerShell:**
```bash
# Permitir execução de scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Depois ativar
venv\Scripts\Activate.ps1
```

### Erro: "ModuleNotFoundError: No module named 'X'"

**Solução**:
1. Certifique-se que o venv está ativado (veja `(venv)` no terminal)
2. Reinstale as dependências:
```bash
pip install -r requirements.txt
```

### Erro: "OPENAI_API_KEY não encontrada"

**Solução**:
1. Verifique se o arquivo `.env` existe na raiz do projeto
2. Abra o arquivo e confirme que contém: `OPENAI_API_KEY=sk-...`
3. Certifique-se que não há espaços extras

### Erro: "sqlite3.OperationalError: database is locked"

**Solução**:
```bash
# Fechar todos os processos Python
# Depois deletar o banco
python utils.py
# Escolha opção 1 (Limpar ChromaDB)
```

### Erro: "Rate limit exceeded"

**Solução**: Você atingiu o limite de requisições da OpenAI.
- Aguarde alguns minutos
- Ou adicione créditos em [platform.openai.com/account/billing](https://platform.openai.com/account/billing)

### Erro ao instalar chromadb no Windows

**Solução**: Instale o Visual C++ Build Tools:
1. Baixe: [visualstudio.microsoft.com/visual-cpp-build-tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Instale "Desktop development with C++"
3. Reinicie o terminal
4. Execute novamente: `pip install -r requirements.txt`

---

## 🔄 Atualização de Dependências

Para atualizar todas as bibliotecas para as versões mais recentes:

```bash
pip install --upgrade -r requirements.txt
```

---

## 🗑️ Desinstalação

Para remover completamente o projeto:

```bash
# 1. Desativar venv (se ativo)
deactivate

# 2. Deletar pasta do ambiente virtual
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# 3. Deletar ChromaDB
rm -rf chroma_db  # Linux/Mac
rmdir /s chroma_db  # Windows

# 4. Deletar arquivo .env (contém sua API key)
rm .env  # Linux/Mac
del .env  # Windows
```

---

## 📦 Instalação em Ambiente de Produção

Para deploy em servidor:

### Usando Docker (Recomendado)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "auditor_contratos.py"]
```

```bash
docker build -t auditor-contratos .
docker run -e OPENAI_API_KEY=sk-... auditor-contratos
```

### Usando requirements.txt com versões fixas

```bash
# Gerar requirements com versões exatas
pip freeze > requirements-lock.txt

# Instalar em produção
pip install -r requirements-lock.txt
```

---

## 🧪 Instalação para Desenvolvimento

Para contribuir com o projeto:

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Configurar pre-commit hooks
pip install pre-commit
pre-commit install
```

---

## 💻 Ambientes Alternativos

### Google Colab

```python
# Instalar dependências
!pip install langchain langchain-openai langchain-community chromadb pypdf python-dotenv pydantic

# Configurar API Key
import os
os.environ["OPENAI_API_KEY"] = "sk-sua-chave"

# Upload do contrato
from google.colab import files
uploaded = files.upload()

# Executar código normalmente
!python auditor_contratos.py
```

### Jupyter Notebook

```bash
# Instalar kernel do venv
pip install ipykernel
python -m ipykernel install --user --name=auditor-contratos

# Abrir Jupyter
jupyter notebook
```

---

## 📞 Suporte

Se você encontrou um problema não listado aqui:

1. Verifique o arquivo `REFERENCIA_RAPIDA.md`
2. Consulte o `README.md` para documentação completa
3. Execute `python test_setup.py` para diagnóstico

---

**✅ Instalação concluída com sucesso!**

Próximos passos:
- Leia o `QUICKSTART.md` para começar rapidamente
- Explore `exemplo_uso_avancado.py` para casos de uso
- Abra `index.html` no navegador para o material teórico

---

**Bootcamp Itaú FIAP 2026** | Última atualização: Janeiro 2026
