import streamlit as st 
from groq import Groq
st.title('🦜🔗 Quickstart App')
# groq_api_key =st.sidebar.text_input('Groq API Key', type ='password')
groq_api_key = st.secrets["GROQ_API_KEY"]
def generate_response(input_text):
    llm=ChatGroq(temperature =0.7, groq_api_key = groq_api_key,  model="openai/gpt-oss-20b")
    response = llm.invoke(input_text)
    st.info(response.content)
with st.form('my_form'):
    text=st.text_area('Enter text:', '...')
    submitted = st.form_submit_button('Submit')

    
if submitted and groq_api_key:
    generate_response(text)