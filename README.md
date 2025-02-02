# MessengerGroupChatBot

MessengerGroupChatBot is a bot designed to providie interactive features like math challenges, virtual money system, a slot machine game with a growing jackpot pool, a roulette game, and simple commands.

## Technologies Used
- Java 11
- Selenium WebDriver

## Installation

### Requirements:
- Java 11 or higher

# Commands and Arguments

All available commands and their arguments:

### 1. `time`
   - **Description**: Displays the current time.
   - **Arguments**: None

### 2. `money`
   - **Description**: Displays the player's account balance.
   - **Arguments**: None

### 3. `roulette`
   - **Description**: Starts a roulette game.
   - **Arguments**: 
     - `betAmount` (required): The amount to bet.
     - `colorOrExactnumber` (required): The color to bet on (`red`, `black`, `green`).
     - `history`: Displays the game history.

### 4. `kill`
   - **Description**: Use to terminate the app.
   - **Arguments**:
   - **Arguments**: None

### 5. `stop`
   - **Description**: Stops the app.
   - **Arguments**: None

### 6. `start`
   - **Description**: Starts the app.
   - **Arguments**: None

### 7. `status`
   - **Description**: Shows the status of the app.
   - **Arguments**: None

### 8. `say`
   - **Description**: Bot sends the provided message.
   - **Arguments**:
     - `message` (required): The message content.

### 9. `answer`
   - **Description**: Provides an answer to a math question.
   - **Arguments**:
     - `<answer>` (required): Your answer to the math question.

### 10. `transfer`
   - **Description**: Transfers money to another player.
   - **Arguments**:
     - `amount` (required): The amount to transfer.
     - `targetPlayer` (required): The player name and surname to whom the money will be transferred.

### 11. `rank`
   - **Description**: Displays the players ranking.
   - **Arguments**: None

### 12. `help`
   - **Description**: Displays help information for the commands.
   - **Arguments**: None

### 13. `slots`
   - **Description**: Starts a slot game.
   - **Arguments**:
     - `multi` (optional): Plays 5 slots games with the same bet amount.
     - `betAmount` (required): The amount to bet.
     - `jackpot`: Displayes the jackpot amount.

### 14. `buy`
   - **Description**: Purchases access to available games.
   - **Arguments**:
     - `game` (required): The name of the game to purchase access for.

### 15. `daily`
   - **Description**: Claims the daily bonus.
   - **Arguments**: None

### 16. `hourly`
   - **Description**: Collects the bonus available every full hour.
   - **Arguments**: None

### 17. `coinflip`
   - **Description**: Starts a coin flip game with a specified bet amount or interacts with existing games.
   - **Arguments**:
     - `start betAmount`: Creates a new coin flip game with the given bet amount.
     - `cancel gameId`: Cancels a coin flip game.
     - `accept gameId`: Accepts a coin flip game.
     - `games`: Lists all available coin flip games.

### 18. `colors`
   - **Description**: Starts the color betting game with various betting options.
   - **Arguments**:
     - `multi` (optional): Plays 5 colors games with the same bet amount.
     - `amount` (required): The amount to bet.
     - `singleColor` (required): The color to bet on (`black`, `red`, `blue`, `gold`).
     - `betBlack betRed betBlue betGold`: Specifies bet amounts for multiple colors in order (`black red blue gold`), instead of a single color bet.

### 19. `mines`
   - **Description**: Plays the mines game.
   - **Arguments**:
     - `start betAmount bombCount`: Start the game with a specific bet and number of bombs (default is 3).
     - `cashout`: Cash out the current game.
     - `fieldNumber`: (required after start): Reveal a specific field (number 1-25).

### 20. `skins`
   - **Description**: Changes skins.
   - **Arguments**:
     - `set skin_name`: Sets the player's skin to a specified one.
     - `list`: Lists all available skins.
     - `buy skin_name`: Purchases a specified skin.
     - `shop`: Displays the available skins in the shop.

### 21. `lotto`
   - **Description**: Participates in the lottery.
   - **Arguments**:
     - `multi` (optional): Purchase multiple tickets with the same amount.
     - `amount` (required): Bet amount.
     - `numbers` (required): 6 numbers to choose, separated by commas (e.g., `1, 2, 3, 4, 5, 6`), or use `random` to select random numbers.

### 22. `race`
   - **Description**: Plays a horse racing game.
   - **Arguments**:
     - `horses`: Displays the list of available horses.
     - `betAmount horseNumber`: Place a bet on a specific horse.

### 23. `sports`
   - **Description**: Allows users to place bets on sports matches and check results.
   - **Arguments**:
     - `bet`: Places a bet on a match.  
       - **Usage**: `/sports bet <betAmount> <matchId> <outcome>`  
       - **Outcome options**: `home`, `away`, `draw`
     - `checkresults`: Checks the results of all matches and processes payouts.
     - `showmatches`: Displays a list of available matches.

### 24. `blackjack`
   - **Description**: Plays blackjack.
   - **Arguments**:
     - `betAmount`: The amount to bet.
     - `hit`: Draw another card.
     - `stand`: End your turn.

### 25. `plinko`
   - **Description**: Plays the Plinko game.
   - **Arguments**:
     - `amount` (required): The amount to bet.

### 26. `stats`
   - **Description**: Displays specific statics.
   - **Arguments**:
     - `statsName` (required): The name of the statistics view. Available options:
       - `colors`
       - `games`
       - `global`
       - `lotto`
       - `main`
       - `mines`
       - `race`
       - `roulette`
       - `slots`
