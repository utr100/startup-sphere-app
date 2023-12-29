import platform
if platform.system() == 'Linux':
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import pandas as pd
from streamlit_card import card
import psycopg2
import postgres_functions
import langchain_rag
import time
import validators
import requests

from streamlit.logger import get_logger
logger = get_logger(__name__)

# Initialize connection.
conn = st.connection("postgresql", type="sql")

# Perform query.
data = conn.query('SELECT * FROM company_information;', ttl="0m")

st.markdown("<h1 style='text-align: center;'>Startup Sphere</h1>", unsafe_allow_html=True)

name_mapper = {'company_name' : 'Company Name',
               'company_location' : 'Company Location',
               'number_of_employees' : 'Number of Employees',
               'total_funding' : 'Total Funding',
               'number_of_investors' : 'Number of Investors',
               'names_of_investors' : 'Name of Investors',
               'founders' : 'Founders',
               'founded_year' : 'Founded Year'}

options = data['company_name'].unique()

option = st.selectbox(
   "Select a company",
   options,
   index=None,
   placeholder="Select company...",
)


with st.form("my_form"):
    text_input = st.text_input(
                        "Not finding what you're looking for? Submit a new company here!",
                        placeholder='Enter company website link',
                        key = 'text_input'
                    )

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")
    if submitted:
        if text_input:
            with st.spinner("Processing..."):
                # Check if url is valid
                if validators.url(text_input):
                    logger.info(f'text_input : {text_input}')
                    fetched_data = langchain_rag.fetch_company_data(logger, text_input)
                    values = ", ".join(f"'{value}'" for value in fetched_data.values())
                    result = f'({values})'

                    sql = f"""INSERT INTO company_information VALUES {result}"""

                    postgres_functions.execute_query(sql)
                    st.success("Process completed!")
                else:
                    st.error("The URL is not valid.")

data = data[data['company_name'] == option].reset_index(drop=True)
data = data.sort_values(by = 'record_timestamp', ascending = False)
data = data.drop('record_timestamp', axis = 1)

if data.shape[0] > 0:
    for i, column in enumerate(data.columns):
        value = data[column][0]
        column = name_mapper[column]
        
        if i%2 == 0:
            col1, col2 = st.columns(2)
            with col1:
                res = card(
                  title=column,
                  text=value,
                  )
        else:
            with col2:
                res = card(
                  title=column,
                  text=value,
                  )