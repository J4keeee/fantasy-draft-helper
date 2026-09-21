import requests

class SleeperData:
    """Class for getting and using data from Sleeper's API."""

    def testing():
        # Get User Data via username
        x = requests.get("https://api.sleeper.app/v1/user/J4ke117")
        print("--- USER DATA ---\n" + str(x.json()) + "\n\n")

        # Get League data with a league id
        y = requests.get("https://api.sleeper.app/v1/league/1407863657043353600")
        print("--- LEAGUE DATA ---\n" + str(y.json()) + "\n\n")

        # Get draft data with a draft id
        z = requests.get("https://api.sleeper.app/v1/draft/1407869304355016704")
        print("--- DRAFT DATA ---\n" + str(y.json()) + "\n\n")

        # Get draft picks
        a = requests.get("https://api.sleeper.app/v1/draft/1407869304355016704/picks")
        print("--- DRAFT PICKS ---\n" + str(a.json()) + "\n\n")

def main():
    SleeperData.testing()

if __name__ == "__main__":
    main()