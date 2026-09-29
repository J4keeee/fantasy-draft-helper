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
        data_request = requests.get(f"https://api.sleeper.app/v1/user/{self.getUserName}")
        return data_request.json()

    def getLeagueData(self) -> str:
        """Get data for a specific league"""
        data_request = requests.get(f"https://api.sleeper.app/v1/league/{self.getLeagueId}")
        return data_request.json()

    def getDraftData(self) -> str:
        """Get data for a specific draft"""
        data_request = requests.get(f"https://api.sleeper.app/v1/draft/{self.getDraftId}")
        return data_request.json()

    def getDraftPicks(self) -> str:
        """Get picks for a draft"""
        data_request = requests.get(f"https://api.sleeper.app/v1/draft/{self.getDraftId}/picks")
        return data_request.json()

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