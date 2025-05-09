# Imagem base com Python
FROM python:3.11-slim

WORKDIR /app

# Instala as dependências diretamente usando pip
RUN pip install fastapi uvicorn[standard] psycopg2-binary python-dotenv

# Copia os arquivos do projeto para dentro do container
COPY . /app/

EXPOSE 8000

# Comando para rodar o app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8009"]
