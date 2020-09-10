import asyncio
import locale
import math
import random

import discord
from discord import Embed

import config
from database import Database


def parse_id(author):
    raw = author.mention
    if raw.find('!') != -1:
        return raw[3:-1]
    return raw[2:-1]


# connecting to the server

client = discord.Client()
locale.setlocale(locale.LC_ALL, '')
# establishing connection to database
db = Database()


async def half_minute_loop():
    while True:
        db.update_stock("$SAFE")
        await asyncio.sleep(30)


async def start_loop():
    asyncio.ensure_future(half_minute_loop())


loop = asyncio.get_event_loop()
loop.run_until_complete(start_loop())


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    user_id = parse_id(message.author)
    if message.content == '!work':
        db.verify_existence(user_id)
        if db.can_work(user_id):
            earn = int(math.ceil((random.random() * 10 + 20) * (db.get_level(user_id) + 1)))
            xp = int(math.ceil((random.random() * 10 + 10) * .5 * (db.get_level(user_id) + 1)))
            db.update_stats(user_id, exp=xp, bal=earn)
            db.create_cooldown(user_id, seconds=20)
            await message.channel.send(
                "You made **" + str(locale.currency(earn, grouping=True)) + '** and earned **' + str(
                    xp) + "XP**, " + message.author.mention)
            if db.try_level_up(user_id):
                await message.channel.send(
                    "Congratulations, " + message.author.mention + ". You reached level **" + str(
                        db.get_level(user_id)) + "**!")
        else:
            await message.channel.send(
                'You need to wait **' + str(db.get_work_cd(user_id).seconds) + 's** to work again.')

    if message.content == '!poggas':
        await message.channel.send('matt is a god')

    if message.content.startswith('!balance') or message.content.startswith('!bal'):
        db.verify_existence(user_id)
        if len(message.mentions) > 0:
            name = str(message.mentions[0])
            await message.channel.send(
                '**{}** has **{}**.'.format(name[:-5],
                                            locale.currency(db.get_balance(message.mentions[0].id), grouping=True)))
        else:
            await message.channel.send(
                'You have **' + str(
                    locale.currency(db.get_balance(user_id), grouping=True)) + '**, ' + message.author.mention)

    if message.content.startswith('!level') or message.content.startswith('!xp'):
        db.verify_existence(user_id)
        if len(message.mentions) > 0:
            name = str(message.mentions[0])
            await message.channel.send(
                '**{}** is level **{}**.'.format(name[:-5], db.get_level(message.mentions[0].id)))
        else:
            await message.channel.send(
                'You are level** ' + str(
                    db.get_level(user_id)) + '**, ' + message.author.mention + '.\nYou have **' + str(
                    db.get_exp(user_id)) + 'XP**, and you need **' + str(
                    db.get_xp_until_level(user_id)[1]) + 'XP** to level up.')

    if message.content.startswith('!admin'):
        db.verify_existence(user_id)
        if len(message.mentions) > 0:
            name = str(message.mentions[0])
            if db.get_admin(message.mentions[0].id):
                await message.channel.send('**{}** is an admin.'.format(name[:-5]))
            else:
                await message.channel.send('**{}** is not an admin.'.format(name[:-5]))
        elif db.get_admin(user_id):
            await message.channel.send('You are an admin.')
        else:
            await message.channel.send('You are not an admin.')

    if message.content == "!shop":
        db.verify_existence(user_id)
        embed = Embed(title="Shop", description="Usage: !buy [item_name]")
        embed.add_field(name="ticket ($100)", value="Buy this and a minute later you will receive $50-150 back",
                        inline=False)
        embed.add_field(name="goldmine ($5000)", value="Buy this to earn money while AFK!", inline=False)
        await message.channel.send(embed=embed)

    if message.content.startswith('!buy'):
        db.verify_existence(user_id)
        msg_list = message.content.split(" ")
        if len(msg_list) > 1:
            items = {"ticket": 100, "goldmine": 5000}
            item = msg_list[1]
            balance = db.get_balance(user_id)
            if len(msg_list) > 2 and msg_list[2].isnumeric():
                number = msg_list[2]
                if item in items:
                    if balance >= items[item] * int(number):
                        if item == "goldmine":
                            db.buy_goldmine(id=user_id, amount=number)
                            await message.channel.send("**{}** goldmines purchased!".format(number))
                        db.update_stats(user_id, bal=-items[item] * int(number))
                    else:
                        await message.channel.send(
                            "Not enough money. Your balance is **{}** while [{}] costs **{}!**".format(
                                locale.currency(balance, grouping=True), item,
                                locale.currency(items[item] * int(number), grouping=True)))
            else:
                if item in items:  # if valid item
                    balance = db.get_balance(user_id)
                    if balance >= items[item]:  # if has enough money
                        if item == "ticket":
                            db.create_ticket(user_id=user_id, ticket_id=0, value=100, seconds_long=60)
                            await message.channel.send("Ticket purchased!")
                        elif item == "goldmine":
                            db.buy_goldmine(id=user_id)
                            await message.channel.send("Goldmine purchased!")
                        db.update_stats(user_id, bal=-items[item])
                else:
                    await message.channel.send(
                        "Not enough money. Your balance is **{}** while [{}] costs **{}!**".format(
                            locale.currency(balance, grouping=True), item,
                            locale.currency(items[item]), grouping=True))

    if message.content.startswith("!ticket"):
        db.verify_existence(user_id)
        msg_list = message.content.split(" ")
        if len(msg_list) == 1:
            embed = db.get_tickets(message.author, user_id)
            await message.channel.send(embed=embed)
        elif msg_list[1].isdigit():
            bal = db.get_balance(user_id)
            if bal >= int(msg_list[1]) > 0:  # if first arg is a number
                db.create_ticket(user_id, 0, int(msg_list[1]), 60)
                db.update_stats(user_id, bal=-int(msg_list[1]))
                await message.channel.send("Ticket of value {} created.".format(msg_list[1]))
            elif int(msg_list[1]) <= 0:
                await message.channel.send("The minimum price of a ticket is **$1!**")
            else:
                await message.channel.send(
                    "You do not have enough money! You tried to purchase a **{}** ticket while you have only **{}!**".format(
                        locale.currency(msg_list[1], grouping=True), locale.currency(bal, grouping=True)))

    if message.content == "!claim":
        db.verify_existence(user_id)
        amt = db.claim(user_id)
        await message.channel.send(
            'You collected **{}** and **{}XP** from your goldmine!'.format(str(locale.currency(amt, grouping=True)),
                                                                           str(int(amt * .2))))
        if db.try_level_up(user_id):
            await message.channel.send(
                "Congratulations, " + message.author.mention + ". You reached level **" + str(
                    db.get_level(user_id)) + "**!")

    if message.content == "!help":
        db.verify_existence(user_id)
        embed = Embed(title="Help Menu")
        embed.add_field(name="!help", value="Shows this help menu", inline=False)
        embed.add_field(name="!balance", value="Shows the amount of money you have", inline=False)
        embed.add_field(name="!level", value="Shows your level", inline=False)
        embed.add_field(name="!xp", value="Shows the amount of experience you have", inline=False)
        embed.add_field(name="!work", value="Allows you to work for money/EXP", inline=False)
        embed.add_field(name="!shop", value="Shows the shop where you can buy items", inline=False)
        embed.add_field(name="!buy", value="Allows you to buy an item", inline=False)
        embed.add_field(name="!ticket", value="Allows you to buy a ticket for a certain price", inline=False)
        embed.add_field(name="!rob", value="Allows you to steal from someone's goldmine", inline=False)
        embed.add_field(name="!order", value="Allows you to order stocks", inline=False)
        embed.add_field(name="!sell", value="Allows you to sell stocks", inline=False)
        embed.add_field(name="!market", value="Allows you to see all stocks on the market", inline=False)
        embed.add_field(name="!portfolio", value="Allows you to see all the stocks you own", inline=False)

        await message.channel.send(embed=embed)

    if message.content.startswith("!redeem"):
        db.verify_existence(user_id)
        await message.channel.send(db.redeem_tickets(user_id))

    if message.content.startswith("!steal") or message.content.startswith("!rob"):
        if len(message.mentions) > 0:
            robber_id = user_id
            victim_id = message.mentions[0].id
            name = str(message.mentions[0])
            amount_stolen, percent = db.attempt_steal(victim_id, robber_id)
            await message.channel.send(
                'You stole **{}** of **{}**\'s goldmine profits!'.format(percent, name[:-5]))
            await message.channel.send(
                'You made **{}** and earned **{}XP**.'.format(locale.currency(amount_stolen, grouping=True),
                                                              int(amount_stolen * .2)))
            if db.try_level_up(user_id):
                await message.channel.send(
                    "Congratulations, " + message.author.mention + ". You reached level **" + str(
                        db.get_level(user_id)) + "**!")
        else:
            await message.channel.send('You need to \'@\' someone to steal from them!')

    if message.content.startswith("!give"):
        db.verify_existence(user_id)
        msg_list = message.content.split()
        if len(message.mentions) > 0 and len(msg_list) == 3 and msg_list[2].isnumeric():
            amount = int(msg_list[2])
            receiver_id = message.mentions[0].id
            receiver_name = str(message.mentions[0])
            if db.get_balance(user_id) >= amount:
                db.update_stats(user_id, bal=-1 * amount)
                db.update_stats(receiver_id, bal=amount)
                await message.channel.send(
                    'You gave **{}** **{}**. How nice of you.'.format(receiver_name[:-5],
                                                                      locale.currency(amount, grouping=True)))
            else:
                await message.channel.send('You don\'t have enough money for that!')
        else:
            embed = Embed(title="!give")
            embed.add_field(name="Usage:", value="!give [@recipient] [amount]")
            await message.channel.send(embed=embed)

    if message.content.startswith('!goldmine'):
        db.verify_existence(user_id)
        if len(message.mentions) > 0:
            name = str(message.mentions[0])[:-5]
            amount = db.get_goldmine(message.mentions[0].id)
            if amount == 0:
                await message.channel.send('**{}** doesn\'t own any goldmines.'.format(name))
            else:
                await message.channel.send(
                    '**{}**\'s goldmine is level **{}**, which gives **{}/min**'.format(name, amount, locale.currency(
                        12 * int(amount), grouping=True)))
        else:
            amount = db.get_goldmine(user_id)
            if amount == 0:
                await message.channel.send('You don\'t own any goldmines. Purchase one in the !shop')
            else:
                await message.channel.send(
                    'Your goldmine is level **{}**, which gives **{}/min**'.format(
                        int(amount),
                        locale.currency(12 * int(amount), grouping=True)))

    if message.content.startswith("!order"):
        db.verify_existence(user_id)
        msg_list = message.content.split(" ")
        if len(msg_list) > 2 and db.stock_exists(msg_list[1].upper()):
            last = msg_list[2]
            stock = msg_list[1].upper()
            try:
                num = float(last)
                if num > 0:
                    stock_price = db.get_stock_value(stock)
                    quantity = num
                    price = stock_price * quantity
                    if db.get_balance(user_id) >= price:
                        db.buy_stock(user_id, stock, shares=quantity)
                        await message.channel.send(
                            "You successfully bought **{}** shares of **{}** for **{}!**".format(quantity, stock,
                                                                                                 locale.currency(
                                                                                                     price,
                                                                                                     grouping=True)))
                    else:
                        await message.channel.send(
                            "You can not afford **{}** shares of **{}** (worth **{}**) with your balance of **{}!**".format(
                                quantity, stock, locale.currency(stock_price, grouping=True),
                                locale.currency(db.get_balance(user_id)), grouping=True))
            except ValueError:
                embed = Embed(title="!order", description="Note: use !market to look at all tradable stocks")
                embed.add_field(name="Usage:", value="!order [stock] [shares]")
                await message.channel.send(embed=embed)

        else:
            embed = Embed(title="!order", description="Note: use !market to look at all tradable stocks")
            embed.add_field(name="Usage:", value="!order [stock] [shares]")
            await message.channel.send(embed=embed)

    if message.content.startswith("!sell"):
        db.verify_existence(user_id)
        msg_list = message.content.split()
        if len(msg_list) > 2 and db.stock_exists(msg_list[1].upper()):
            stock = msg_list[1].upper()
            if db.user_has_stock(user_id, stock):
                last = msg_list[2]
                if last == "all":
                    num_shares = db.get_number_of_shares(user_id, stock)
                    db.sell_stock(user_id, stock)
                    value = int(num_shares * db.get_stock_value(stock))
                    await message.channel.send(
                        "You have successfully sold **{}** shares of **{}** for **{}**!".format(num_shares, stock,
                                                                                                locale.currency(value,
                                                                                                                grouping=True)))
                else:
                    try:
                        num = float(last)
                        if num > 0:
                            num_shares = db.get_number_of_shares(user_id, stock)
                            value = db.sell_stock(user_id, stock, float(last))
                            actual_sold = min(num_shares, float(last))
                            await message.channel.send(
                                "You have successfully sold **{}** shares of **{}** for **{}!**".format(actual_sold,
                                                                                                        stock,
                                                                                                        locale.currency(
                                                                                                            value,
                                                                                                            grouping=True)))
                    except ValueError:

                        embed = Embed(title="!sell")
                        embed.add_field(name="Usage:", value="!sell [stock] [shares/all]")
                        await message.channel.send(embed=embed)
            else:
                await message.channel.send("You do not own any shares of **{}!**".format(stock))
        else:
            embed = Embed(title="!sell")
            embed.add_field(name="Usage:", value="!sell [stock] [shares/all]")
            await message.channel.send(embed=embed)

    if message.content.startswith("!market"):
        embed = Embed(title="Market", description="Use !order to order stocks!")
        for stock in db.get_stock_list():
            embed.add_field(name=stock, value="**{}**/share".format(locale.currency(db.get_stock_value(stock))))
        await message.channel.send(embed=embed)
    if message.content.startswith("!portfolio") or message.content.startswith("!pf"):
        db.verify_existence(user_id)
        embed = Embed(title="Portfolio", description="")
        has_stock = False
        for stock in db.get_stock_list():
            if db.user_has_stock(user_id, stock):
                has_stock = True
                num_shares = db.get_number_of_shares(user_id, stock)
                stock_price = db.get_stock_value(stock)
                embed.add_field(
                    name="**{}** (trading at **{}**)".format(stock, locale.currency(stock_price, grouping=True)),
                    value="You own **{}** shares of **{}** (worth **{}**)".format(
                        num_shares, stock, locale.currency(num_shares * stock_price, grouping=True)))
        if not has_stock:
            embed.add_field(name="You don\'t own any stock",
                            value="Use !order to order stocks and !market to look at all stocks")
        await message.channel.send(embed=embed)


client.run(config.fuckit_token)
# client.run("NzE1NDA4ODY3NDI0NDY5MDYz.XxM9Hg.rgehoxEalyPoBNiyLPJeJV4j0hE")
