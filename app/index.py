import streamlit as st
import text_to_sql_gemini as sqlGen
import pandas as pd

def run_query(query): # Função para executar uma consulta na base
    engine = sqlGen.connect_database()
    df = pd.read_sql(query, engine)
    return df

st.set_page_config(page_title= 'Assistente SQL', layout= 'wide')
st.title('Assistente de consultas SQL com Google Gemini')
st.write('Esse assistente é capaz de gerar consultas SQL, com base na base "barber_shop" (ver https://github.com/PeSobrinho/barber_shop_report), usando Google Gemini ')

# Interface do chat

## Histórico da conversa
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message["content"])

## Interação com usuário
if prompt := st.chat_input('Faça uma pergunta sobre os dados da barbearia'):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    ### Resposta da aplicação
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response = ""

        #### Consulta gerada pelo Gemini
        sql_result = sqlGen.ask_gemini(prompt) 
        response += f'Consulta gerada\n```sql\n{sql_result}\n```\n\n'

        message_placeholder.markdown(response)

        #### Execução da consulta na base
        sql_result = str.replace(str.replace(sql_result, '```', ''), 'sql', '')
        df = run_query(sql_result)
        response += "Resultado da consulta:\n"
        message_placeholder.markdown(response)
        st.dataframe(df)

        st.session_state.messages.append({"role": "assistant", "content": response}) #### Atualização do histórico

if st.button('Limpar conversa'):
    st.session_state.messages = []
    st.rerun()