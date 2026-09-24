from google import genai

class Gemini:
    client = None

    def __init__(self):
        self.initialize()

    def initialize(self):
        self.client = genai.Client(api_key="AQ.Ab8RN6IAioGw-XkvBVo2dl85iTWXUeoBk415mYem6d6j6t_0Mg")

    def interact(self, user_input="Tell me a one sentence summary of what you do"):
        interaction = self.client.interactions.create(
            model="gemini-3.5-flash-lite",
            input = user_input
        )

        print(interaction.output_text)