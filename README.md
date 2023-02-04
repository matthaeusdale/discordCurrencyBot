# Financial Management Bot
A fully autonomous Discord bot featuring dozens of commands dedicated to teaching individuals the basics of financial management through an immersive portfolio simulation.

## Available Commands

| Command | Description |
| --- | --- |
| `!help` | Shows a help menu |
| `!balance` | Shows the amount of money you have |
| `!level` | Shows your level |
| `!xp` | Shows the amount of experience you have |
| `!work` | Allows you to work for money/EXP |
| `!shop` | Shows the shop where you can buy items |
| `!buy` | Allows you to buy an item |
| `!ticket` | Allows you to buy a ticket for a certain price |
| `!rob` | Allows you to steal from someone's goldmine |
| `!order` | Allows you to order stocks |
| `!sell` | Allows you to sell stocks |
| `!market` | Allows you to see all stocks on the market |
| `!portfolio` | Allows you to see all the stocks you own |

## Features
- Dozens of interactive commands to help users simulate their portfolios.
- 24/7 availability through the use of the discord.py library
- MySQL for local storage and retrieval of data.

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
