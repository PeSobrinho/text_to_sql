from dotenv import load_dotenv
import os
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import google.generativeai as genai

load_dotenv()

def connect_database():

    user = os.getenv('user')
    password = os.getenv('password')
    host = os.getenv('host')
    port = os.getenv('port')
    database = os.getenv('database')
    ssl_cert= os.getenv('ssl_cert')


    engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}?sslmode=verify-full&sslrootcert={ssl_cert}')

    return engine

def get_schemas(engine):
    
    base_content_query = '''
    SELECT 
        table_name,
        column_name,
        data_type
    FROM 
        information_schema.columns
    WHERE 
        table_schema = 'dw'
    ORDER BY 
        table_name, column_name;
    '''

    base_content = pd.read_sql(base_content_query, engine)

    ddl_schemas = []

    for table_name in base_content['table_name'].unique():
        table_columns = base_content[base_content['table_name'] == table_name]
        
        ddl = f"CREATE TABLE dw.{table_name} (\n"
        columns = []
        
        for _, row in table_columns.iterrows():
            column = f"    {row['column_name']} {row['data_type']}"
            columns.append(column)
        
        ddl += ",\n".join(columns)
        ddl += "\n);"
        
        ddl_schemas.append(ddl)

    ddl_text = "\n\n".join(ddl_schemas)
    return ddl_text

def ask_gemini(query):

    engine = connect_database()

    ddl_text = get_schemas(engine)

    gemini_api = os.getenv('gemini_api')

    gen_config = {
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain"
    }

    prompt = f"""
    Você é um assistente de análise de dados, com o objetivo de extrair dados de uma base postgres SQL sob a demanda.
    A base com a qual está trabalhando no momento possui o seguinte esquema:

    <esquema>
    {ddl_text}
    </esquema>

    <descricao_tabelas>
    A tabela dim_cliente contém dados que identificam os clientes
    A tabela dim_funcionario contém dados que identificam os funcionários
    A tabela dim_pagamento contém dados que identificam as formas de pagamento disponíveis
    A tabela dim_servico contém dados que identificam os serviços disponíveis
    A tabela fact_servicos_barbearia contém dados de cada atendimento prestado
    </descricao_tabelas>

    <instruções>
    1 - Antes de gerar a query, faça:
        - Consulte <descricao_tabelas></descricao_tabelas> para entender do que se trata cada tabela
    2 - Com base unicamente no <esquema></esquema> fornecido, gere uma query sql que responda a pergunta do usuário;
    3 - Otimize a query gerada para a melhor performance;
    4 - Mantenha boas práticas em SQL;
    5 - Nunca traga resultados com IDs;
    5 - Retorne apenas a query gerada.
    </instruções>
    """

    genai.configure(api_key = gemini_api)

    model = genai.GenerativeModel(
        model_name= 'gemini-1.5-pro',
        generation_config= gen_config,
        system_instruction= prompt)

    response = model.generate_content(query)
    return response.text

if __name__ == '__main__':
    ask_gemini()
