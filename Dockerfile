FROM openjdk:17-jdk-slim

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    chromium \
    chromium-driver

RUN apt-get update && apt-get install -y wget unzip chromium && \
wget https://chromedriver.storage.googleapis.com/$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip && \
unzip chromedriver_linux64.zip && \
chmod +x chromedriver && \
mv chromedriver /usr/local/bin/ && \
rm chromedriver_linux64.zip

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromium-driver

COPY ./MessengerGroupChatBot.jar /MessengerGroupChatBot.jar

RUN mkdir -p /app/logs && touch /app/logs/application.log

COPY ./src/resources/config.properties /app/src/resources/config.properties

RUN mkdir -p src/repository

COPY ./src/repository/*.txt /src/repository/

RUN chmod -R 755 src


ENTRYPOINT ["java", "-jar", "/MessengerGroupChatBot.jar"]
