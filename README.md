
# Poe Phrecia Idol Finder

A small project built with Flask as the backend and React as the frontend. The tool on launch will ask you to authorize the project to look at your PoE account's name, leagues, stash and items. The tool can only look at those things and can't make any harmful changes to your account or items. 

The tool will display your idols in a given stash and allow you to sort them by Content Tags, like Abyss, Incursion, Bestiary, etc. I'm hoping the tool makes it easier for people to look through their stash, pick certain content they want to use and easily find the idols associated with it. Some mods don't necessarily have easy keywords to filter with in game for, so this tool will simplify the process.



## Installation

To install and run the program, you'll need both Python 3.13, Node and a PoE API Client ID, which you can by emailing oauth@grindinggear.com and following the instructions [here](https://www.pathofexile.com/developer/docs#gettingstarted). I'm looking into trying to host the tool on an external website so this won't be necessary, but for those who have the know how and want to mess around with the tool the code is available.

The root directory requires a .env file containing the following: CLIENT_ID, REDIRECT_URI and SCOPES.

To start, you can use `pipenv install` in the root directory to get all the python dependencies and start the shell by using `pipenv shell`.

For the backend, you `cd backend` and `py .\app.py` to start the backend which should host on http://localhost:5000.

For the frontend, you `cd frontend` and `npm install`, followed by `npm build` and start it with `npm start`. It'll host on http://localhost:3000.

Optionally, the app-development branch has it set so you only have to run the `app.exe` file with the `.env` and `poe-idols.csv` files in same directory for the tool to work.
# Usage

Once you've installed and are running the backend and frontend servers, visit http://localhost:3000 or http://127.0.0.1:5000 if you're running `app.exe`. It'll redirect you to authorize the tool as stated above and redirect you back to the tool.

To use the tool, click the "Fetch Stashes" button and a dropdown bar will appear with all your stashes. Select a stash that has non-unique idols in it, if there are no idols it'll state so. It'll display all your idols on the page and you'll be able to filter by Content Tags and sort from highest to lowest.