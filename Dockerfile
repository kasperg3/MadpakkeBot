FROM python:3.7
COPY . /slackbot/
WORKDIR /slackbot/

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# da_DK.UTF-8 UTF-8/da_DK.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales
ENV LANG da_DK.UTF-8
ENV LC_ALL da_DK.UTF-8

RUN pip install -r requirements.txt
CMD ls
CMD pwd
CMD python ./main.py --token="xoxb-18948748048-1249904618129-6z4Pkq4OUxvxq6TxFD6sEsSf"