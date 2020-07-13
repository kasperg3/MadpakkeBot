FROM python:3.7
COPY . .

RUN apt update && \
    apt install -y default-jre && \
    apt install -y locales && \
    sed -i -e 's/# da_DK.UTF-8 UTF-8/da_DK.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales
ENV LANG da_DK.UTF-8
ENV LC_ALL da_DK.UTF-8

RUN pip install -r requirements.txt

EXPOSE ${PORT:-8080}

CMD python ./main.py --token="--token=${TOKEN}"