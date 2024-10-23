from langchain.chains import LLMChain
from langchain_aws import BedrockLLM  # Updated import
from langchain.prompts import PromptTemplate
import boto3
import os
import streamlit as st
import json
import sys
import logging  # Added logging import

sys.path.append(os.path.abspath('/Users/jadendang/Documents/GitHub/VCT-Team-Builder/project'))
from vlrdata.vlr_fetch import fetch_stats

# Set up AWS profile
os.environ["AWS_PROFILE"] = "Hackthon"

# Bedrock Client
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="ap-northeast-1"  # Tokyo region
)

modelID = "amazon.titan-text-express-v1"
llm = BedrockLLM(
    model_id=modelID,
    client=bedrock_client,
    model_kwargs={"maxTokenCount": 300, "temperature": 0.7}  # Reduce token limit for testing
)

region = "na"
timespan = "60"
scrape_data = fetch_stats(region, timespan)
logging.basicConfig(level=logging.INFO)
logging.info(f"Scraped Data: {scrape_data}")  # Added logging to check scraped data

# Chatbot function
def vct_chatbot(freeform_text, scraped_data):
    if not scraped_data or 'data' not in scraped_data or 'segments' not in scraped_data['data']:
        return "Sorry, I couldn't retrieve any player statistics. Please try again later."

    base_prompt = "You are a chatbot that helps analyze player stats and build teams for VCT based on that data. Answer the following:\n\n"
    prompt_text = base_prompt + freeform_text
    scraped_data_info = "Here are the player statistics:\n\n"
    
    player_count = 0
    for entry in scraped_data['data']['segments']:
        if player_count < 3:  # Limit to 3 players for concise output
            scraped_data_info += (
                f"- Player: {entry['player']}, Org: {entry['org']}, Agents: {entry['agents']}, "
                f"Roles: {entry['roles']}, Rounds Played: {entry['rounds_played']}, Rating: {entry['rating']}, "
                f"ACS: {entry['average_combat_score']}, Avg Dmg per round: {entry['average_damage_per_round']}, "
                f"Headshot %: {entry['headshot_percentage']}, Clutch %: {entry['clutch_success_percentage']}\n"
            )
            player_count += 1
        else:
            break

    prompt_text += scraped_data_info
    prompt = PromptTemplate(input_variables=["prompt_text"], template="{prompt_text}")
    bedrock_chain = LLMChain(llm=llm, prompt=prompt)

    try:
        response = bedrock_chain({"prompt_text": prompt_text})
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")  # Added error logging
        return f"Sorry, there was an issue generating a response: {str(e)}"

    return response["text"] if "text" in response else "Sorry, I couldn't generate a valid response."

# Streamlit UI
st.title("VCT Team Builder")

freeform_text = st.sidebar.text_area(label="What is your question", max_chars=100)

if freeform_text:
    response = vct_chatbot(freeform_text, scrape_data)
    st.write(response)
