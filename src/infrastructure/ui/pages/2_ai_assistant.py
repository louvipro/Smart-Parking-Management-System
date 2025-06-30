import streamlit as st
import asyncio

from src.infrastructure.persistence.database import AsyncSessionLocal
from src.infrastructure.ml_agents.parking_agent_hybrid import HybridParkingAssistant
from src.infrastructure.persistence.sqlalchemy_repositories.sqlalchemy_repositories import SQLAlchemyVehicleRepository


st.set_page_config(
    page_title="AI Parking Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Parking Assistant")
st.markdown("Ask me anything about the parking system!")

# Initialize chat history and state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": """Hello! I'm your AI Parking Assistant. I can help you with:

- How many cars are currently parked?
- How many blue/red/black cars are in the parking?
- Color distribution of vehicles
- Brand distribution (Toyota, Honda, Ford, etc.)
- Floor distribution (which floors have the most cars)
- How much revenue was generated in the last N hours?
- Current parking status and availability
- Available spots and occupancy rate

Just ask me anything about the parking system!"""
    })

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initialize pending query state
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

async def process_user_query(query: str):
    async with AsyncSessionLocal() as db:
        if "assistant" not in st.session_state or st.session_state.assistant is None:
            st.session_state.assistant = HybridParkingAssistant(db)
        
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing your question and checking parking data..."):
                try:
                    response = await st.session_state.assistant.process_query(query)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Process pending query from example buttons
if st.session_state.pending_query:
    query = st.session_state.pending_query
    st.session_state.pending_query = None  # Clear the pending query
    asyncio.run(process_user_query(query))

# Chat input
if prompt := st.chat_input("Ask about parking..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    asyncio.run(process_user_query(prompt))

# Sidebar with example queries
with st.sidebar:
    st.subheader("📝 Example Questions")
    
    example_queries = [
        "How many cars are currently parked?",
        "How many red cars are in the parking?",
        "What's the color distribution?",
        "What's the brand repartition?",
        "What's the floor distribution?",
        "How much revenue in the last 2 hours?",
        "What's the parking status?",
        "How many spots are available?",
        "Show me the brand distribution"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"example_{query}"):
            st.session_state.messages.append({"role": "user", "content": query})
            st.session_state.pending_query = query
            st.rerun()