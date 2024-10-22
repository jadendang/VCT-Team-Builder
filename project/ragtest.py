from langchain.chains import LLMChain
from langchain_community.llms import Bedrock
from langchain.prompts import PromptTemplate
import boto3
import os
import streamlit as st
import json
import sys

sys.path.append(os.path.abspath('/Users/jadendang/Documents/GitHub/VCT-Team-Builder/project'))
from vlrdata.vlr_fetch import fetch_stats

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

region = "na"
timespan = "60"
scrape_data = fetch_stats(region, timespan)
print(scrape_data)

def vct_chatbot(freeform_text, scraped_data):
    if not scraped_data or 'data' not in scraped_data or 'segments' not in scraped_data['data']:
        return "Sorry, I couldn't retrieve any player statistics. Please try again later."
    
    base_prompt = "You are a chatbot that helps analyze player stats and build teams for VCT based on that data. The language is English.\n\n"
    prompt_text = base_prompt + freeform_text
   
    scraped_data_info = "Here are the player statistics: \n\n"
    player_count = 0
    for entry in scraped_data['data']['segments']:
        if player_count < 3:  # Limit to 3 players for concise output
            scraped_data_info += f"- Player: {entry['player']}, Org: {entry['org']}, Agents: {entry['agents']}, Roles: {entry['roles']}, Rounds Played: {entry['rounds_played']}, Rating: {entry['rating']}, ACS: {entry['average_combat_score']}, Avg Dmg per round: {entry['average_damage_per_round']}, Headshot %: {entry['headshot_percentage']}, Clutch %: {entry['clutch_success_percentage']}\n"
            player_count += 1
        else:
            break

    prompt_text += scraped_data_info
    prompt = PromptTemplate(input_variables=["prompt_text"], template="{prompt_text}")
    bedrock_chain = LLMChain(llm=llm, prompt=prompt)

    try:
        response = bedrock_chain({"prompt_text": prompt_text})
    except Exception as e:
        return f"Sorry, there was an issue generating a response: {str(e)}"

    return response

def load_json(folder_path):
    data = {
        "mapping_data": [],
        "players": [],
        "teams": [],
        "tournaments": [],
        "leagues": []
    }

    for file_name in os.listdir(folder_path):
        if file_name == "mapping_data.json":
            with open(os.path.join(folder_path, file_name), "r") as f:
                data["mapping_data"] = json.load(f)
        elif file_name == "players.json":
            with open(os.path.join(folder_path, file_name), "r") as f:
                player = json.load(f)
                data["players"][player["id"]] = player  # Use player ID as key
        elif file_name == "teams.json":
            with open(os.path.join(folder_path, file_name), "r") as f:
                team = json.load(f)
                data["teams"][team["id"]] = team  # Use team ID as key
        elif file_name == "tournaments.json":
            with open(os.path.join(folder_path, file_name), "r") as f:
                tournament = json.load(f)
                data["tournaments"][tournament["id"]] = tournament  # Use tournament ID as key
        elif file_name == "leagues.json":
            with open(os.path.join(folder_path, file_name), "r") as f:
                league = json.load(f)
                data["leagues"][league["league_id"]] = league  # Use league ID as key

    return data

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

folder_path = '../data'
data = load_json(folder_path)
linked_data = link_data(data)

# Streamlit UI
st.title("VCT Team Builder")

freeform_text = st.sidebar.text_area(label="What is your question", max_chars=100)

if freeform_text:
    response = vct_chatbot(freeform_text, scrape_data)
    st.write(response)

