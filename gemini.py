from google import genai
from google.genai import types

class Gemini:
    __client = None
    __system_prompt = None


    def __init__(self):
        self.initialize()

    def initialize(self):
        self.setClient(genai.Client(api_key="AQ.Ab8RN6IAioGw-XkvBVo2dl85iTWXUeoBk415mYem6d6j6t_0Mg"))

    def interact(self, user_input=""):
        interaction = self.getClient().interactions.create(
            config=types.GenerateContentConfig( system_instruction = self.getSystemPrompt()),
            model="gemini-3.5-flash-lite",
            input = user_input
        )

        print(interaction.output_text)


    def getClient(self) -> genai.Client:
        return self.__client

    def getSystemPrompt(self) -> str:
        return self.__system_prompt

    def setClient(self, client):
        self.__client = client

    def setSystemPrompt(self, system_prompt):
        self.__system_prompt = system_prompt