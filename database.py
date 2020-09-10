import locale
import random
import time
from datetime import datetime, timedelta

import mysql.connector
from discord import Embed

import config


class Database:
    def __init__(self):
        # ud = userdata, cd = cooldowns
        self.ud_cnx = mysql.connector.connect(user=config.username, password=config.password, host="127.0.0.1",
                                              database="userdata")
        self.ud_cursor = self.ud_cnx.cursor(buffered=True)
        # self.cd_cnx = mysql.connector.connect(user="yuhwanlee1", password=config.password, host="127.0.0.1",
        #                                      database="cooldowns")
        # self.cd_cursor = self.cd_cnx.cursor(buffered=True)
        self.st_cnx = mysql.connector.connect(user=config.username, password=config.password, host="127.0.0.1",
                                              database="stocks")
        self.st_cursor = self.st_cnx.cursor(buffered=True)

    def verify_existence(self, id):
        self.ud_cursor.execute("SELECT * FROM stats WHERE user_id={}".format(id))
        if self.ud_cursor.rowcount == 0:
            new_id = "INSERT INTO stats (user_id, balance, exp, level, admin) VALUES ({}, 0, 0, 0, 0)".format(id)
            self.ud_cursor.execute(new_id)
        self.ud_cursor.execute("SELECT * FROM cooldowns WHERE user_id={}".format(id))
        if self.ud_cursor.rowcount == 0:
            new_user_time = datetime.now() - timedelta(days=50)
            new_id = "INSERT INTO cooldowns (user_id, work) VALUES ({},  \'{}\')".format(id, new_user_time)
            self.ud_cursor.execute(new_id)
        self.ud_cnx.commit()

    # def update_afk(self):
    #     self.ud_cursor.execute("SELECT * FROM goldmine")
    #     for user_id, level, prev_bal in self.ud_cursor:
    #         amount = int(prev_bal) + (20 * int(level))
    #         update = "UPDATE goldmine SET balance={}".format(amount)
    #         self.ud_cursor.execute(update)
    #     self.ud_cnx.commit()

    def attempt_steal(self, victim_id, robber_id):
        self.ud_cursor.execute("SELECT * FROM goldmine WHERE user_id={}".format(victim_id))
        if self.ud_cursor.rowcount > 0:
            id, level, prev_time = self.ud_cursor.fetchone()
            time_now = datetime.now()
            update = "UPDATE goldmine SET time=\'{}\' WHERE user_id={}".format(time_now, victim_id)
            self.ud_cursor.execute(update)
            self.ud_cnx.commit()
            xp_mod = .2
            total = (time_now - prev_time).total_seconds() * float(level) * .2
            proportion = random.choice([0, .25, .5, .75])
            amount_stolen = int(proportion * total)
            amount_retained = int((1 - proportion) * total)
            xp_stolen = int(proportion * total * xp_mod)
            xp_retained = int((1 - proportion) * total * xp_mod)
            percent = "{}%".format(int(proportion * 100))
            self.update_stats(robber_id, bal=amount_stolen, exp=xp_stolen)
            self.update_stats(victim_id, bal=amount_retained, exp=xp_retained)
            return amount_stolen, percent

    def claim(self, id):
        self.ud_cursor.execute("SELECT * FROM goldmine WHERE user_id={}".format(id))
        id, level, prev_time = self.ud_cursor.fetchone()
        time_now = datetime.now()
        update = "UPDATE goldmine SET time=\'{}\' WHERE user_id={}".format(time_now, id)
        self.ud_cursor.execute(update)
        self.ud_cnx.commit()
        total = int((time_now - prev_time).total_seconds() * float(level) * .2)
        self.update_stats(id, bal=total, exp=total * .2)
        return total

    def buy_goldmine(self, id, amount=1):
        self.ud_cursor.execute("SELECT * FROM goldmine WHERE user_id={}".format(id))
        if self.ud_cursor.rowcount == 0:
            buy = "INSERT INTO goldmine (user_id, level, time) VALUES ({}, {}, \'{}\')".format(id, amount,
                                                                                               datetime.now())
            self.ud_cursor.execute(buy)
        else:
            id, prev_lvl, prev_time = self.ud_cursor.fetchone()

            upgrade = "UPDATE goldmine SET level={} WHERE user_id={}".format(int(prev_lvl) + int(amount), id)
            self.ud_cursor.execute(upgrade)
        self.ud_cnx.commit()

    def get_goldmine(self, id):
        self.ud_cursor.execute("SELECT * FROM goldmine WHERE user_id={}".format(id))
        if self.ud_cursor.rowcount == 0:
            return 0
        id, level, prev_time = self.ud_cursor.fetchone()
        return level

    def update_stats(self, id, bal=0, exp=0, level=0, admin=0):
        self.ud_cursor.execute("SELECT * FROM stats WHERE user_id={}".format(id))
        if self.ud_cursor.rowcount > 0:  # if there is a row with the given id
            id, prev_bal, prev_exp, prev_lvl, admin = self.ud_cursor.fetchone()
            update = "UPDATE stats SET balance={}, exp={}, level={}, admin={} WHERE user_id={}".format(
                int(prev_bal) + bal,
                int(float(prev_exp)) + exp,
                int(prev_lvl) + level,
                admin, id)
            self.ud_cursor.execute(update)
        else:
            stats_id = "INSERT INTO stats (user_id, balance, exp, level, admin) VALUES ({}, {}, {}, {}, {})".format(id,
                                                                                                                    bal,
                                                                                                                    exp,
                                                                                                                    level,
                                                                                                                    admin)
            self.ud_cursor.execute(stats_id)
        self.ud_cnx.commit()

    def get_balance(self, id):
        self.verify_existence(id)
        self.ud_cursor.execute("SELECT * FROM stats WHERE user_id={}".format(id))
        user_id, bal, exp, level, admin = self.ud_cursor.fetchone()
        return int(bal)

    def create_ticket(self, user_id, ticket_id, value, seconds_long):
        ts = time.time() + seconds_long
        timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        self.ud_cursor.execute(
            "INSERT INTO tickets (user_id, ticket_id, value, time) VALUES ({}, {}, {}, \"{}\")".format(user_id,
                                                                                                       ticket_id, value,
                                                                                                       timestamp))
        self.ud_cnx.commit()

    def get_tickets(self, author, id):
        now = datetime.fromtimestamp(time.time())
        query = "SELECT * FROM tickets WHERE user_id={};".format(id)
        self.ud_cursor.execute(query)
        embed = Embed(title="Tickets", description=str(author)[:-5], inline=False)
        redeemable, has_tickets = False, False
        for user_id, ticket_id, value, ticket_time in self.ud_cursor:
            has_tickets = True
            if now > ticket_time:
                embed.add_field(name="Ticket (**${}**)".format(locale.currency(value, grouping=True)),
                                value="Redeemable", inline=False)
                redeemable = True
            else:
                diff = ticket_time - now
                embed.add_field(name="Ticket (**{}**)".format(locale.currency(value, grouping=True)),
                                value="Wait **{}s**".format(diff.seconds),
                                inline=False)
                self.ud_cnx.commit()
        if redeemable:
            embed.add_field(name="Use !redeem", value="to collect your tickets", inline=False)
        elif not has_tickets:
            embed.add_field(name="You don't have any tickets!", value="Use !ticket [value] to purchase a ticket.",
                            inline=False)
        return embed

    def redeem_tickets(self, user_id):
        now = datetime.fromtimestamp(time.time())
        query = "SELECT * FROM tickets WHERE user_id={};".format(user_id)
        self.ud_cursor.execute(query)
        total_earnings = 0
        count = 0
        init_value = 0
        for user_id, ticket_id, value, ticket_time in self.ud_cursor:
            if now > ticket_time:  # if the current time has passed the ticket's end time
                delete = "DELETE FROM tickets WHERE ticket_id={} AND time=\"{}\"".format(ticket_id, ticket_time)
                earnings = int(value * (random.random() + .5))
                total_earnings += earnings
                count += 1
                init_value += value
                self.update_stats(user_id, bal=earnings)
                self.ud_cursor.execute(delete)

        self.ud_cnx.commit()
        if count == 0:
            return "You have no redeemable tickets!"
        else:
            return "You have redeemed **{}** tickets worth **${}** for **${}**!".format(count, init_value,
                                                                                        total_earnings)

    def can_work(self, id):  # TODO: fix these two functions
        self.ud_cursor.execute("SELECT * FROM cooldowns WHERE user_id={}".format(id))
        user_id, cd_end = self.ud_cursor.fetchone()
        now = datetime.now()
        return now > cd_end

    def create_cooldown(self, id, seconds):  # TODO: MAKE BETTER FOR MULTIPLE COOLDOWNS LATER
        ts = time.time() + seconds
        timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        self.ud_cursor.execute("UPDATE cooldowns SET work=\"{}\" WHERE user_id={}".format(timestamp, id))
        self.ud_cnx.commit()

    def get_work_cd(self, id):  # time until work cooldown ends
        self.ud_cursor.execute("SELECT * FROM cooldowns WHERE user_id={}".format(id))
        user_id, cd_end = self.ud_cursor.fetchone()
        now = datetime.now()
        return cd_end - now

    def get_xp_until_level(self, id):
        self.ud_cursor.execute("SELECT * FROM stats WHERE user_id={}".format(id))
        user_id, bal, exp, level, admin = self.ud_cursor.fetchone()
        total_level_exp = 7.5 * (int(level) ** 2) - (25 * int(level)) + 100
        return not int(total_level_exp - int(float(exp))) > 0, total_level_exp

    def try_level_up(self, id):
        self.ud_cursor.execute("SELECT * FROM stats WHERE user_id={}".format(id))
        user_id, bal, exp, level, admin = self.ud_cursor.fetchone()
        can, lost = self.get_xp_until_level(id)
        if can:
            self.update_stats(id, exp=-lost, level=1)
            return True
        return False

    def get_exp(self, id):
        self.verify_existence(id)
        self.ud_cursor.execute("SELECT * FROM stats WHERE user_id={}".format(id))
        user_id, bal, exp, level, admin = self.ud_cursor.fetchone()
        return int(float(exp))

    def get_level(self, id):
        self.verify_existence(id)
        self.ud_cursor.execute("SELECT * FROM stats WHERE user_id={}".format(id))
        user_id, bal, exp, level, admin = self.ud_cursor.fetchone()
        return int(level)

    def get_admin(self, id):
        self.verify_existence(id)
        self.ud_cursor.execute("SELECT * FROM stats WHERE user_id={}".format(id))
        user_id, bal, exp, level, admin = self.ud_cursor.fetchone()
        return admin

    def get_stock_value(self, stock):
        self.st_cursor.execute("SELECT * FROM {} ORDER BY time DESC LIMIT 1".format(stock))
        last_time, value = self.st_cursor.fetchone()
        return int(float(value))

    def get_stock_list(self):
        return ["$SAFE", "$RISK"]

    def stock_exists(self, stock):
        stocks = self.get_stock_list()
        return stock in stocks

    def update_stock(self, stock):
        old_value = self.get_stock_value(stock)
        new_value = 1000
        if stock == "$SAFE":
            new_value = old_value * (.9 + random.random() * .21)  # range: .9x -> 1.1x
        elif stock == "$RISK":
            new_value = old_value * (.25 + random.random() * 2.75)  # range: .9x -> 1.1x

        update_table = "INSERT INTO {} (time, value) VALUES (\"{}\", {})".format(stock, datetime.now(), new_value)
        self.st_cursor.execute(update_table)
        self.st_cnx.commit()

    def user_has_stock(self, user_id, stock):
        query_user = "SELECT * FROM {}_ownership WHERE user_id={}".format(stock, user_id)
        self.st_cursor.execute(query_user)
        return self.st_cursor.rowcount > 0

    def get_number_of_shares(self, user_id, stock):
        query_user = "SELECT * FROM {}_ownership WHERE user_id={}".format(stock, user_id)
        self.st_cursor.execute(query_user)
        id, shares = self.st_cursor.fetchone()
        return float(shares)

    def buy_stock(self, user_id, stock, shares):  # precondition: user has enough balance
        if self.user_has_stock(user_id, stock):
            self.st_cursor.execute(
                "SELECT * FROM {}_ownership WHERE user_id={}".format(stock, user_id))
            id, prev_shares = self.st_cursor.fetchone()
            update_shares = "UPDATE {}_ownership SET shares={} WHERE user_id={}".format(stock, prev_shares + shares,
                                                                                        user_id)
            self.st_cursor.execute(update_shares)
        else:
            self.st_cursor.execute(
                "INSERT INTO {}_ownership (user_id, shares) VALUES ({}, {})".format(stock, user_id, shares))
        self.update_stats(user_id, bal=-int(self.get_stock_value(stock) * shares))
        self.st_cnx.commit()

    def sell_stock(self, user_id, stock, shares=-1):  # precondition: user already has stock
        self.st_cursor.execute(
            "SELECT * FROM {}_ownership WHERE user_id={}".format(stock, user_id))
        id, prev_shares = self.st_cursor.fetchone()
        value = 0
        if shares == -1 or shares >= prev_shares:
            value = int(prev_shares * self.get_stock_value(stock))
            self.update_stats(user_id, bal=value)
            self.st_cursor.execute("DELETE FROM {}_ownership WHERE user_id={}".format(stock, user_id))
        else:  # if quantity being sold is less than what's owned
            value = int(shares * self.get_stock_value(stock))
            self.update_stats(user_id, bal=value)
            update = "UPDATE {}_ownership SET shares={} WHERE user_id={}".format(stock, prev_shares - shares, user_id)
            self.st_cursor.execute(update)
        self.st_cnx.commit()
        return value
