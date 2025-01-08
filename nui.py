import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from jarvis_stm import handle_query
 

st.set_page_config(layout="wide", page_title="Multi-Agent Chat Application")
 
# Sidebar Contents
with st.sidebar:
    st.title("Multi-Agent Chat Application")
    st.markdown(
        """
This is a demo of the Multi-Agent concept.
"""
    )
    add_vertical_space(5)
    st.write("Related to AutoGen")
    if st.button("Clear Chat"):
        if "history" in st.session_state:
            st.session_state["history"] = []
 
if "history" not in st.session_state:
    st.session_state["history"] = []
 
# Main Chat Interface
st.title("Chat Interface")
 
# Display chat history
history = st.session_state["history"]
for message in history:
    role = message["role"]
    content = message["content"]
    with st.chat_message(role):
        st.markdown(content)
 

    
def add_entry(r,c):
    if c in user_input:
        return
    c = c if 'TERMINATE' not in c else c.replace('TERMINATE','')
    history.append({"role": r, "content": c})
    # Display the user's message
    with st.chat_message(r):
        st.markdown(c)


#Input for user message
user_input = st.chat_input("You:")
 
if user_input:
    # Append user's message to the history
    history.append({"role": "user", "content": user_input})
 
    # Display the user's message
    with st.chat_message("user"):
        st.markdown(user_input)
 
    handle_query(user_input,add_entry)
    # Process the query through the backend
    # response = handle_query(user_input,add_entry)
 
    # # Display the assistant's response
    # if response:
    #     assistant_message = response
    #     history.append({"role": "assistant", "content": assistant_message})
 
    #     with st.chat_message("assistant"):
    #         st.markdown(assistant_message)
    # else:
    #     with st.chat_message("assistant"):
    #         st.markdown("Sorry, I could not process your request.")
 
# Save the updated history
st.session_state["history"] = history


