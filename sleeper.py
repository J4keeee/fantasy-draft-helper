import ast
import requests

class SleeperData:
    """Class for getting and using data from Sleeper's API."""
    __user_name = None
    __league_id = None
    __draft_id = None

    def __init__(self, user_name="", league_id="", draft_id=""):
        self.setUserName(user_name)
        self.setLeagueId(league_id)
        self.setDraftId(draft_id)

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

    def getDraftedPlayers(self, picks=None) -> list[dict]:
        """Every player already taken in the draft, in pick order"""
        if picks is None:
                picks = self.getDraftPicks()

        drafted = []
        for pick in sorted(picks, key=lambda p: p["pick_no"]):
            meta = pick.get("metadata", {})
            drafted.append({
                "pick_no": pick["pick_no"],
                "player_id": pick["player_id"],
                "name": f"{meta.get('first_name', '')} {meta.get('last_name', '')}".strip(),
                "position": meta.get("position", ""),
                "team": meta.get("team", ""),
                "is_mine": pick["draft_slot"] == self.getDraftOrder()
            })

        return drafted

    def getRosterPositions(self) -> str:
        """The positions that will need to be filled in the user's roster"""
        league_data = self.getLeagueData()
        roster_positions = league_data['roster_positions']

        return roster_positions

    def getDraftOrder(self) -> int:
        """The order which the user will draft in each round"""
        draft_data = self.getDraftData()
        draft_order_key = draft_data['draft_order'].keys()

        for key in draft_order_key:
            draft_order = int(draft_data['draft_order'][key])

        return draft_order

    def getRounds(self) -> int:
        """The number of rounds in the draft"""
        draft_data = self.getDraftData()
        draft_settings = draft_data['settings']
        rounds = int(draft_settings['rounds'])

        return rounds

    def getPickNumber(self) -> int:
        """The current pick number in the draft"""
        draft_picks = self.getDraftPicks()

        if draft_picks is None:
            pick_number = 1
        else:
            current_pick = draft_picks[-1]
            pick_number = int(current_pick['pick_no']) + 1

        return pick_number

    def getCurrentRound(self) -> int:
        """The current round in the draft"""
        draft_picks = self.getDraftPicks()

        if draft_picks is None:
            current_round = 1
        else:
            current_pick = draft_picks[-1]
            current_round = int(current_pick['round'])

        return current_round


    def saveAllPlayers(self) -> None:
        """Only use once a day to generate daily info"""
        data_request = requests.get(f"https://api.sleeper.app/v1/players/nfl?active=true")
        with open("updated_players.txt", "w") as f:
            f.write(str(data_request.json()))

    def filterPlayersFile(self):
        """Filters the player list so that it is more mangable for the agent to process"""
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

    # GETTERS AND SETTERS
    def getUserName(self):
        return self.__user_name

    def getLeagueId(self):
        return self.__league_id

    def getDraftId(self):
        return self.__draft_id

    def setUserName(self, user_name):
        self.__user_name = user_name

    def setLeagueId(self, league_id):
        self.__league_id = league_id

    def setDraftId(self, draft_id):
        self.__draft_id = draft_id