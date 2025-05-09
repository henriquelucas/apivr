# Imagem base com Python
FROM python:3.10-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos da aplicação para dentro do container
COPY . /app

# Instala as dependências
RUN pip install --no-cache-dir fastapi[all] psycopg2

# Expõe a porta padrão do Uvicorn
EXPOSE 8000

# Comando para rodar a aplicação com Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
