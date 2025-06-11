package games.balatro;

import model.CommandContext;
import repository.UserRepository;
import service.MessageService;
import service.UserService;
import utils.ImageUtils;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class BalatroGameController {

    public static void handleBalatroCommand(CommandContext context) {
        String userName = context.getUserName();
        String firstArg = context.getFirstArgument();
        String secondArg = context.getSecondArgument();

        if (firstArg == null) {
            MessageService.sendMessage(userName + ", please provide a command.");
            return;
        }

        BalatroGame currentGame = BalatroGameRepository.getGameByUserName(userName);

        switch (firstArg.toLowerCase()) {
            case "bet":
            case "b":
                if (secondArg == null) {
                    MessageService.sendMessage(userName + ", please specify the bet amount.");
                    return;
                }
                int betAmount = UserService.validateAndParseBetAmount(userName, secondArg);
                if (betAmount == -1) {
                    return;
                }

                if (betAmount != 10) {
                    MessageService.sendMessage(userName + ", kaganiec na bet = 10 w fazie testow.");
                    return;
                }

                if (currentGame != null) {
                    MessageService.sendMessage(userName + ", you already have an active game.");
                    return;
                }

                UserService.updateAndRetriveUserBalance(userName, -betAmount);
                currentGame = BalatroGameService.startNewGame(userName, betAmount, UserRepository.getCurrentUserBalance(userName, false));
                BalatroGameRepository.saveGame(currentGame);
                break;

            case "jocker":
            case "j":
                if (currentGame == null || currentGame.getGameStatus() != BalatroGameService.STATUS_NEW) {
                    MessageService.sendMessage(userName + ", no game is waiting for joker selection.");
                    return;
                }
                try {
                    int jokerId = Integer.parseInt(secondArg);
                    if (jokerId != 1 && jokerId != 2 && jokerId != 3) {
                        MessageService.sendMessage(userName + ", invalid joker number. Choose: 1, 2 or 3");
                        return;
                    }
                    System.out.println(jokerId +" "+currentGame.getAvailableJokerIds().get(jokerId-1));
                    jokerId = currentGame.getAvailableJokerIds().get(jokerId-1);

                    BalatroGameService.playTurn(currentGame, "chooseJoker", jokerId);
                    System.out.println("po playtrun");
                    BalatroGameRepository.updateGame(currentGame);
                    System.out.println("update game");
                } catch (NumberFormatException e) {
                    System.out.println("teeeeeest2");
                    System.out.println(e.toString());
                    System.out.println(e);
                    e.printStackTrace();
                    MessageService.sendMessage(userName + ", invalid joker number. Choose: 1, 2 or 3");
                }
                break;

            case "discard":
            case "d":
                if (currentGame == null || 
                    (currentGame.getGameStatus() != BalatroGameService.STATUS_JOKER_SELECTED &&
                     currentGame.getGameStatus() != BalatroGameService.STATUS_CARDS_EXCHANGED)) {
                    MessageService.sendMessage(userName + ", you cannot discard cards right now.");
                    return;
                }
                if (secondArg == null || secondArg.isEmpty()) {
                    MessageService.sendMessage(userName + ", please specify cards to discard, e.g., discard 1,2");
                    return;
                }
                List<String> cardsToDiscard = parseDiscardArgument(secondArg, currentGame.getPlayerHand());
                if (cardsToDiscard.isEmpty()) {
                    MessageService.sendMessage(userName + ", no valid cards specified to discard.");
                    return;
                }
                BalatroGameService.playTurn(currentGame, "discard", cardsToDiscard);
                BalatroGameRepository.updateGame(currentGame);

                if (currentGame.getGameStatus() == BalatroGameService.STATUS_GAME_OVER) {
                    BalatroGameService.finalizeGame(userName, currentGame, context);
                }
                break;

            case "stand":
            case "s":
                if (currentGame == null) {
                    MessageService.sendMessage(userName + ", no active game.");
                    return;
                }
                currentGame.setGameStatus(BalatroGameService.STATUS_GAME_OVER);
                BalatroGameRepository.updateGame(currentGame);

                BalatroGameService.finalizeGame(userName, currentGame, context);
                break;

            case "help":
            case "h":

                String helpMessage = """

                **Available Commands**:
                - `bet <amount>` or `b <amount>` — start a new game with a given bet.
                - `jocker <1|2|3>` or `j <1|2|3>` — choose a joker from the 3 offered options.
                - `discard <indexes>` or `d <indexes>` — discard cards by index, e.g., `discard 1,3,5`.
                - `stand` or `s`— end the game and finalize your score.
                - `help` — show this help message.

                **Multipliers (Mults)**:
                - High Card (+1): Highest single card.
                - Pair (+2): Two cards of the same rank.
                - Two Pair (+3): Two distinct pairs.
                - Three of a Kind (+4): Three cards of the same rank.
                - Straight (+5): Five consecutive ranks, any suit.
                - Flush (+6): Five cards of the same suit, any rank.
                - Full House (+7): Three of a kind + a pair.
                - Four of a Kind (+8): Four cards of the same rank.
                - Straight Flush (+9): Straight of the same suit.
                - Royal Flush (+10): A♠, K♠, Q♠, J♠, 10♠ — same suit.

                **Chips Points (Base Value per Card)**:
                - Each card gives chips based on its rank:
                  - 2 = 2 chips
                  - 3 = 3 chips
                  - ...
                  - 10 = 10 chips
                  - Jack = 10 chips
                  - Queen = 10 chips
                  - King = 13 chips
                  - Ace = 11 chips
                - Total hand value = sum of card values + bonus for hand ranking.

                **Jokers**:
                - Some jokers provide flat bonus chips per card rank or suit.
                - Others multiply total chip value or only for specific hands.

                **Payouts Based on Final Score:**
                Your winnings depend on the final score calculated as (multiplier * chips):

                - Final Score < 120: no winnings (0 chips).
                - 120 ≤ Final Score < 150: half of your bet is returned.
                - 150 ≤ Final Score < 200: double your bet.
                - 200 ≤ Final Score < 400: triple your bet.
                - 400 ≤ Final Score < 600: 5x your bet.
                - 600 ≤ Final Score < 1000: 8x your bet.
                - 1000 ≤ Final Score < 1400: 12x your bet.
                - Final Score ≥ 1400: 20x your bet.

                """;

                ImageUtils.setClipboardImage(BalatroImageGenerator.createHelpImage(helpMessage));
                MessageService.sendMessageFromClipboard(false);
                return;

            default:
                MessageService.sendMessage(userName + ", unknown command: " + firstArg);
                break;
        }
    }

    private static List<String> parseDiscardArgument(String arg, List<String> playerHand) {
        List<String> indices;

        if (arg.contains(",")) {

            indices = Arrays.stream(arg.split(","))
                            .map(String::trim)
                            .filter(s -> s.matches("\\d+"))
                            .collect(Collectors.toList());
        } else {

            indices = arg.chars()
                        .mapToObj(c -> String.valueOf((char) c))
                        .filter(s -> s.matches("\\d"))
                        .collect(Collectors.toList());
        }

        return indices.stream()
                    .map(Integer::parseInt)
                    .filter(i -> i >= 1 && i <= playerHand.size())
                    .map(i -> playerHand.get(i - 1))
                    .collect(Collectors.toList());
    }
    
}
