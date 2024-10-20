from langchain.chains import LLMChain
from langchain_community.llms import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import boto3
import os
import streamlit as st
import json
import sys

sys.path.append(os.path.abspath('/Users/jadendang/Documents/GitHub/VCT-Team-Builder/project'))
from vlrdata.vlr_fetch import fetch_stats


os.environ["AWS_PROFILE"] = "vscode"

#Bedrock Client

bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

modelID = "anthropic.claude-v2:1"

llm = Bedrock(
    model_id=modelID,
    client=bedrock_client,
    model_kwargs={"max_tokens_to_sample": 2000,"temperature": 0.9}
)

# def chatbot(language, freeform_text):
#     prompt = PromptTemplate(
#         input_variables=["language", "freeform_text"],
#         template="You are a chatbot. You are in {language}.\n\n{freeform_text}"
#     )

#     bedrock_chain = LLMChain(llm=llm, prompt=prompt)

#     response=bedrock_chain({"language": language, "freeform_text": freeform_text})

#     return response

# def vct_chatbot(language, freeform_text, linked_data):
#     base_prompt = "You are a chatbot that helps build teams for VCT based on game data. You are in {language}.\n\n{freeform_text}"

#     linked_data_info = "Here is the tournament information: \n\n"
#     for entry in linked_data:
#         linked_data_info += f"- Platform Game ID: {entry['platformGameId']}, Teams: {entry['teams']}, Participants: {entry['participants']}, Tournament: {entry['tournament_info'].get('name', 'N/A')}\n"

#     promp_text = base_prompt + linked_data_info

#     prompt = PromptTemplate(
#         input_variables=["prompt_text"],
#         template="{prompt_text}"
#     )

#     bedrock_chain = LLMChain(llm=llm, prompt=prompt)
#     response = bedrock_chain({"prompt_text": promp_text})

    # return response

region = "na"
timespan = "60"
scrape_data = fetch_stats(region, timespan)
print(scrape_data)

def vct_chatbot(freeform_text, scraped_data):
    base_prompt = """
    You are a chatbot that helps analyze player stats and build teams for VCT based on that data. The language is English

    {freeform_text}
    """

    scraped_data_info = "Here are the player statistics: \n\n"
    for entry in scraped_data['data']['segments']:
        scraped_data_info += f"- Player: {entry['player']}, Org: {entry['org']}, Agents: {entry['agents']}, Rounds Played: {entry['rounds_played']}, Rating: {entry['rating']}, ACS: {entry['average_combat_score']}, Avg Dmg per round: {entry['average_damage_per_round']}, Headshot %: {entry['headshot_percentage']}, Clutch %: {entry['clutch_success_percentage']}\n"

    promp_text = base_prompt.format(freeform_text=freeform_text) + scraped_data_info

    prompt = PromptTemplate(
        input_variables=["prompt_text"],
        template="{prompt_text}"
    )

    bedrock_chain = LLMChain(llm=llm, prompt=prompt)
    response = bedrock_chain({"prompt_text": promp_text})

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

# print(chatbot("English", "What is the capital of Canada?"))

# Streamlit UI

st.title("VCT Team Builder")

# language = st.selectbox("Select Language", ("English"))

freeform_text = st.sidebar.text_area(label="What is your question", max_chars=100)

if freeform_text:
    response = vct_chatbot(freeform_text, scrape_data)
    st.write(response)

