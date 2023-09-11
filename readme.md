# NixBot

## Nix

Nix is a multi-purpose discord bot we created for our server, the _Watching Raccoons_.
Nix is a personable bot providing many functions, such as random quotes, facts, or reddit posts as well as tracking birthdays and the counting game.
[Add him to your server!](https://discord.com/api/oauth2/authorize?client_id=1025014989376978944&permissions=268435456&scope=applications.commands%20bot)

### Features 
- **Fun**: Commands such as /reddit can browse reddits posts, getting memes, videos or textposts. The command /quote will display an AI-generated quote over an inspirational image with some humorous results.
- **Subscriptions**: Nix provides the ability to subscribe to facts or subreddits, sending a fact/post to your server every day!
- **Birthday tracking**: Users can input their birthdays, and Nix will send a birthday message for them to a specified channel. Let your server celebrate birthdays together!
- **Counting game**: Nix can also keep track of the classic discord counting game, no need for a seperate bot!
- **Admin**: A range of admin tools are also provided, this mainly relates to automatic role assignments and messages from Nix on various customisable events (e.g. reacting to, or writing a message). We use this in Watching Raccoons to create a custom new member experience, but these commands are generic enough to let you do whatever you want with them.

### Personality 

We have spent a lot of time making Nix more exciting than your typical discord bot. Nix has a unique personality and style. It features custom emoji and is even able to reply to messages he is tagged in! We want Nix to be a part of your server as much as your other members are.

Note: by default Nix does not remember past conversation it has with you, if you want it to remember things then reply to his messages and he will remember everything in that reply chain.

### Bugs + Suggestions

Nix isnt perfect, it is a hobby project made for the specific use cases our server required. If you notice any bugs or have requests for Nix, please open an issue on the [GitHub](https://github.com/StanleyRoberts/Nix-Bot/issues) page and we will do our best to respond in a timely manner.

## Developers

The below info is for developers of Nix or developers who wish to fork this repo

### Setup

The app requires [Python 3.10+](https://www.python.org/downloads/), and we also recommend using a virtual environment:  
Setup a virtual environment using: `python -m venv .venv`  
And install the requirements (on your virtual env) with: `pip install -r requirements.txt`

For running locally/testing, you will also need a `.env` file (or another way to set environment variables for the app), which establishes private keys/tokens to be used within the app. If you are not one of the original authors for this project you will have to create this yourself with your own keys/tokens as required (please examine the functions/env.py file to identify the variables that must be set). For live deployment the environment variables must be set on the hosting service/machine you use. The testing.postgres module needs to be installed using the following command: `pip install git+https://github.com/tk0miya/testing.postgresql.git`

Running the project locally (i.e. not on Fly.io) runs a testing build, with a fresh testing database however you will need [PostgreSQL](https://www.postgresql.org/download/) installed on your machine and on your `PATH`.

### Continuous Development

This app is run on a [Fly.io](https://fly.io/) account connected to this GitHub repo. Any changes to the main branch are automatically reflected in the live app.  
If you would like to run this app yourself, it should work by deploying to Fly.io in the same way and setting appropriate environment variables.

While developing you can quickly modify the `requirements.txt` by running `pip freeze > requirements.txt`. The Dockerfile can be updated with `docker build -t nix .`. The requirements and Dockerfile **must** be up to date before deploying any changes to Fly.io.

Static type checking can be performed using MyPy. Simply run `mypy .`. Or for strict: `mypy --strict --disable-error-code no-untyped-call --disable-error-code misc .`

To run the code on Fly.io you will need to copy the values in your `.env` into the Fly.io configuration variables (and make any necessary key changes to reflect your live app), you will also need to setup a PostgreSQL server to interact with whose connection URL should be specified in an environment variable.

### Documentation

You can generate documentation for Nix using Sphinx. Simply install m2r2 and sphinx: `pip install sphinx m2r2` then (for Windows) run the command:
`.\docs\launch.cmd` from the top level project directory. To run this on Linux you may need a different launch script.

This will launch an HTML documentation site at `localhost:8000/docs/_build/html/` populated via the Google docstrings in the code using sphinx-autodoc and the README using m2r2.

Note that the slash commands do not appear in the documentation and produce a warning in the launch script output. This is ideal behaviour since the slash command functions should never be externally called and are simply callbacks for the discord slash commands.