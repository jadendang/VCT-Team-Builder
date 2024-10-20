import requests
from selectolax.parser import HTMLParser

from utils.utils import headers, agent_roles


def fetch_stats(region: str, timespan: str):
    base_url = f"https://www.vlr.gg/stats/?event_group_id=all&event_id=all&region={region}&country=all&min_rounds=200&min_rating=1550&agent=all&map_id=all"
    url = (
        f"{base_url}&timespan=all"
        if timespan.lower() == "all"
        else f"{base_url}&timespan={timespan}d"
    )

    resp = requests.get(url, headers=headers)
    html = HTMLParser(resp.text)
    status = resp.status_code

    result = []

    for item in html.css("tbody tr"):
        player = item.text().replace("\t", "").replace("\n", " ").strip().split()
        player_name = player[0]
        org = player[1] if len(player) > 1 else "N/A"

        agents = [
            agents.attributes["src"].split("/")[-1].split(".")[0]
            for agents in item.css("td.mod-agents img")
        ]

        roles = [agent_roles.get(agent, "Unknown") for agent in agents]

        color_sq = [stats.text() for stats in item.css("td.mod-color-sq")]
        rnd = item.css_first("td.mod-rnd").text() if item.css_first("td.mod-rnd") else "N/A"

        result.append(
            {
                "player": player_name,
                "org": org,
                "agents": agents,
                "roles": roles,
                "rounds_played": rnd,
                "rating": color_sq[0] if len(color_sq) > 0 else "N/A",
                "average_combat_score": color_sq[1] if len(color_sq) > 1 else "N/A",
                "kill_deaths": color_sq[2] if len(color_sq) > 2 else "N/A",
                "kill_assists_survived_traded": color_sq[3] if len(color_sq) > 3 else "N/A",
                "average_damage_per_round": color_sq[4] if len(color_sq) > 4 else "N/A",
                "kills_per_round": color_sq[5] if len(color_sq) > 5 else "N/A",
                "assists_per_round": color_sq[6] if len(color_sq) > 6 else "N/A",
                "first_kills_per_round": color_sq[7] if len(color_sq) > 7 else "N/A",
                "first_deaths_per_round": color_sq[8] if len(color_sq) > 8 else "N/A",
                "headshot_percentage": color_sq[9] if len(color_sq) > 9 else "N/A",
                "clutch_success_percentage": color_sq[10] if len(color_sq) > 10 else "N/A",
            }
        )

    segments = {"status": status, "segments": result}
    data = {"data": segments}

    if status != 200:
        raise Exception("API response: {}".format(status))
    return data