# Financial Management Bot
A fully autonomous Discord bot dedicated to teaching individuals the basics of financial management through an immersive portfolio simulation.

## Features
- Dozens of interactive commands to help users simulate their portfolios.
- 24/7 availability through the use of the discord.py library and MySQL for local storage and retrieval of data.
- Supports over 30 concurrent users.

## Getting Started

### Prerequisites
- A Discord account and server.
- Python 3.6 or higher.
- MySQL installed on your system.

### Installation
1. Clone the repository to your local machine: `git clone https://github.com/matthaeusdale/discordCurrencyBot.git`
2. Install the required dependencies: `pip install -r requirements.txt`
3. Set up a MySQL database and configure the credentials in the `config.py` file.
4. Replace the `BOT_TOKEN` in `config.py` with your Discord bot token.
5. Run the bot using the command: `python bot.py`

## Contributing
If you would like to contribute to this project, please fork the repository and submit a pull request with your changes.

## Acknowledgements
- [Discord.py](https://github.com/Rapptz/discord.py) for providing the library for interacting with the Discord API.
- [MySQL](https://www.mysql.com/) for local storage and retrieval of user data.