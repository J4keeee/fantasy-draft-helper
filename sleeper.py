import requests

class SleeperData:
    """Class for getting and using data from Sleeper's API."""

    def getUserData(user_name):
        """Get the data for a sleeper user"""
        return requests.get(f"https://api.sleeper.app/v1/user/{user_name}")

    def getLegueData(league_id):
        """Get data for a specific league"""
        return requests.get(f"https://api.sleeper.app/v1/league/{league_id}")

    def getDraftData(draft_id):
        """Get data for a specific draft"""
        return requests.get(f"https://api.sleeper.app/v1/draft/{draft_id}")

    def getDraftPicks(draft_id):
        """Get picks for a draft"""
        return requests.get(f"https://api.sleeper.app/v1/draft/{draft_id}/picks")