# Draft Helper

A desktop app that follows your live Sleeper fantasy football draft and uses Google Gemini to suggest who to pick next.

## What you need

- **A Sleeper account** This project only works for fantays drafts through sleeper. You will need at least your username as well as the *draftId* or the draft URL
    - The *draftId* can be found in the URL of a current draft, in `https://sleeper.com/draft/nfl/1418530714927837184?ftue=commish`, 1418530714927837184 would be the *draftId*

## Setup

1. Download all files and move then to a project folder

2. Install package requirements, optionally inside a virtual enviroment
    ```
    pip install -r requirements.txt
    ```

## Running it

```
python ui.py
```

1. Enter your **Sleeper username** and your **draft ID**. You can also paste the draft's link from the Sleeper website. Then press **Connect**.
2. The top of the window shows how many picks until your turn and turns green when you're on the clock.
3. Press **Suggest pick** to get three suggestions from Gemini. You can type extra instructions in the box first, like "PPR league" or "I need a WR".

The draft refreshes every 5 seconds on its own. You can also press **Refresh**.
