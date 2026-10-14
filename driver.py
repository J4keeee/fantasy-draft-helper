from google import genai
from gemini import Gemini
from sleeper import SleeperData
import time

sleeper = SleeperData("J4ke117", "1407863657043353600", "1416073162810003456", 5)
gemini = Gemini()

def main():

    print("*** Welcome to the Fantasy Draft Helper ***")
    end_program = False

    while not end_program:

        combined_data, drafted_players = retrieveSleeperData()

        if combined_data:
            input("Ready to Draft! Hit enter to get suggested picks")

            print("Getting info from gemini...")
            gemini.suggest_pick(combined_data, drafted_players=drafted_players)
            time.sleep(45)

def retrieveSleeperData():
    draft_picks = sleeper.getDraftPicks()
    drafted_players = sleeper.getDraftedPlayers(draft_picks)

    if draft_picks:
        current_draft_slot = draft_picks[-1]['draft_slot']
        print(f"Draft picks -1: {draft_picks[-1]}")
    else:
        current_draft_slot = 1

    draft_slot_difference = abs(sleeper.getDraftOrder() - current_draft_slot)

    if draft_slot_difference > 1:
        print(f"Waiting for {0.5} second...")
        time.sleep(0.5)
        return None, None

    else:
        user_data = str(sleeper.getUserData())
        league_data = str(sleeper.getLeagueData())
        draft_data = str(sleeper.getDraftData())

        combined_data = user_data + league_data + draft_data + str(draft_picks)

        with open("stats.txt", "w") as f:
            f.write(f"User Data: {user_data}\n")
            f.write(f"League Data: {league_data}\n")
            f.write(f"Draft Data: {draft_data}\n")
            f.write(f"Draft Picks: {draft_picks}\n")

        return combined_data, drafted_players


if __name__ == '__main__':
    main()