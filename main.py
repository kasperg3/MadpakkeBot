import re
# Setup slack client
import shutil
import time

# For extracting information from pdf
import numpy
import tabula

# Slack bot
from slack import WebClient as SlackClient, RTMClient
import logging as log
# aquiring pdf from webpage
import requests
from bs4 import BeautifulSoup
import urllib3
from io import BytesIO
from PyPDF4 import PdfFileWriter, PdfFileReader
import time

NEXT_MENU = "next_menu.pdf"
CURRENT_MENU = "current_menu.pdf"


class FoodBot:
    def __init__(self, auth_token):
        # instantiate Slack client
        self.slack_client = SlackClient(auth_token)
        # constants
        self.RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
        self.HELP_COMMAND = "help"
        self.CHANNEL = "#random"
        self.MANDAG = "mandag"
        self.TIRSDAG = "tirsdag"
        self.ONSDAG = "onsdag"
        self.TORSDAG = "torsdag"
        self.FREDAG = "fredag"
        self.UGE = "uge"
        self.FLODEKARTOFLER = "flødekartofler"

        self.MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

        # Initializes the menus, both menus has to be present when starting!
        self.current_menu = self.get_menu_as_dict(CURRENT_MENU)
        self.next_menu = self.get_menu_as_dict(NEXT_MENU)

        try:
            if self.slack_client.rtm_connect(with_team_state=False):
                print("Bot connected and running!")
                # Read bot's user ID by calling Web API method `auth.test`
                starterbot_id = self.slack_client.api_call("auth.test")["user_id"]
            else:
                print("Connection failed. Exception traceback printed above.")

        except:
            log.log(log.CRITICAL, "Not able to connect to slack client! Shutting down...")
            exit()

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

    def post_message(self, message):
        self.slack_client.chat_postMessage(channel=self.CHANNEL, text=message)

    def handle_command(self, **payload):
        """
            Executes bot command if the command is known
        """
        data = payload['data']
        web_client = payload['web_client']
        rtm_client = payload['rtm_client']

        # Default response is help text for the user
        default_response = "Not sure what you mean. Try *{}*.".format(self.HELP_COMMAND)
        response = default_response
        command = ""
        if 'text' in data and 'Hello' in data.get('text', command):
            channel_id = data['channel']
            thread_ts = data['ts']
            user = data['user']
            # This is where you start to implement more commands!
            if command.startswith(self.HELP_COMMAND):
                response = "Command syntax: @Mention command \n Available commands: \n\t help \n\tmandag \n\ttirsdag \n\tonsdag \n\ttorsdag \n\tfredag"
            elif command.startswith(self.MANDAG):
                print(self.current_menu["mandag"])
            elif command.startswith(self.TIRSDAG):
                pass
            elif command.startswith(self.ONSDAG):
                pass
            elif command.startswith(self.TORSDAG):
                pass
            elif command.startswith(self.FREDAG):
                pass
            elif command.startswith(self.UGE):
                pass
            elif command.startswith(self.FLODEKARTOFLER):
                pass
            # Sends the response back to the channel
            self.post_message(response)

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
            array[i] = numpy.core.defchararray.replace(array[i], "\r", "\n\t")
            array[i] = numpy.core.defchararray.replace(array[i], "\tKOLDT", "\KOLDT")
            array[i] = numpy.core.defchararray.replace(array[i], "\tVARMT", "VARMT")
            array[i] = numpy.core.defchararray.replace(array[i], "\tFROKOSTSALAT", "FROKOSTSALAT")
            array[i] = numpy.core.defchararray.replace(array[i], "\tRIG SALAT", "RIG SALAT")
            array[i] = numpy.core.defchararray.replace(array[i], "\tBRØD", "BRØD")

        days = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag"]
        menu = dict(zip(days, array))
        return menu

    @staticmethod
    def replace_file(src, dst):
        shutil.move(src=src, dst=dst)


    def update_menus(self):
        # Delete and rename the old menu
        self.replace_file(NEXT_MENU, CURRENT_MENU)

        # download the new menu
        url = self.get_pdf_menu_url()
        bot.download_file(url, NEXT_MENU)
        menu = self.get_menu_as_dict(NEXT_MENU)

        self.current_menu = self.next_menu
        self.next_menu = menu


if __name__ == "__main__":
    # TODO Replace the authtoken with an env variable
    auth_token = ""
    bot = FoodBot(auth_token=auth_token)
    # Schedule update of menus every friday at 14:00 TODO
    #schedule.every().day.friday.at("14:00").do(bot.update_menus)

    while True:
        command, channel = bot.parse_bot_commands(bot.slack_client.rtm_read())
        if command:
            bot.handle_command(command, channel)
        time.sleep(bot.RTM_READ_DELAY)

