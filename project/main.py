from langchain.chains import LLMChain
from langchain_aws import BedrockLLM  # Updated import
from langchain.prompts import PromptTemplate
import boto3
import os
import streamlit as st
import json
import sys
import time
import random

# Set up AWS profile
os.environ["AWS_PROFILE"] = "Hackthon"  # Changed to default profile

# Bedrock Client
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2"
)

modelID = "amazon.titan-text-express-v1"
llm = BedrockLLM(
    model_id=modelID,
    client=bedrock_client,
    model_kwargs={"maxTokenCount": 300, "temperature": 0.7}  # Reduce token limit for testing
)

# Chatbot function
def vct_chatbot(freeform_text, linked_data):
    if not linked_data:
        return "Sorry, I couldn't find any relevant data right now. Please try again later."

    # Check if query is for a specific player
    player_name_query = None
    if "player" in freeform_text.lower() or any(player.lower() in freeform_text.lower() for player in ["tenz"]):  # Include check for Tenz
        player_name_query = freeform_text.split()[-1].lower()  # Assuming last word is the player name
    
    if player_name_query:
        # Search for player data in linked_data
        player_data_found = False
        linked_data_info = "Player stats:\n\n"
        for entry in linked_data:
            for player_id, player in entry['participants'].items():
                player_name = player.get('name', '').lower()
                if player_name_query == player_name:  # Found the player in data
                    linked_data_info += f"- Player: {player.get('name', 'Unknown')}, Org: {player.get('org', 'Unknown')}, Agents: {player.get('agents', 'Unknown')}, Roles: {player.get('roles', 'Unknown')}\n"
                    player_data_found = True
                    break  # Stop after finding the first match
            if player_data_found:
                break  # Stop after finding the player data

        if not player_data_found:
            return f"Sorry, no data available for {player_name_query.capitalize()}."

        prompt_text = linked_data_info
    else:
        # Default prompt if it's not a player query
        prompt_text = "You are a chatbot that helps with general VCT esports inquiries. Please answer the following:\n\n" + freeform_text

    prompt = PromptTemplate(input_variables=["prompt_text"], template="{prompt_text}")
    bedrock_chain = LLMChain(llm=llm, prompt=prompt)

    retry_attempts = 2  # Fewer attempts to reduce request overload
    for attempt in range(retry_attempts):
        try:
            print(f"Attempt {attempt + 1} running Bedrock Chain...")
            response = bedrock_chain.run(prompt_text=prompt_text)
            
            # Adding delay to avoid hitting the API request limit
            time.sleep(0.5)  # 500ms delay (2 requests per second)
            
            return response
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {str(e)}")
            if "ThrottlingException" in str(e):
                wait_time = (2 ** (attempt + 1)) * 5 + random.uniform(1, 2)  # Increased base wait time
                print(f"Throttled, retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                return f"Sorry, there was an issue generating a response: {str(e)}"

    print("Request limit reached after retrying.")
    return "Request limit reached. Please try again later."


# Load JSON Data
def load_json(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        sys.exit(f"Error: Folder path '{folder_path}' does not exist.")

    # Print the contents of the folder to verify
    print("Contents of folder:", os.listdir(folder_path))

    data = {
        "mapping_data": [],
        "players": {},  # Changed from list to dictionary
        "teams": {},
        "tournaments": {},
        "leagues": {}
    }

    try:
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path) and file_name.endswith(".json") and not file_name.endswith(".gz"):
                print(f"Loading file: {file_name}")
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        content = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"Skipping file {file_name} due to JSON decode error: {e}")
                        continue

                    if file_name == "mapping_data.json":
                        data["mapping_data"] = content
                    elif file_name == "players.json":
                        if isinstance(content, list):
                            for player in content:
                                data["players"][player["id"]] = player
                        elif isinstance(content, dict):
                            data["players"].update(content)
                    elif file_name == "teams.json":
                        if isinstance(content, list):
                            for team in content:
                                data["teams"][team["id"]] = team
                        elif isinstance(content, dict):
                            data["teams"].update(content)
                    elif file_name == "tournaments.json":
                        if isinstance(content, list):
                            for tournament in content:
                                data["tournaments"][tournament["id"]] = tournament
                        elif isinstance(content, dict):
                            data["tournaments"].update(content)
                    elif file_name == "leagues.json":
                        if isinstance(content, list):
                            for league in content:
                                data["leagues"][league["league_id"]] = league
                        elif isinstance(content, dict):
                            data["leagues"].update(content)
    except Exception as e:
        sys.exit(f"Error loading JSON files: {str(e)}")

    return data


# Link Data
def link_data(data):
    linked_data = []
    for mapping in data["mapping_data"]:
        team_info = {team_id: data["teams"].get(team_id, {}) for team_id in mapping.get("teamMapping", {}).values() if team_id in data["teams"]}
        participant_info = {participant_id: data["players"].get(participant_id, {}) for participant_id in mapping.get("participantMapping", {}).values() if participant_id in data["players"]}

        linked_data.append({
            "platformGameId": mapping.get("platformGameId", ""),
            "tournamentId": mapping.get("tournamentId", ""),
            "teams": team_info,
            "participants": participant_info,
            "tournament_info": data["tournaments"].get(mapping.get("tournamentId", ""), {}),
            "league_info": data["leagues"].get(data["tournaments"].get(mapping.get("tournamentId", ""), {}).get("league_id", ""), {})
        })
    return linked_data


# Main Program
folder_path = '/Users/shadmanshahzahan/Downloads/VCT/VCT-Team-Builder/project/esports-data'

data = load_json(folder_path)
linked_data = link_data(data)

# Streamlit UI
st.title("VCT Team Builder")
freeform_text = st.sidebar.text_area(label="Enter your question here", max_chars=100)

if freeform_text:
    response = vct_chatbot(freeform_text, linked_data)
    st.write(response)

