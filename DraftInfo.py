from sleeper import SleeperData

class DraftInfo:
    """Class which is used to communicate with the interface to determine what is shown to the user"""
    __roster_positions = None
    __users_draft_order = -1
    __current_pick_number = -1
    __users_draft_slots = []
    __user_can_draft = False
    __current_round = -1
    __rounds = -1
    __teams = 10

    def __init__(self, roster_positions=None, users_draft_order=-1, current_pick_number=-1, users_draft_slots=None, user_can_draft=False, current_round=-1, rounds=None, teams=10):
        self.setRosterPositions(roster_positions)
        self.setUsersDraftOrder(users_draft_order)
        self.setCurrentPickNumber(current_pick_number)
        self.setUsersDraftSlots(users_draft_slots)
        self.setUserCanDraft(user_can_draft)
        self.setRounds(rounds)
        self.setCurrentRound(current_round)
        self.setTeams(teams)

    #HELPERS
    def determineUsersDraftSlots(self) -> None:
        """Determines the draft slots of the user to determine when they can draft or not"""

        users_draft_slots = []
        teams = self.getTeams()
        for i in range(1, self.getRounds() + 1):
            if i % 2 == 0:
                pick_number = (i * teams) - (self.getUsersDraftOrder() - 1)
            else:
                pick_number = ((i-1) * teams) + self.getUsersDraftOrder()

            users_draft_slots.append(pick_number)

        self.setUsersDraftSlots(users_draft_slots)

    def determineDraftStatus(self) -> None:
        """Checks the current pick number against the users draft slots to see if they are able to draft currently"""

        if self.getCurrentPickNumber() in self.getUsersDraftSlots():
            self.setUserCanDraft(True)
        else:
            self.setUserCanDraft(False)

    # GETTERS AND SETTERS
    def getRosterPositions(self):
        return self.__roster_positions

    def getUsersDraftOrder(self):
        return self.__users_draft_order

    def getCurrentPickNumber(self):
        return self.__current_pick_number

    def getUsersDraftSlots(self):
        return self.__users_draft_slots

    def getUserCanDraft(self):
        return self.__user_can_draft

    def getCurrentRound(self):
        return self.__current_round

    def getRounds(self):
        return self.__rounds

    def getTeams(self):
        return self.__teams

    def setRosterPositions(self, roster_positions):
        self.__roster_positions = roster_positions

    def setUsersDraftOrder(self, users_draft_order):
        self.__users_draft_order = users_draft_order

    def setCurrentPickNumber(self, current_pick_number):
        self.__current_pick_number = current_pick_number

    def setUsersDraftSlots(self, users_draft_slots):
        self.__users_draft_slots = users_draft_slots

    def setUserCanDraft(self, user_can_draft):
        self.__user_can_draft = user_can_draft

    def setCurrentRound(self, current_round):
        self.__current_round =  current_round

    def setRounds(self, rounds):
        self.__rounds = rounds

    def setTeams(self, teams):
        self.__teams = teams