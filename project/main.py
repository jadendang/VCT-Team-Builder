from langchain.chains import LLMChain
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate
import boto3
import os
import streamlit as st
import json

# Set up AWS profile
os.environ["AWS_PROFILE"] = "vscode"

# Bedrock Client
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

modelID = "anthropic.claude-v2:1"
llm = Bedrock(
    model_id=modelID,
    client=bedrock_client,
    model_kwargs={"max_tokens_to_sample": 2000, "temperature": 0.9}
)

# Chatbot function
def vct_chatbot(freeform_text, linked_data):
    if not linked_data:
        return "Sorry, I couldn't find any relevant data right now. Please try again later."

    if "player" in freeform_text.lower():
        base_prompt = "You are a chatbot that helps analyze player stats for VCT. Answer the following:\n\n"
        prompt_text = base_prompt + freeform_text
        linked_data_info = "Here are the player statistics:\n\n"

        if not any(entry['participants'] for entry in linked_data):
            return "Sorry, no player data is available."

        for entry in linked_data:
            for player_id, player in entry['participants'].items():
                linked_data_info += f"- Player: {player['name']}, Org: {player['org']}, Agents: {player['agents']}, Roles: {player['roles']}\n"

        prompt_text += linked_data_info

    elif "team" in freeform_text.lower():
        base_prompt = "You are a chatbot that helps build teams for VCT based on player data. Answer the following:\n\n"
        prompt_text = base_prompt + freeform_text
        linked_data_info = "Here are the teams:\n\n"

        if not any(entry['teams'] for entry in linked_data):
            return "Sorry, no team data is available."

        for entry in linked_data:
            for team_id, team in entry['teams'].items():
                linked_data_info += f"- Team: {team['name']}, Players: {[player['name'] for player in team['players']]}\n"

        prompt_text += linked_data_info

    else:
        prompt_text = "You are a chatbot that helps with general VCT esports inquiries. Please answer the following:\n\n" + freeform_text

    prompt = PromptTemplate(input_variables=["prompt_text"], template="{prompt_text}")
    bedrock_chain = LLMChain(llm=llm, prompt=prompt)

    try:
        response = bedrock_chain({"prompt_text": prompt_text})
    except Exception as e:
        return f"Sorry, there was an issue generating a response: {str(e)}"

    return response

# Load JSON Data
def load_json(folder_path):
    data = {
        "mapping_data": [],
        "players": [],
        "teams": [],
        "tournaments": [],
        "leagues": []
    }

    for file_name in os.listdir(folder_path):
        with open(os.path.join(folder_path, file_name), "r") as f:
            if file_name == "mapping_data.json":
                data["mapping_data"] = json.load(f)
            elif file_name == "players.json":
                player = json.load(f)
                data["players"][player["id"]] = player
            elif file_name == "teams.json":
                team = json.load(f)
                data["teams"][team["id"]] = team
            elif file_name == "tournaments.json":
                tournament = json.load(f)
                data["tournaments"][tournament["id"]] = tournament
            elif file_name == "leagues.json":
                league = json.load(f)
                data["leagues"][league["league_id"]] = league
    return data

# Link Data
def link_data(data):
    linked_data = []
    for mapping in data["mapping_data"]:
        team_info = {team_id: data["teams"][team_id] for team_id in mapping["teamMapping"].values() if team_id in data["teams"]}
        participant_info = {participant_id: data["players"][participant_id] for participant_id in mapping["participantMapping"].values() if participant_id in data["players"]}

        linked_data.append({
            "platformGameId": mapping["platformGameId"],
            "tournamentId": mapping["tournamentId"],
            "teams": team_info,
            "participants": participant_info,
            "tournament_info": data["tournaments"].get(mapping["tournamentId"], {}),
            "league_info": data["leagues"].get(data["tournaments"].get(mapping["tournamentId"], {}).get("league_id"), {})
        })
    return linked_data

# Main Program
folder_path = '../data'
data = load_json(folder_path)
linked_data = link_data(data)

# Streamlit UI
st.title("VCT Team Builder")
freeform_text = st.sidebar.text_area(label="Enter your question here", max_chars=100)

if freeform_text:
    response = vct_chatbot(freeform_text, linked_data)
    st.write(response)
