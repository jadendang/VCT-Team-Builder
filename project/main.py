from langchain.chains import LLMChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import boto3
import os
import streamlit as st
import json

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

def vct_chatbot(language, freeform_text, linked_data):
    base_prompt = "You are a chatbot that helps build teams for VCT based on game data. You are in {language}.\n\n{freeform_text}"

    linked_data_info = "Here is the tournament information: \n\n"
    for entry in linked_data:
        linked_data_info += f"- Platform Game ID: {entry['platformGameId']}, Teams: {entry['teams']}, Participants: {entry['participants']}, Tournament: {entry['tournament_info'].get('name', 'N/A')}\n"

    promp_text = base_prompt + linked_data_info

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

st.title("VCT Team Builder")

# language = st.selectbox("Select Language", ("English"))

freeform_text = st.sidebar.text_area(label="Enter your text here", max_chars=100)

if freeform_text:
    response = vct_chatbot("English", freeform_text, linked_data)
    st.write(response)

