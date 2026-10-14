import ast
import json

import requests

class SleeperData:
    """Class for getting and using data from Sleeper's API."""
    __user_name = None
    __league_id = None
    __draft_id = None
    __draft_order = -1

    def __init__(self, user_name="", league_id="", draft_id="", draft_order = -1):
        self.setUserName(user_name)
        self.setLeagueId(league_id)
        self.setDraftId(draft_id)
        self.setDraftOrder(draft_order)

    # HELPERS
    def getUserData(self) -> str:
        """Get the data for a sleeper user"""
        data_request = requests.get(f"https://api.sleeper.app/v1/user/{self.getUserName()}")
        return data_request.json()

    def getLeagueData(self) -> str:
        """Get data for a specific league"""
        data_request = requests.get(f"https://api.sleeper.app/v1/league/{self.getLeagueId()}")
        return data_request.json()

    def getDraftData(self) -> str:
        """Get data for a specific draft"""
        data_request = requests.get(f"https://api.sleeper.app/v1/draft/{self.getDraftId()}")
        return data_request.json()

    def getDraftPicks(self) -> str:
        """Get picks for a draft"""
        data_request = requests.get(f"https://api.sleeper.app/v1/draft/{self.getDraftId()}/picks")
        return data_request.json()

    def saveAllPlayers(self) -> None:
        """Only use once a day to generate daily info"""
        data_request = requests.get(f"https://api.sleeper.app/v1/players/nfl?active=true")
        with open("updated_players.txt", "w") as f:
            f.write(str(data_request.json()))

    # GETTERS AND SETTERS
    def getUserName(self):
        return self.__user_name

    def getLeagueId(self):
        return self.__league_id

    def getDraftId(self):
        return self.__draft_id

    def getDraftOrder(self):
        return self.__draft_order

    def setUserName(self, user_name):
        self.__user_name = user_name

    def setLeagueId(self, league_id):
        self.__league_id = league_id

    def setDraftId(self, draft_id):
        self.__draft_id = draft_id

    def setDraftOrder(self, draft_order):
        self.__draft_order = draft_order

    def filterPlayersFile(self):
        with open("updated_players.txt", "r") as f:
            players_file = f.read()
        players = ast.literal_eval(players_file)
        player_ids = list(players.keys())

        with open(f"updated_current_player_info.txt", "w") as f:
            for player_id in player_ids:
                player = players[player_id]
                try:
                    if player['team'] is not None and int(player['search_rank']) <= 750:
                        f.write(str(player))
                        f.write("\n")
                except Exception as e:
                    print("Search Rank not found...")