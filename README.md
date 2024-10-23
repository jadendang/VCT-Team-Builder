# VCT Team Builder

Welcome to **VCT Team Builder**! This project aims to provide valuable insights into player statistics, team compositions, and more for Valorant Championship Tour (VCT) enthusiasts, coaches, and analysts. Leveraging Amazon Bedrock's AI capabilities, the chatbot offers easy access to data-driven answers, supporting better team management and strategic decision-making.

## Table of Contents
- [About the Project](#about-the-project)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Limitations](#limitations)
- [License](#license)

## About the Project
The VCT Team Builder is an AI-powered chatbot designed to provide quick and insightful answers related to VCT esports players, teams, and tournament data. It aims to simplify the process of analyzing player statistics and building effective teams for coaches, analysts, and even casual fans of Valorant esports.

## Features
- **Data-Driven Insights**: Get quick and detailed statistics about players, including their team, roles, agents used, and more.
- **AI Chatbot Interaction**: Conversational chatbot that can answer questions about teams, players, and general esports-related inquiries.
- **Easy Data Integration**: Automatically link team, player, and tournament data from multiple sources for up-to-date insights.

## Technology Stack
- **AWS Bedrock**: For AI foundation models and inference.
- **LangChain**: Framework used to build and manage LLM-powered chains.
- **Streamlit**: Web framework used to create an interactive and easy-to-use interface.
- **Python**: Core programming language used to implement the application.
- **Boto3**: AWS SDK for Python to interact with AWS Bedrock.

## Getting Started
To get a local copy up and running, follow these steps:

### Prerequisites
- Python 3.8 or higher
- AWS credentials configured
- Streamlit
- Boto3

### Installation
1. Clone the repo:
   ```sh
   git clone https://github.com/your_username/VCT-Team-Builder.git
   cd VCT-Team-Builder
   ```
2. Create a virtual environment and activate it:
   ```sh
   python -m venv myenv
   source myenv/bin/activate  # On Windows, use `myenv\Scripts\activate`
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up AWS credentials:
   - Configure AWS CLI with your credentials and set the profile as `Hackthon`.

## Usage
1. To run the Streamlit app, use the following command:
   ```sh
   streamlit run main.py
   ```
2. Enter your question in the text area and get instant AI-generated responses related to VCT players, teams, and more.

### Example Queries
- "Tell me about player TenZ"
- "What are the details of Team Liquid?"

The chatbot will analyze the linked data and provide insights accordingly.

## Limitations
- **Incomplete Features**: The chatbot is a rough model, and many functionalities are not fully developed yet.
- **Chatbot Issues**: The chatbot may not provide consistent or accurate answers for all queries, as it is still a work in progress.

## License
Distributed under the MIT License. See `LICENSE` for more information.
