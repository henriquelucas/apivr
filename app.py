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
                SELECT pa.id_produto, p.descricaocompleta, pc.precovenda, pc.estoque, pa.codigobarras
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
                    "precovenda": float(row[2]) if row[2] is not None else None,
                    "estoque": float(row[3]) if row[3] is not None else None,
                    "ean": row[4]
                } for row in resultados
            ]
            return produtos

        else:
            # Buscar id_produto e ean pela tabela produtoautomacao
            cur.execute("SELECT id_produto, codigobarras FROM produtoautomacao WHERE codigobarras = %s", (ean,))
            result = cur.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Produto não encontrado no produtoautomacao")

            id_produto, codigobarras = result

            # Verifica se o produto está ativo (id_situacaocadastro = 1) para a loja
            cur.execute("""
                SELECT 1 FROM produtocomplemento 
                WHERE id_produto = %s AND id_loja = %s AND id_situacaocadastro = 1
            """, (id_produto, id_loja))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Produto inativo para esta loja")

            # Buscar descricao, preco, estoque
            cur.execute("""
                SELECT p.descricaocompleta, pc.precovenda, pc.estoque
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
                "precovenda": float(produto[1]) if produto[1] is not None else None,
                "estoque": float(produto[2]) if produto[2] is not None else None,
                "ean": codigobarras
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

# Rota para consultar produtos alterados
@app.get("/produtosalterados/{id_loja}")
def consultar_produtos_alterados(id_loja: int):
    try:
        # Estabelecendo a conexão com o banco
        conn = get_connection()
        cur = conn.cursor()

        # Obter a data de hoje no formato YYYY-MM-DD
        today = datetime.today().strftime('%Y-%m-%d')

        # Consultar produtos alterados hoje
        cur.execute("""
            SELECT pa.id_produto, p.descricaocompleta, pc.precovenda, pc.estoque, pa.codigobarras
            FROM produtoautomacao pa
            JOIN produto p ON pa.id_produto = p.id
            LEFT JOIN produtocomplemento pc 
                ON pa.id_produto = pc.id_produto 
                AND pc.id_loja = %s 
                AND pc.id_situacaocadastro = 1
            WHERE p.dataalteracao::DATE = %s  -- Filtrando produtos com data de alteração de hoje
            AND EXISTS (
                SELECT 1 
                FROM produtocomplemento sub_pc 
                WHERE sub_pc.id_produto = pa.id_produto 
                AND sub_pc.id_loja = %s 
                AND sub_pc.id_situacaocadastro = 1
            )
        """, (id_loja, today, id_loja))
        
        resultados = cur.fetchall()

        # Processar resultados e formatar como JSON
        produtos = [
            {
                "id_produto": row[0],
                "descricao": row[1],
                "precovenda": float(row[2]) if row[2] is not None else None,
                "estoque": float(row[3]) if row[3] is not None else None,
                "ean": row[4]
            } for row in resultados
        ]

        # Retornar os produtos
        return produtos

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()
