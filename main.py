# coding=utf-8
import argparse
import logging as log
import os
import re

# Setup slack client
import shutil
import time
from enum import Enum
from io import BytesIO

# For extracting information from pdf
import numpy
# aquiring pdf from webpage
import requests
import schedule as schedule
import tabula
import urllib3
from PyPDF4 import PdfFileWriter, PdfFileReader
from bs4 import BeautifulSoup
# Slack bot
from slackclient import SlackClient

# scheduling and date handling
import calendar
from datetime import datetime
import locale

locale.setlocale(locale.LC_TIME, 'da_DK.UTF-8')
# Constants
NEXT_MENU = "next_menu.pdf"
CURRENT_MENU = "current_menu.pdf"


class Days(Enum):
    MANDAG = 'mandag'
    TIRSDAG = 'tirsdag'
    ONSDAG = 'onsdag'
    TORSDAG = 'torsdag'
    FREDAG = 'fredag'


class FoodBot:
    def __init__(self, auth_token):
        # instantiate Slack client
        print("Starting slack client...")
        self.slack_client = SlackClient(auth_token)
        # constants
        self.RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
        self.HELP_COMMAND = "help"
        self.CHANNEL = "#random"
        self.UGE = "uge"
        self.FLODEKARTOFLER = "flødekartofler"
        self.MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
        self.DEFAULT_CHANNEL = "#random"

        # Initializes the menus, both menus has to be present when running the bot!
        print("Loading local menu files...")
        self.current_menu = self.get_menu_as_dict(CURRENT_MENU)
        self.next_menu = self.get_menu_as_dict(NEXT_MENU)


        print("Trying to connect to slack RTM")
        if self.slack_client.rtm_connect(with_team_state=False):
            print("Bot connected and running!")
            # Read bot's user ID by calling Web API method `auth.test`
            self.starterbot_id = self.slack_client.api_call("auth.test")["user_id"]
        else:
            print("Connection failed.")


    def parse_bot_commands(self, slack_events):
        """
            Parses a list of events coming from the Slack RTM API to find bot commands.
            If a bot command is found, this function returns a tuple of command and channel.
            If its not found, then this function returns None, None.
        """
        for event in slack_events:
            if event["type"] == "message" and not "subtype" in event:
                user_id, message = self.parse_direct_mention(event["text"])
                if user_id == self.starterbot_id:
                    return message, event["channel"]
        return None, None

    def parse_direct_mention(self, message_text):
        """
            Finds a direct mention (a mention that is at the beginning) in message text
            and returns the user ID which was mentioned. If there is no direct mention, returns None
        """
        matches = re.search(self.MENTION_REGEX, message_text)
        # the first group contains the username, the second group contains the remaining message
        return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

    def post_message(self, message, channel):
        # Sends the response back to the channel
        self.slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=message
        )

    def get_next_menu(self, day):
        return self.next_menu[day.value].__str__()

    def get_current_menu(self, day):
        return self.current_menu[day.value].__str__()

    def is_command_day(self, command, day):
        return command.lower().startswith(day.value)

    def handle_command(self, command, channel):
        """
            Executes bot command if the command is known
        """
        # Default response is help text for the user
        default_response = "Not sure what you mean. Try *{}*.".format(self.HELP_COMMAND)
        response = ""

        # This is where you start to implement more commands!
        if command.startswith(self.HELP_COMMAND):
            response = "Command syntax: @Mention command \n Available commands: \n\t\thelp \n\t\tmandag \n\t\ttirsdag \n\t\tonsdag \n\t\ttorsdag \n\t\tfredag \n\t\tuge \n\t\tflødekartofler"
        elif command.startswith(self.UGE):
            for day in Days:
                response += "\n\n*" + day.value.upper() + "*\n"
                response += self.get_current_menu(day)
        elif command.startswith(self.FLODEKARTOFLER.__str__()):
            day_this_week, day_next_week = self.is_flodekartofler()
            if day_this_week:
                response += "DER ER FLØDEKARTOFLER " + "*" + day_this_week.upper() + "*" + " I DENNE UGE! :drooling_face: \n"
            if day_next_week:
                response += "DER ER FLØDEKARTOFLER " + "*" + day_next_week.upper() + "*" + " I NÆSTE UGE! :drooling_face: \n"
            if day_next_week == None and day_this_week == None:
                response = "Der er ingen flødekartofler i denne eller næste uge :sob:"
        else:
            for day in Days:
                if self.is_command_day(command, day):
                    response = "*" + day.value.upper() + "*" + "\n" + self.get_current_menu(day)

        if not response:
            response = default_response
        # Sends the response back to the channel
        self.post_message(message=response, channel=channel)

    def is_flodekartofler(self):
        """
        :rtype: day_this_week, day_next_week if no flødekartofler return None, None
        """
        day_this_week = None
        day_next_week = None
        for day in Days:
            if self.get_current_menu(day).find("flødebagte kartofler") != -1:
                day_this_week = day.value
            if self.get_next_menu(day).find("flødebagte kartofler") != -1:
                day_next_week = day.value
        return day_this_week, day_next_week

    @staticmethod
    def get_pdf_menu_url():
        # ude wget to get page
        response = requests.get("https://www.kokkenogco.dk/weekly-menu")
        page = str(BeautifulSoup(response.content, features="html.parser"))
        sub_string = "https://www.kokkenogco.dk/wp-content/uploads/202"
        # Loop through all lines starting with "a hr
        start_char = page.find(sub_string)
        end_char = page.find(".pdf", start_char)
        return page[start_char:end_char + 4]

    @staticmethod
    def download_file(url, file_name):
        response = urllib3.PoolManager().request('GET', url, preload_content=False)
        memoryFile = BytesIO(response.data)
        pdfFile = PdfFileReader(memoryFile)
        writer = PdfFileWriter()
        for pageNum in range(pdfFile.getNumPages()):
            currentPage = pdfFile.getPage(pageNum)
            writer.addPage(currentPage)

        outputStream = open(file_name, "wb")
        writer.write(outputStream)
        outputStream.close()

    @staticmethod
    def get_menu_as_dict(file):
        df = tabula.read_pdf(file, pages="1", lattice=True)
        array = df[0].to_numpy()[0][0:5]

        # remove carriage return and Add line shifts
        for i in range(array.__len__()):
            array[i] = numpy.core.defchararray.replace(array[i], "\r", "\n\t\t")
            array[i] = numpy.core.defchararray.replace(array[i], "KOLDT", "\t_KOLDT_")
            array[i] = numpy.core.defchararray.replace(array[i], "\tVARMT", "_VARMT_")
            array[i] = numpy.core.defchararray.replace(array[i], "\tVARMT/LUNT", "_VARMT/LUNT_")
            array[i] = numpy.core.defchararray.replace(array[i], "\tFROKOSTSALAT", "_FROKOSTSALAT_")
            array[i] = numpy.core.defchararray.replace(array[i], "\tRIG SALAT", "_RIG SALAT_")
            array[i] = numpy.core.defchararray.replace(array[i], "\tDET SØDE", "_DET SØDE_")
            array[i] = numpy.core.defchararray.replace(array[i], "\tOST", "_OST_")
            array[i] = numpy.core.defchararray.replace(array[i], "\tBRØD", "_BRØD_")

        days = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag"]
        menu = dict(zip(days, array))
        return menu

    @staticmethod
    def replace_file(src, dst):
        shutil.move(src=src, dst=dst)

    def update_menus(self):
        # Delete and rename the old menu
        print("Updating the menus...")
        self.replace_file(NEXT_MENU, CURRENT_MENU)

        # download the new menu
        url = self.get_pdf_menu_url()
        bot.download_file(url, NEXT_MENU)
        menu = self.get_menu_as_dict(NEXT_MENU)

        # Update the class variables
        self.current_menu = self.next_menu
        self.next_menu = menu
        print("Finished updating menus...")

    def daily_menu_post(self):
        # If the day is not a weekend (-1 to make is match calendar days 0==monday...)
        current_weekday = datetime.today().isoweekday() - 1
        if current_weekday < 5:
            print("Posting daily menu...")
            self.handle_command(calendar.day_name[current_weekday], self.DEFAULT_CHANNEL)
        else:
            print("Not posting daily menu, it's weekend ma doods!")

if __name__ == "__main__":
    # Create the bot
    bot = FoodBot(auth_token=os.environ['TOKEN'])
    # Schedules
    schedule.every().day.friday.at("23:00").do(bot.update_menus)    # update of the menus every friday night
    schedule.every().day.at("11:00").do(bot.daily_menu_post)        # post every day at 11

    # MAIN LOOP
    while True:
        # run if any pending scheduled jobs
        schedule.run_pending()

        # fetch messages
        command, channel = bot.parse_bot_commands(bot.slack_client.rtm_read())
        if command:
            bot.handle_command(command, channel)
        time.sleep(bot.RTM_READ_DELAY)
