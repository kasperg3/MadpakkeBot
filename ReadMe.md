
# Bot Setup

Create a classic bot: `https://api.slack.com/apps?new_classic_app=1`

1. go to app home and add Legacy bot user
2. then update the permission scope
3. Then copy the bot OAuth token and create a nevironment variable called XXXXTBDXXXX

You're done! Run the bot script!

# Requriements
A danish locale is needed for translating the commands into english

`sudo apt-get install language-pack-da-base`

`sudo dpkg-reconfigure locales`

Choose da_dk.UTF-8 and set to defualt