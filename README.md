# startup-sphere-app
A crunchbase-like company intelligence application created using Langchain and Streamlit

## Running the app
### In local
1. Clone the github repo
2. `pip install -r requirements.txt`
3. `streamlit run app.py`

### In Streamlit cloud
1. Go to https://share.streamlit.io/
2. Click on 'new app', and fill in the details
3. Click on 'advanced settings' and copy the contents of .streamlit/secrets.toml in the secrets section
4. Click on 'Deploy'

This project uses a managed version of Postgresql to store the data. The database service used is Aiven ([https://aiven.io/postgresql](https://aiven.io/postgresql))
