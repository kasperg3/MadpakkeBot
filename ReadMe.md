
# Bot Setup

Create a classic bot: `https://api.slack.com/apps?new_classic_app=1`

1. go to app home and add Legacy bot user
2. then update the permission scope
3. Then copy the bot OAuth token and create a nevironment variable called XXXXTBDXXXX

You're done! Run the bot script!

# Docker setup

`sudo apt install docker.io`

`sudo systemctl start docker`

`sudo systemctl enable docker`

Verify: 
`docker --version
`
Python docker containers: 
`docker pull python:3.7`


#### Docker Permission setup

FIRST: Try logging out and back in after installing docker. If this doesn't work, try: 

`sudo groupadd docker`
 
`sudo usermod -aG docker ${USER}`

`su -s ${USER}`

#### Test hello world example

`docker run hello-world`

### IMPORTANT IF USING GMAL
The gmail requires a token from the credentials. This is generated the first time you run **GmailMenu.py**.
This means that before building the directory you have to run GmailMenu.py and generate the token from a credentials file obtained from: https://developers.google.com/gmail/api/quickstart/python

#### Build the container

`cd SlackBot/`

`docker build --tag slackbot .`

#### Run the build or the existing image

`export TOKEN=<INSER BOT AUTH TOKEN>`

`docker run --env TOKEN slackbot`


