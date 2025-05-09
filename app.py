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
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1. Buscar id_produto na tabela produtoautomacao
        cur.execute(
            "SELECT id_produto FROM produtoautomacao WHERE codigobarras = %s",
            (ean,)
        )
        result = cur.fetchone()
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado no produtoautomacao"
            )

        id_produto = result[0]

        # 2. Buscar descricao na tabela produto
        cur.execute(
            "SELECT descricaocompleta FROM produto WHERE id = %s",
            (id_produto,)
        )
        produto = cur.fetchone()
        if not produto:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado na tabela produtos"
            )

        return {"id_produto": id_produto, "descricao": produto[0]}

    except HTTPException:
        # redireciona HTTPExceptions sem alterar o status ou detalhe
        raise
    except Exception as e:
        # Em caso de qualquer outro erro, retorna 500
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Fecha cursor e conexão apenas se existirem
        if cur:
            cur.close()
        if conn:
            conn.close()
