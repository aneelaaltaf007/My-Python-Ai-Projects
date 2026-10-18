import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    groq_api_key = st.text_input(
        "🔑 Groq API Key",
        type="password",
        placeholder="Enter your Groq API key"
    )

    st.caption("Your API key is entered by you to use this app.")

# Main app
st.title("🤖 AI Assistant")

user_input = st.text_area(
    "💬 Ask your question",
    placeholder="Type your question here..."
)

if st.button("🚀 Generate Answer"):

    if not groq_api_key:
        st.warning("Please enter your Groq API key in the sidebar.")

    elif not user_input:
        st.warning("Please enter your question.")

    else:
        try:
            client = Groq(api_key=groq_api_key)

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                temperature=0.2,
                max_completion_tokens=600
            )

            answer = response.choices[0].message.content

            st.subheader("💡 Answer")
            st.write(answer)

        except Exception as e:
            st.error(f"Error: {e}")