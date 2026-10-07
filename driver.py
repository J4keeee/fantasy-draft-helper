from google import genai
from gemini import Gemini
from sleeper import SleeperData
import time

sleeper = SleeperData("Jelf", "1407863657043353600", "1413350612417916928")
gemini = Gemini()

def main():

    print("*** Welcome to the Fantasy Draft Helper ***")
    end_program = False
    prev_round_number = -1


    while not end_program:
        user_input = input("\nWould you like your next pick suggestion? (Enter Y to Continue): ")

        if user_input.lower() == "y":

            new_round_data = False

            print("Retrieving Sleeper Data...")

            sleeper_request_counter = 0

            while not new_round_data:
                combined_data = retrieveSleeperData(prev_round_number)

                if combined_data:
                    gemini.suggest_pick(combined_data)
                    prev_round_number += 1
                    new_round_data = True
                else:
                    if sleeper_request_counter == 5:
                        print("Sorry, please try again, new draft data not found...")
                        new_round_data = True
                    else:
                        print("New data still not found...")
                        sleeper_request_counter += 1
                        time.sleep(5)





def retrieveSleeperData(prev_round_number):
    draft_picks = sleeper.getDraftPicks()
    round_number = draft_picks[-1]['round']

    if round_number == prev_round_number:
        return False

    else:
        user_data = str(sleeper.getUserData())
        league_data = str(sleeper.getLeagueData())
        draft_data = str(sleeper.getDraftData())

        combined_data = user_data + league_data + draft_data + str(draft_picks)

        print(round_number)

        with open("stats.txt", "w") as f:
            f.write(f"User Data: {user_data}\n")
            f.write(f"League Data: {league_data}\n")
            f.write(f"Draft Data: {draft_data}\n")
            f.write(f"Draft Picks: {draft_picks}\n")

        return combined_data


if __name__ == '__main__':
    main()