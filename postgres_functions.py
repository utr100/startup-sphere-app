import toml
import psycopg2

def execute_query(query, arg_tuple):
    secrets = toml.load('.streamlit/secrets.toml')

    postgre_credentials = secrets['connections']['postgresql']

    host = postgre_credentials['host']
    port = postgre_credentials['port']
    database = postgre_credentials['database']
    user = postgre_credentials['username']
    password = postgre_credentials['password']


    conn = psycopg2.connect(host=host,
                          port=port,
                          database=database,
                          user=user,
                          password=password)

    conn.autocommit = True

    cursor = conn.cursor()
    cursor.execute(query, arg_tuple)