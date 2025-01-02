FROM openjdk:17-jdk-slim

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    chromium \
    chromium-driver

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromium-driver

COPY ./MessengerGroupChatBot.jar /MessengerGroupChatBot.jar

RUN mkdir -p /app/logs && touch /app/logs/application.log

COPY ./src/resources/config.properties /app/src/resources/config.properties

ENTRYPOINT ["java", "-jar", "/MessengerGroupChatBot.jar"]
