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
import logging
import re
from fuzzywuzzy import fuzz  # Added fuzzy matching library
from fuzzywuzzy import process  # Import fuzzy matching function

# Set up AWS profile
os.environ["AWS_PROFILE"] = "Hackthon"  # Ensure this profile has permissions for Tokyo region

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

# Setup logging
logging.basicConfig(level=logging.INFO)

# Chatbot function
def vct_chatbot(freeform_text, linked_data):
    if not linked_data:
        return "Sorry, I couldn't find any relevant data right now. Please try again later."

    # Check if query is for a specific player or team
    player_name_query = None
    team_name_query = None
    player_name_keywords = ["player", "tell me about", "information on", "who is"]
    team_name_keywords = ["team", "who is team"]

    # Identify if the query contains any keywords for player or team information
    if any(keyword in freeform_text.lower() for keyword in player_name_keywords):
        # Extract possible player name
        potential_name = re.findall(r'\b(?:' + '|'.join(player_name_keywords) + r')\s+([\w\s]+)', freeform_text.lower())
        if potential_name:
            player_name_query = potential_name[0].strip().lower()
    elif any(keyword in freeform_text.lower() for keyword in team_name_keywords):
        # Extract possible team name
        potential_name = re.findall(r'\b(?:' + '|'.join(team_name_keywords) + r')\s+([\w\s]+)', freeform_text.lower())
        if potential_name:
            team_name_query = potential_name[0].strip().lower()

    if player_name_query:
        # Search for player data in linked_data
        player_data_found = False
        linked_data_info = "Player stats:\n\n"
        for entry in linked_data:
            for player_id, player in entry['participants'].items():
                player_name = player.get('name', '').lower()
                # Use fuzzy matching to allow partial name matches
                if fuzz.partial_ratio(player_name_query, player_name) > 80:  # Increased threshold for fuzzy matching
                    linked_data_info += f"- Player: {player.get('name', 'Unknown')}, Org: {player.get('org', 'Unknown')}, Agents: {player.get('agents', 'Unknown')}, Roles: {player.get('roles', 'Unknown')}\n"
                    player_data_found = True
            if player_data_found:
                break  # Stop after finding the player data

        if not player_data_found:
            return f"Sorry, no data available for {player_name_query.capitalize()}."

        prompt_text = linked_data_info
    elif team_name_query:
        # Search for team data in linked_data
        team_data_found = False
        linked_data_info = "Team stats:\n\n"
        for entry in linked_data:
            for team_id, team in entry['teams'].items():
                team_name = team.get('name', '').lower()
                if fuzz.partial_ratio(team_name_query, team_name) > 80:  # Increased threshold for fuzzy matching
                    linked_data_info += f"- Team: {team.get('name', 'Unknown')}, Region: {team.get('region', 'Unknown')}, Players: {', '.join([player.get('name', 'Unknown') for player in team.get('players', [])])}\n"
                    team_data_found = True
            if team_data_found:
                break  # Stop after finding the team data

        if not team_data_found:
            return f"Sorry, no data available for team {team_name_query.capitalize()}."

        prompt_text = linked_data_info
    else:
        # Default prompt if it's not a player or team query
        prompt_text = "You are a chatbot that helps with general VCT esports inquiries. Please answer the following:\n\n" + freeform_text

    prompt = PromptTemplate(input_variables=["prompt_text"], template="{prompt_text}")
    bedrock_chain = LLMChain(llm=llm, prompt=prompt)

    retry_attempts = 2  # Fewer attempts to reduce request overload
    for attempt in range(retry_attempts):
        try:
            logging.info(f"Attempt {attempt + 1} running Bedrock Chain...")
            response = bedrock_chain.run(prompt_text=prompt_text)
            
            # Adding delay to avoid hitting the API request limit
            time.sleep(0.5)  # 500ms delay (2 requests per second)
            
            return response
        except Exception as e:
            logging.error(f"Error on attempt {attempt + 1}: {str(e)}")
            if "ThrottlingException" in str(e):
                wait_time = (2 ** (attempt + 1)) * 5 + random.uniform(1, 2)  # Increased base wait time
                logging.info(f"Throttled, retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                return f"Sorry, there was an issue generating a response: {str(e)}"

    logging.warning("Request limit reached after retrying.")
    return "Request limit reached. Please try again later."


# Load JSON Data
def load_json(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        logging.error(f"Error: Folder path '{folder_path}' does not exist.")
        sys.exit(f"Error: Folder path '{folder_path}' does not exist.")

    # Print the contents of the folder to verify
    logging.info("Contents of folder: %s", os.listdir(folder_path))

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
                logging.info(f"Loading file: {file_name}")
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        content = json.load(f)
                    except json.JSONDecodeError as e:
                        logging.error(f"Skipping file {file_name} due to JSON decode error: {e}")
                        continue

                    if file_name == "mapping_data.json" or file_name.startswith("mapping_data_v2"):
                        data["mapping_data"].extend(content)  # To load all mapping files
                        logging.info(f"Loaded {len(content)} mappings from {file_name}")
                    elif file_name == "players.json":
                        if isinstance(content, list):
                            for player in content:
                                data["players"][player["id"]] = player
                        elif isinstance(content, dict):
                            data["players"].update(content)
                        logging.info(f"Loaded {len(data['players'])} players from players.json")
                        logging.info(f"Player data loaded: {data['players']}")  # New detailed log
                    elif file_name == "teams.json":
                        if isinstance(content, list):
                            for team in content:
                                data["teams"][team["id"]] = team
                        elif isinstance(content, dict):
                            data["teams"].update(content)
                        logging.info(f"Loaded {len(data['teams'])} teams from teams.json")
                    elif file_name == "tournaments.json":
                        if isinstance(content, list):
                            for tournament in content:
                                data["tournaments"][tournament["id"]] = tournament
                        elif isinstance(content, dict):
                            data["tournaments"].update(content)
                        logging.info(f"Loaded {len(data['tournaments'])} tournaments from tournaments.json")
                    elif file_name == "leagues.json":
                        if isinstance(content, list):
                            for league in content:
                                data["leagues"][league["league_id"]] = league
                        elif isinstance(content, dict):
                            data["leagues"].update(content)
                        logging.info(f"Loaded {len(data['leagues'])} leagues from leagues.json")
    except Exception as e:
        sys.exit(f"Error loading JSON files: {str(e)}")

    logging.info(f"Data loaded from folder: {json.dumps(data, indent=2)}")
    return data


def link_data(data):
    linked_data = []
    for mapping in data["mapping_data"]:
        linked_team_data = {}
        linked_participant_data = {}

        # Link team data
        for team_id in mapping.get("teamMapping", {}).values():
            team_id_normalized = team_id.strip().lower()  # Normalize team ID
            logging.info(f"Original team ID: {team_id}, Normalized: {team_id_normalized}")
            if team_id_normalized in data["teams"]:
                linked_team_data[team_id_normalized] = data["teams"][team_id_normalized]
                logging.info(f"Linked team: {data['teams'][team_id_normalized].get('name', 'Unknown')}")
            else:
                logging.warning(f"Team ID '{team_id}' not found in team data.")

        # Link participant data
        for participant_id in mapping.get("participantMapping", {}).values():
            participant_id_normalized = participant_id.strip().lower()  # Normalize participant ID
            logging.info(f"Original participant ID: {participant_id}, Normalized: {participant_id_normalized}")
            if participant_id_normalized in data["players"]:
                linked_participant_data[participant_id_normalized] = data["players"][participant_id_normalized]
                logging.info(f"Linked participant: {data['players'][participant_id_normalized].get('name', 'Unknown')}")
            else:
                # Fuzzy matching as a fallback to find closest match
                logging.warning(f"Participant ID '{participant_id}' not found in players data. Attempting fuzzy match...")
                all_ids = list(data["players"].keys())
                best_match, match_score = process.extractOne(participant_id_normalized, all_ids)
                logging.info(f"Best match for '{participant_id_normalized}' is '{best_match}' with score {match_score}")
                if match_score > 80:  # Set a threshold for matching accuracy
                    linked_participant_data[best_match] = data["players"][best_match]
                    logging.info(f"Fuzzy linked participant: {data['players'][best_match].get('name', 'Unknown')} (Match Score: {match_score})")
                else:
                    logging.warning(f"No close match found for participant ID '{participant_id_normalized}'.")

        # Print out all player names to verify data linkage
        player_names = [
            data["players"].get(participant_id.strip().lower(), {}).get('name', 'Unknown')
            for participant_id in mapping.get("participantMapping", {}).values()
        ]
        logging.info("Participants in mapping: %s", player_names)

        linked_data.append({
            "platformGameId": mapping.get("platformGameId", ""),
            "tournamentId": mapping.get("tournamentId", ""),
            "teams": linked_team_data,
            "participants": linked_participant_data,
            "tournament_info": data["tournaments"].get(mapping.get("tournamentId", ""), {}),
            "league_info": data["leagues"].get(data["tournaments"].get(mapping.get("tournamentId", ""), {}).get("league_id", ""), {})
        })

    logging.info(f"Total number of linked mappings: {len(linked_data)}")
    if linked_data:
        logging.info(f"Linked data example: {json.dumps(linked_data[0], indent=2)}")
    else:
        logging.error("No linked data was created.")
    return linked_data


# Main Program
folder_path = '/Users/shadmanshahzahan/Downloads/VCT/VCT-Team-Builder/project/esports-data'

data = load_json(folder_path)
linked_data = link_data(data)

# Streamlit UI
st.title("VCT Team Builder")
freeform_text = st.sidebar.text_area(label="Enter your question here", max_chars=100)

if freeform_text:
    logging.info(f"User query: {freeform_text}")
    response = vct_chatbot(freeform_text, linked_data)
    st.write(response)






