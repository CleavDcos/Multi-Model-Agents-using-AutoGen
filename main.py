#------Note; go through README to undertsnd working of AUTOGEN--------
# Ignore Warnings
import warnings
warnings.filterwarnings("ignore")

# Import necessary libraries
import os
import autogen
import gradio as gr
from openai import OpenAI  # Keep for reference if needed
from dotenv import load_dotenv
import random  # Used later for unique Gradio outputs
import google.generativeai as genai  # Import the Google library

# Load environment variables from the .env file
load_dotenv()

# Retrieve API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
print(openai_api_key)
google_api_key = os.getenv("GOOGLE_API_KEY")


print("Setup Complete: Libraries installed and API keys loaded.")


#define configuration of LLM for openai
config_list_openai = [
    {"model":"gpt-4o-mini",
     "api_key":openai_api_key}
]

llm_config_openai = {
    "config_list":config_list_openai,
    "temperature":0.7,
    "timeout":120
}
#define configuration of LLM for google gemini
config_list_gemini = [
    {"model":"gemini-2.0-flash",
     "api_key":google_api_key}
]

llm_config_gemini = {
    "config_list":config_list_gemini,
    "temperature":0.7,
    "timeout":120
}
#Define the CMO Officer prompt
cmo_prompt = """You are the Chief Marketing Officer (CMO) of a new shoe brand (sustainable).
Provide high-level strategy, define target audiences, and guide the Marketer. Focus on the big picture. Be concise."""
#Define the Brand Marketer Prompt
brand_marketer_prompt = """You are the Brand Marketer for the shoe brand. Brainstorm creative, specific campaign ideas (digital, content, experiences).
Focus on tactics and details. Suggest KPIs for your ideas."""

#Create Both the agents, ie for CMO AND Brand Marketer
cmo_agent_gemini = autogen.ConversableAgent(
    name= "Chief_Marketing_Officer_Gemini",
    system_message=cmo_prompt,
    llm_config=llm_config_gemini,
    human_input_mode="NEVER"
)
brand_marketer_agent_openai = autogen.ConversableAgent(
    name = "Brand_Marketer_OpenAI",
    system_message = brand_marketer_prompt,
    llm_config = llm_config_openai,  # Assign the same OpenAI config
    human_input_mode = "NEVER")

print(f"Agent '{cmo_agent_gemini.name}' created (using Google Gemini).")
print(f"Agent '{brand_marketer_agent_openai.name}' created (using OpenAI).")

#---Now adding Human in the LOOP to interact with the multimodel team----
user_proxy_agent = autogen.UserProxyAgent(
    name = "Human_User_Proxy",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=1,
    is_termination_msg = lambda x: x.get("content", "").rstrip().lower() in ["exit", "quit", "terminate"],
    code_execution_config = False,
    system_message = "You are the human user interacting with a multi-model AI team (Gemini CMO, OpenAI Marketer). Guide the brainstorm. Type 'exit' to end.",
)
print(f"Agent '{user_proxy_agent.name}' created for HIL with multi-model team.")

print("--- Starting Human-in-the-Loop (HIL) Conversation (Multi-Model) ---")
print("You will interact with Gemini CMO and OpenAI Marketer. Type 'exit' to end.")
print("---------------------------------------------------------------------")

# Reset agents for a clean new session
cmo_agent_gemini.reset()  # Reset Gemini CMO
brand_marketer_agent_openai.reset()  # Reset OpenAI Marketer
user_proxy_agent.reset()

#Create a GROUPCHAT to include all agents and initiate convo
from autogen import GroupChat, GroupChatManager
groupchat = GroupChat(
    agents = [user_proxy_agent, cmo_agent_gemini, brand_marketer_agent_openai],
    messages = [ ], #empty message histiory for now
    max_round = 20,
)
# Create a manager for the group chat, which is also an LLm
# The GroupChatManager orchestrates the conversation flow between agents
# It determines which agent should speak next and handles the overall conversation logic
group_manager = GroupChatManager(groupchat = groupchat, llm_config = llm_config_gemini)  # Uses Google's LLM to manage the conversation

#User Proxxy initiates the chat
group_chat_result = group_manager.initiate_chat(
    recipient = user_proxy_agent,
    message = """Hello Team!""",
)
print("---------------------------------------------------------------------")
print("--- Conversation Ended (Human terminated or Max Turns) ---")