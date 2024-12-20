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

COPY ./chromedriver.exe /chromedriver.exe


# Pobierz i zainstaluj chromedriver
RUN wget -q https://chromedriver.storage.googleapis.com/111.0.5563.64/chromedriver_linux64.zip -O chromedriver.zip \
    && unzip chromedriver.zip -d /usr/local/bin/ \
    && rm chromedriver.zip

# Ustaw uprawnienia do pliku chromedriver
RUN chmod +x /usr/local/bin/chromedriver

COPY ./chromedriver /chromedriver
RUN chmod +x /chromedriver

ENTRYPOINT ["java", "-jar", "/MessengerGroupChatBot.jar"]

