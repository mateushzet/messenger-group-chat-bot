FROM openjdk:17-jdk-slim

# Aktualizacja i instalacja podstawowych narzędzi
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
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libxkbcommon0 \
    xdg-utils \
    && apt-get clean

# Instalacja Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb || true && \
    apt-get -f install -y && \
    rm google-chrome-stable_current_amd64.deb

# Instalacja ChromeDriver
RUN wget https://chromedriver.storage.googleapis.com/131.0.6778.204/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Ustawienie zmiennych środowiskowych dla Selenium
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_DRIVER=/usr/local/bin/chromedriver
ENV PATH="/usr/local/bin:$PATH"

# Dodanie aplikacji
COPY ./MessengerGroupChatBot.jar /MessengerGroupChatBot.jar

# Ustawienie domyślnego polecenia
ENTRYPOINT ["java", "-jar", "/MessengerGroupChatBot.jar"]
