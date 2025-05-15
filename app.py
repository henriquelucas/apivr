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

@app.get("/produtos/{id_loja}/{ean}")
def consultar_produto(id_loja: int, ean: str):
    try:
        conn = get_connection()
        cur = conn.cursor()

        if ean.lower() == "all":
            # Traz todos os produtos com join entre as tabelas para a loja informada e ativos
            cur.execute("""
                SELECT pa.id_produto, p.descricaocompleta, pc.precovenda
                FROM produtoautomacao pa
                JOIN produto p ON pa.id_produto = p.id
                LEFT JOIN produtocomplemento pc 
                    ON pa.id_produto = pc.id_produto 
                    AND pc.id_loja = %s 
                    AND pc.id_situacaocadastro = 1
                WHERE EXISTS (
                    SELECT 1 FROM produtocomplemento sub_pc 
                    WHERE sub_pc.id_produto = pa.id_produto 
                    AND sub_pc.id_loja = %s 
                    AND sub_pc.id_situacaocadastro = 1
                )
            """, (id_loja, id_loja))
            resultados = cur.fetchall()
            produtos = [
                {
                    "id_produto": row[0],
                    "descricao": row[1],
                    "precovenda": float(row[2]) if row[2] is not None else None
                } for row in resultados
            ]
            return produtos

        else:
            # Buscar id_produto pela tabela produtoautomacao
            cur.execute("SELECT id_produto FROM produtoautomacao WHERE codigobarras = %s", (ean,))
            result = cur.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Produto não encontrado no produtoautomacao")

            id_produto = result[0]

            # Verifica se o produto está ativo (id_situacaocadastro = 1) para a loja
            cur.execute("""
                SELECT 1 FROM produtocomplemento 
                WHERE id_produto = %s AND id_loja = %s AND id_situacaocadastro = 1
            """, (id_produto, id_loja))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Produto inativo para esta loja")

            # Buscar descricao e preco pela tabela produto e produtocomplemento
            cur.execute("""
                SELECT p.descricaocompleta, pc.precovenda
                FROM produto p
                LEFT JOIN produtocomplemento pc 
                    ON p.id = pc.id_produto 
                    AND pc.id_loja = %s 
                    AND pc.id_situacaocadastro = 1
                WHERE p.id = %s
            """, (id_loja, id_produto))
            produto = cur.fetchone()

            if not produto:
                raise HTTPException(status_code=404, detail="Produto não encontrado na tabela produtos")

            return {
                "id_produto": id_produto,
                "descricao": produto[0],
                "precovenda": float(produto[1]) if produto[1] is not None else None
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()
