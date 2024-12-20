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

# Ustawienie uprawnień do wykonywania dla ChromeDriver
RUN chmod +x /usr/local/bin/chromedriver


# Instalacja wymaganych narzędzi (w tym wget, curl i unzip)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    libx11-dev \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libglu1-mesa \
    libfontconfig1 \
    && apt-get clean

# Instalacja Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb && \
    apt-get -f install -y && \
    rm google-chrome-stable_current_amd64.deb

# Instalacja ChromeDriver
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    rm chromedriver_linux64.zip

# Ustawienie zmiennej środowiskowej, aby wskazać ścieżkę do ChromeDriver
ENV PATH="/usr/local/bin:$PATH"

ENTRYPOINT ["java", "-jar", "/MessengerGroupChatBot.jar"]

