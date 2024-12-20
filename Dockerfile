FROM openjdk:17-jdk-slim

# Instalacja podstawowych narzędzi
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

# Ustawienie zmiennej środowiskowej dla Google Chrome
ENV CHROME_BIN=/usr/bin/google-chrome

# Pobieranie odpowiedniej wersji ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE_131) && \
    wget https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Ustawienie zmiennej środowiskowej dla ChromeDriver
ENV PATH="/usr/local/bin:$PATH"

# Kopiowanie pliku JAR z aplikacją
COPY ./MessengerGroupChatBot.jar /MessengerGroupChatBot.jar

# Ustawienie punktu wejścia aplikacji
ENTRYPOINT ["java", "-jar", "/MessengerGroupChatBot.jar"]
