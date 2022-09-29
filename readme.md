# Nix the Bot


Nix is a multi-purpose discord bot we created for our server, the *Watching Racoons*.  
Nix provides many functions, mainly as a provider for many other API's such as random quotes, facts, or reddit posts.

## Setup

The app requires [Python 3.10+](https://www.python.org/downloads/), and we also recommend using a virtual environment:  
Setup a virtual environment using: `python -m venv .venv`  
And install the requirements with: `pip install -r requirements.txt`  

You will also need a `.env` file, which establishes private keys/tokens in environment variables to be used within the app. If you are not one of the original authors for this project you will have to create this yourself with your own keys/tokens as required.

## Live Development

This app is run on a [Heroku](https://www.heroku.com/) account connected to this GitHub repo. Any changes to the main branch are automatically reflected in the live app.  
If you would like to run this app yourself, it should work off-the-shelf by deploying to Heroku in the same way.  

While developing you can quickly modify the `requirements.txt` by running `pip freeze > requirements.txt`, the requirements must be up to date before deploying any changes to Heroku.

### TODO

- Integrate counting bot

- Add birthday tracker