from google import genai
from gemini import Gemini
from sleeper import SleeperData

sleeper = SleeperData()
gemini = Gemini()

def main():

    user_data = str(sleeper.getUserData("Jelf").json())
    league_data = str(sleeper.getLegueData("1407863657043353600").json())
    draft_data = str(sleeper.getDraftData("1408953047333326848").json())
    draft_picks = str(sleeper.getDraftPicks("1408953047333326848").json())
    combined_data = user_data + league_data + draft_data + draft_picks


    suggest_pick(combined_data)


def suggest_pick(draft_information):
    gemini.interact("Based on this information, which player should I pick next?. Give me a concise and specific answer, give me names. Then, give me three concise bullet points on why I should pick that player." + draft_information)




if __name__ == '__main__':
    main()