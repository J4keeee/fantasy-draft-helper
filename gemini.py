from certifi import contents
from google import genai
from google.genai import types

class Gemini:
    __client = None
    __system_prompt = None
    __start_of_season_data = None
    __current_season_data = None

    def __init__(self):
        self.initialize()

    def initialize(self):
        self.setClient(genai.Client(api_key="AQ.Ab8RN6IAioGw-XkvBVo2dl85iTWXUeoBk415mYem6d6j6t_0Mg"))
        self.setSystemPrompt(
                                """You are a NFL fantasy draft expert, your goal is to provide the user with a fantasy football lineup with the best chance of winning the season
                                Follow these rules:
                                    - Provide the user with three options and specific player names/positions
                                    - Provide a few concise bullet points for why the user should choose those players
                                    - Consider the previous picks that the user has chosen when providing suggested picks
                                    - Pay special attention to the Draft Picks Data to Consider the picks that the other players in the league have made to avoid suggesting a pick that has already been done. (For Example, if you see Draft Picks: [{'draft_id': '1415899504514760704', 'draft_slot': 1, 'is_keeper': None, 'metadata': {'first_name': 'Bijan', 'injury_status': '', 'last_name': 'Robinson', then don't suggest Bijan Robinson to me because he has already been picked.
                                    - Adjust your draft criteria according to any football specific prompts given by the user
                                    
                                Avoid:
                                    - Don't give overly wordy analysis's
                                    - Don't tell the user to pick a vague position without a specific player attached
                                    - Don't suggest a low ranked player without facts and reason behind it
                                    - Do not suggest a player which has already been chosen in the provided draft picks
                                    - You only know information about football, don't answer anything that doesn't have to do with the NFL, NFL players, or Fantasy Football.
                                    - Your goal is not to answer problems directly, it is to suggest players.
                                    """
                            )

        self.setStartOfSeasonData(self.getClient().files.upload(file="football.csv"))
        self.setCurrentSeasonData(self.getClient().files.upload(file="updated_current_player_info.txt"))

    def interact(self, prompt="", blacklist=""):
        start_of_season_data = self.getStartOfSeasonData()
        current_season_data = self.getCurrentSeasonData()

        interaction = self.getClient().interactions.create(
            system_instruction = self.getSystemPrompt() + blacklist,
            model="gemini-3.5-flash-lite",
            input = [
                        {"type": "document", "uri":start_of_season_data.uri, "mime_type": self.getStartOfSeasonData().mime_type},
                        {"type": "document", "uri":current_season_data.uri, "mime_type": current_season_data.mime_type},
                        {"type": "text", "text": prompt}
                    ]
        )

        print(interaction.output_text)

    def suggest_pick(self, user_prompt=None, drafted_players=None, roster_positions=None):
        prompt = f"Suggest the next pick for the user with the NFL season information given. The user may provide additional input, if so it is given here:\n{user_prompt}."
        self.interact(prompt, self.buildBlacklistPrompt(drafted_players or [], roster_positions))

    def buildBlacklistPrompt(self, drafted_players, roster_positions) -> str:
        def line(p):
            return f"- {p['name']} ({p['position']}, {p['team']}, id {p['player_id']})"

        taken = "\n".join(line(p) for p in drafted_players) or "- (none yet)"
        mine = "\n".join(line(p) for p in drafted_players if p["is_mine"]) or "- (none yet)"

        return  f"""
                    UNAVAILABLE PLAYERS - already drafted, NEVER suggest any of these ({len(drafted_players)} total):
                    {taken}

                    USER'S ROSTER SO FAR (consider positional needs; these are also unavailable):
                    {mine}
                    
                    ROSTER POSITIONS - Make sure that the user's roster meets the roster needs:
                    {roster_positions}
                """

    # GETTERS AND SETTERS
    def getClient(self) -> genai.Client:
        return self.__client

    def getSystemPrompt(self) -> str:
        return self.__system_prompt

    def getStartOfSeasonData(self):
        return self.__start_of_season_data

    def getCurrentSeasonData(self):
        return self.__current_season_data

    def setClient(self, client):
        self.__client = client

    def setSystemPrompt(self, system_prompt):
        self.__system_prompt = system_prompt

    def setStartOfSeasonData(self, start_of_season_data):
        self.__start_of_season_data = start_of_season_data

    def setCurrentSeasonData(self, current_season_data):
        self.__current_season_data = current_season_data