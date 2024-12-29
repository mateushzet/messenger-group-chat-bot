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

ENTRYPOINT ["java", "-jar", "/MessengerGroupChatBot.jar"]
