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

        my_slot = self.getDraftOrder()
        drafted = []
        for pick in sorted(picks, key=lambda p: p["pick_no"]):
            meta = pick.get("metadata", {})
            drafted.append({
                "pick_no": pick["pick_no"],
                "player_id": pick["player_id"],
                "name": f"{meta.get('first_name', '')} {meta.get('last_name', '')}".strip(),
                "position": meta.get("position", ""),
                "team": meta.get("team", ""),
                "is_mine": pick["draft_slot"] == my_slot
            })

        return drafted

    def getRosterPositions(self) -> str:
        """The positions that will need to be filled in the user's roster"""
        league_data = self.getLeagueData()
        roster_positions = league_data['roster_positions']

        return roster_positions

    def getDraftOrder(self) -> int:
        """The order which the user will draft in each round"""
        user_id = self.getUserData()['user_id']
        draft_order = self.getDraftData()['draft_order']

        return int(draft_order[user_id])

    def getRounds(self) -> int:
        """The number of rounds in the draft"""
        draft_data = self.getDraftData()
        draft_settings = draft_data['settings']
        rounds = int(draft_settings['rounds'])

        return rounds

    def getPickNumber(self) -> int:
        """The current pick number in the draft"""
        draft_picks = self.getDraftPicks()

        if not draft_picks:
            return 1
        return int(draft_picks[-1]['pick_no']) + 1

    def getCurrentRound(self) -> int:
        """The current round in the draft"""
        return (self.getPickNumber() - 1) // self.getTeams() + 1

    def getTeams(self) -> int:
        """The number of teams in the draft"""
        return int(self.getDraftData()['settings']['teams'])

    def saveAllPlayers(self) -> None:
        """Only use once a day to generate daily info"""
        data_request = requests.get(f"https://api.sleeper.app/v1/players/nfl?active=true")
        with open("data/updated_players.txt", "w") as f:
            f.write(str(data_request.json()))

    FANTASY_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")
    def filterPlayersFile(self):
        """Writes a short line per player to give the AI less to process"""
        with open("data/updated_players.txt", "r") as f:
            players = ast.literal_eval(f.read())

        keep = []
        for player in players.values():
            rank = player.get("search_rank")
            if player.get("team") and rank is not None and int(rank) <= 750 and player.get("position") in self.FANTASY_POSITIONS:
                keep.append(player)

        keep.sort(key=lambda p: int(p["search_rank"]))

        with open("data/updated_current_player_info.txt", "w") as f:
            f.write("rank | name | pos | team | age | years exp | depth chart | injury\n")
            for p in keep:
                name = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name')}".strip()
                f.write(f"{p['search_rank']} | {name} | {p['position']} | {p['team']} | {p.get('age')} | {p.get('years_exp')} | {p.get('depth_chart_order')} | {p.get('injury_status') or "healthy"}\n")

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