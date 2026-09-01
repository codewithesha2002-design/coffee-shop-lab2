import os
import asyncio
import streamlit as st
from dotenv import load_dotenv

from google.adk.runners import InMemoryRunner
from google.genai import types

from data_agent.agent import root_agent


load_dotenv()


st.set_page_config(
    page_title="Coffee Shop Expansion Agent",
    page_icon="☕",
)

st.title("☕ Coffee Shop Expansion Agent")

st.write(
    "Use Gemini and BigQuery to analyze potential coffee shop locations "
    "based on cyclist and transportation activity."
)


# Get API key from Streamlit Cloud Secrets
# or from local .env
api_key = None

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except st.errors.StreamlitSecretNotFoundError:
    api_key = os.getenv("GEMINI_API_KEY")
except KeyError:
    api_key = os.getenv("GEMINI_API_KEY")


if not api_key:
    st.error("GEMINI_API_KEY is not configured.")
    st.stop()


question = st.text_area(
    "Ask the expansion agent",
    placeholder="Where should we open our next coffee shop?",
)


async def run_agent(user_question):
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="coffee_shop_expansion",
    )

    session = await runner.session_service.create_session(
        app_name="coffee_shop_expansion",
        user_id="streamlit_user",
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(text=user_question)
        ],
    )

    response_text = ""

    async for event in runner.run_async(
        user_id="streamlit_user",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text

    return response_text


if st.button("Analyze"):

    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    with st.spinner("Analyzing BigQuery data..."):

        try:
            response_text = asyncio.run(
                run_agent(question)
            )

            st.subheader("Recommendation")
            st.write(response_text)

        except Exception as e:
            st.error("Agent error:")
            st.code(str(e))
            