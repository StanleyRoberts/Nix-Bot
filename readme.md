# NixBot

Nix is a multi-purpose discord bot we created for our server, the _Watching Raccoons_.  
Nix provides many functions, as a provider for many other API's such as random quotes, facts, or reddit posts as well as tracking birthdays and the counting game.

## Setup

The app requires [Python 3.10+](https://www.python.org/downloads/), and we also recommend using a virtual environment:  
Setup a virtual environment using: `python -m venv .venv`  
And install the requirements (on your virtual env) with: `pip install -r requirements.txt`

For running locally/testing, you will also need a `.env` file (or another way to set environment variables for the app), which establishes private keys/tokens to be used within the app. If you are not one of the original authors for this project you will have to create this yourself with your own keys/tokens as required (the variables retrieved with `os.getenv` dictate the environment variables to set). These environment variables also need to be set to the live keys/tokens on whichever hosting service/machine you use for live deployment.

Running the project locally (i.e. not on Heroku) runs a testing build, with a fresh testing database however you will need [PostgreSQL](https://www.postgresql.org/download/) installed on your machine and on your `PATH`.

## Continuous Development

This app is run on a [Fly.io](https://fly.io/) account connected to this GitHub repo. Any changes to the main branch are automatically reflected in the live app.  
If you would like to run this app yourself, it should work by deploying to Fly.io in the same way and setting appropriate environment variables.

While developing you can quickly modify the `requirements.txt` by running `pip freeze > requirements.txt`. The Dockerfile can be updated with `docker build -t nix .`. The requirements and Dockerfile **must** be up to date before deploying any changes to Fly.io.

To run the code on Fly.io you will need to copy the values in your `.env` into the Fly.io configuration variables (and make any necessary adjustments to reflect your live app), you will also need to setup a PostgreSQL server to interact with whose connection URL should be specified in an environment variable.
