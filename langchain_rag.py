import getpass
import os
import toml

secrets = toml.load('.streamlit/secrets.toml')
openai = secrets['openai']
api_key = openai['api_key']
os.environ["OPENAI_API_KEY"] = api_key

import bs4
from langchain import hub
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import WebBaseLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
import fetch_links
from urllib.parse import urlsplit
import requests
requests.adapters.DEFAULT_RETRIES = 0
from datetime import datetime


def build_rag_chain(urls, debug = False):
    header_template = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*"
        ";q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    loader = WebBaseLoader(
        web_paths=(urls),
        header_template=header_template
    )
    docs = loader.load()

    if debug==True:
        logger.info(docs)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()

    prompt = hub.pull("rlm/rag-prompt")
    llm = ChatOpenAI(model_name="gpt-4", temperature=0)


    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)


    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain

def extract_data(search_terms, question, query_type='all'):
    google_search_urls = []
    for search_term in search_terms:
        if query_type == 'all':
            google_search_url = f"https://www.google.com/search?q={search_term}"
        elif query_type == 'news':
            google_search_url = f"https://www.google.com/search?q={search_term}&tbm=nws"
        google_search_urls.append(google_search_url)

    search_links = []

    for google_search_url in google_search_urls:
        search_links.extend(fetch_links.google_search_links(google_search_url, num_links=10))
        search_links.append(google_search_url)

    search_links = remove_urls_with_missing_schema(search_links)
    search_links = remove_unreachable_urls(search_links)
    if search_links:
        rag_chain = build_rag_chain(search_links, debug=False)
        return rag_chain.invoke(question)
    else:
        return 'NA'

def remove_urls_with_missing_schema(url_list):
    return [link for link in url_list if urlsplit(link).scheme]

def check_if_url_is_reachable(url):
    try:
        response = requests.head(url, timeout=3)
        return response.status_code == 200
    except:
        return False

def remove_unreachable_urls(url_list):
        return [link for link in url_list if check_if_url_is_reachable(link)]

def remove_long_fields(data):
    for key in data.keys():
        #news corner can be longer
        if key != 'news_corner':
            try:
                if len(data[key]) > 80:
                    data[key] = 'NA' 
            except TypeError:
                pass

    return data

def fetch_company_data(logger, input_url):
    input_depth = 1
    max_links = 5
    all_links = [input_url]
    all_links.extend(fetch_links.get_all_links_in_domain(input_url, input_depth, max_links=max_links))
    all_links = remove_urls_with_missing_schema(all_links)
    all_links = remove_unreachable_urls(all_links)
    all_links = list(set(all_links))

    logger.info(f'all_links : {all_links}')
    rag_chain = build_rag_chain(all_links)

    question = '''This a document about a company website. What is the name of the company written on the 
                  website? Tell me the name that is most frequently appearing on the website. 
                  Just write the name and do now write anything else'''

    company_name = rag_chain.invoke(question)

    logger.info(f'company_name : {company_name}')

    # prompt_template = '''{} If you don't know the answer write NA'''

    # search_term = [f'{company_name} location']
    # question = '''Which city is the company located in according to the data?
    #               Just write the city and do not write anything else'''
    # company_location = extract_data(search_term, prompt_template.format(question))
    # logger.info(f'company_location : {company_location}')

    # search_term = [f'{company_name} number of employees']
    # question = '''How many employees does the company have according to the data?
    #               Just write the number of employees and do not write anything else'''
    # number_of_employees = extract_data(search_term, prompt_template.format(question))
    # logger.info(f'number_of_employees : {number_of_employees}')

    # search_term = [f'{company_name} total funding']
    # question = '''What is the total funding of the company according to the data?
    #               Just write the funding amount and do not write anything else'''
    # total_funding = extract_data(search_term, prompt_template.format(question))
    # logger.info(f'total_funding : {total_funding}')

    # search_term = [f'{company_name} number of investors']
    # question = '''How many inverstors does the company have according to the data?
    #               Just write the total number of investors and do not write anything else'''
    # number_of_investors = extract_data(search_term, prompt_template.format(question))
    # logger.info(f'number_of_investors : {number_of_investors}')

    # search_term = [f'{company_name} names of investors']
    # question = '''What are the names of the inverstors according to the data?
    #               Just write the names and do not write anything else'''
    # investors_name = extract_data(search_term, prompt_template.format(question))
    # logger.info(f'investors_name : {investors_name}')

    # search_term = [f'{company_name} founding year']
    # question = '''When was the company founded according to the data?
    #               Just write the founding year and do not write anything else'''
    # founding_year = extract_data(search_term, prompt_template.format(question))
    # logger.info(f'founding_year : {founding_year}')

    # search_term = [f'{company_name} founders name']
    # question = '''What are the names of the company founders according to the data?
    #               Just write the founders' name and do not write anything else'''
    # founders_name = extract_data(search_term, prompt_template.format(question))
    # logger.info(f'founders_name : {founders_name}')

    # search_terms = [f'{company_name}', f'{company_name} funding']
    # question = f'''Give me important pieces of information about the company {company_name}. 
    #               Include information such as top new articles about the company, any deals they have done,
    #               details of fund raise etc. Include the full links to the sources in your response. This
    #               response is for a customer facing application. Only write what you know, don\'t say I
    #               don\'t know'''
    # news_corner = extract_data(search_terms, prompt_template.format(question))
    # logger.info(f'news_corner : {news_corner}')

    # data = {'company_name' : company_name,
    #         'company_location' : company_location,
    #         'number_of_employees' : number_of_employees,
    #         'total_funding' : total_funding,
    #         'number_of_investors' : number_of_investors,
    #         'investors_name' : investors_name,
    #         'founders_name' : founders_name,
    #         'founding_year' : founding_year,
    #         'news_corner' : news_corner,
    #         'record_timestamp' : datetime.now(),}

    # logger.info('removing long fields')
    # data = remove_long_fields(data)

    # return data


if __name__ == '__main__':
    question = '''Give me important pieces of information about the company Lithasa Technologies Pvt. Ltd. 
                  Include information such as top new articles about the company, any deals they have done,
                  details of fund raise etc. Include the full links to the sources in your response. This
                  response is for a customer facing application. Only write what you know, don\'t say I
                  don\'t know'''
    print(extract_data(['Lithasa Technologies Pvt. Ltd.', 'Lithasa Technologies Pvt. Ltd. funding'], question, query_type='news'))
