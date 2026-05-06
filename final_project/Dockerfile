# Usar a imagem base do Python 3.10
FROM python:3.10-bookworm

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Install uv and dependencies
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY requirements.txt ./

RUN uv pip install --system -r requirements.txt

# Copiar os arquivos do projeto para o container
COPY . /app

# Expor a porta 1337 para o Coolify
EXPOSE 1337

# Configurar o comando de inicialização
CMD ["python", "main.py"]
