import os
from fastapi import FastAPI, HTTPException
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


@app.get("/produto/{ean}")
def consultar_produto(ean: str):
    try:
        conn = get_connection()
        cur = conn.cursor()

        if ean.lower() == "all":
            # Traz todos os produtos com join entre as tabelas
            cur.execute("""
                SELECT pa.id_produto, p.descricaocompleta 
                FROM produtoautomacao pa
                JOIN produto p ON pa.id_produto = p.id
            """)
            resultados = cur.fetchall()
            produtos = [{"id_produto": row[0], "descricao": row[1]} for row in resultados]
            return produtos

        else:
            # Buscar id_produto pela tabela produtoautomacao
            cur.execute("SELECT id_produto FROM produtoautomacao WHERE codigobarras = %s", (ean,))
            result = cur.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Produto não encontrado no produtoautomacao")

            id_produto = result[0]

            # Buscar descricao pela tabela produtos
            cur.execute("SELECT descricaocompleta FROM produto WHERE id = %s", (id_produto,))
            produto = cur.fetchone()

            if not produto:
                raise HTTPException(status_code=404, detail="Produto não encontrado na tabela produtos")

            return {"id_produto": id_produto, "descricao": produto[0]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()
