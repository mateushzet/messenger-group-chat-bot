package utils;

import java.util.List;
import java.awt.image.BufferedImage;
import java.nio.file.Path;
import java.nio.file.Paths;

import javax.imageio.ImageIO;

import model.GameHelp;

public class HelpDataProvider {

    public static List<String> getGames() {
        return List.of("roulette", "slots", "mines", "blackjack", "plinko", "coinflip", "balatro", "case", "colors", "crash", "dice", "race", "jackpot", "lotto", "sports", "tree");
    }

    public static GameHelp getGameHelp(String name) {
            switch (name.toLowerCase()) {
                case "roulette":
                    return loadGameHelp("Bet on numbers or colors and spin the roulette wheel.",
                        List.of(
                        "• /roulette <amount> <color/number>",
                        "• Available colors: red, black, green",
                        "• Available numbers: 0-12",
                        "• You can use /r instead of /roulette",
                        "• Multipliers: red x2, black x2, green x12, number x12",
                        "",
                        "",
                        "",
                        "",
                        "",
                        ""
                    ),
                    name);

                case "slots":
                    return loadGameHelp("Spin the slot machine and match symbols to win. In multi games, you will see 5 rows, each row is a"
                                        +"separate game, and all 5 results are combined to give a final outcome.",
                        List.of(
                            "",
                            "• /slots <amount>",
                            "• /slots multi <amount>",
                            "• You can use /s instead of /slots",
                            "• You can use /m instead of /multi",
                            "• Your bet must be at least 0.5% of your total balance and at least 10 coins",
                            "",
                            "• Each lost game adds 10% of the bet amount to the jackpot pool",
                            "• If you hit the jackpot, you can win up to 100x your bet,", 
                            "  but no more than the current jackpot pool value",
                            "• To hit the jackpot, you need to get 3 big win symbols",
                            "• Every day the jackpot pool increases by 50 coins",
                            "",
                            "• Multipliers:",
                            "Three of a kind ×5",
                            "Two + wild card ×2",
                            "Two wild cards ×2",
                            "Two of a kind ×1.5",
                            "One wild card ×1.1",
                            "No match ×0"
                        ),
                        name);

            case "mines":
                return loadGameHelp(
                    "Avoid hidden bombs and uncover rewards by carefully selecting safe spots on the minefield. "
                    + "Choose how many mines to place and how much to bet. "
                    + "If you don't specify the number of mines at the start, the default is 3 mines. "
                    + "The more mines on the field, the higher the risk but also the bigger potential rewards.",
                    List.of(
                        "",
                        "You can use /m instead of /mines for all commands.",
                        "",
                        "• /mines start <amount> [minesCount]",
                        "  - <amount>: your bet (minimum 10 coins)",
                        "  - [minesCount]: optional number of hidden mines (between 1 and 24, default is 3)",
                        "",
                        "• /mines cashout",
                        "  - Cash out your current winnings before hitting",
                        "    a mine to secure your prize.",
                        "",
                        "• /mines <field numbers>",
                        "  - Choose one or multiple fields to reveal by listing numbers",
                        "     separated by commas (no spaces), e.g., 1,2,3,4,5.",
                        "",
                        "• Try to reveal safe spots without hitting a mine.",
                        "• Each safe spot you uncover increases your multiplier",
                        "   and potential winnings.",
                        "• Hitting a mine ends the game and you lose your bet."
                    ),
                    name
                );

                case "blackjack":
                    return loadGameHelp(
                        "Try to beat the dealer by getting closer to 21 than they do, without going over 21.\n" +
                        "The dealer will draw until they reach at least 17. You can double only on your initial hand, " +
                        "and splitting is not available after doubling." +
                        "Standard win pays x2 your bet. Hitting a blackjack (21 with your first two cards) pays x2.5.",
                        List.of(
                            "",
                            "• You can use /b instead of /blackjack.",
                            "• /blackjack bet <amount>: Start a new game by betting the specified amount.",
                            "",
                            "• /blackjack hit: Take another card.",
                            "• /blackjack stand: End your turn and let the dealer play.",
                            "",
                            "• /blackjack double: Double your bet,", "  take one last card, and end your turn.",
                            "",
                            "• /blackjack split: If you have a pair,", "  split them into two hands (if allowed).",
                            "  After splitting, choose which hand to hit: /bj hit 1 or /bj hit 2. ",
                            "  At the end confirm both hands with /bj stand."
                        ),
                        name
                    );

                case "plinko":
                    return loadGameHelp(
                        "Drop a chip down the Plinko board and win based on where it lands.\n" +
                        "You can choose a risk level that affects the distribution of multipliers. Higher risk offers higher potential rewards, but more variance.",
                        List.of(
                            "",
                            "• /plinko <amount> <risk>: Play Plinko by betting a specified amount and choosing a risk level.",
                            "  You can use /p instead of /plinko",
                            "  Example: /plinko 100 medium",
                            "",
                            "• Accepted risk levels:",
                            "  - low (or l)",
                            "  - medium (or m)",
                            "  - high (or h)",
                            "",
                            "",
                            "",
                            ""
                        ),
                        name
                    );

                case "coinflip":
                    return loadGameHelp(
                        "Start or join a coinflip game against another player. Winner gets the full pot.",
                        List.of(
                            "• /coinflip bet <amount>: Start a new coinflip game with the specified bet.",
                            "• /coinflip games: View currently open coinflip games.",
                            "• /coinflip accept <id>: Accept an existing game by ID and flip the coin.",
                            "• /coinflip cancel <id>: Cancel your own active coinflip game.",
                            "",
                            ""
                        ),
                        name
                    );

                case "balatro":
                    return loadGameHelp(
                        "Play a simplified Balatro-inspired card game. Start by betting coins and building the strongest hand using jokers, discards, and card combos. Final score depends on total card value and hand type. Jokers apply bonuses. Payout increases with higher score.",
                        List.of(
                            "",
                            "• Available Commands:",
                            "   You can use command prefixes: `/balatro`, `/bal`, or `/b`.",
                            "- /bal bet <amount> or /bal b <amount> — start a new game with a given bet.",
                            "- /bal jocker <1|2|3> or /bal j <1|2|3> — choose a joker from the 3 offered options.",
                            "- /bal discard <indexes> or /bal d <indexes> — discard cards by index, e.g., `/b discard 1,3,5`.",
                            "- /bal stand or /bal s — end the game and finalize your score.",
                            "- /bal help — show help message.",
                            "",
                            "• Multipliers (Mults):",
                            "- High Card (+1): Highest single card.",
                            "- Pair (+2): Two cards of the same rank.",
                            "- Two Pair (+3): Two distinct pairs.",
                            "- Three of a Kind (+4): Three cards of the same rank.",
                            "- Straight (+5): Five consecutive ranks, any suit.",
                            "- Flush (+6): Five cards of the same suit, any rank.",
                            "- Full House (+7): Three of a kind + a pair.",
                            "- Four of a Kind (+8): Four cards of the same rank.",
                            "- Straight Flush (+9): Straight of the same suit.",
                            "- Royal Flush (+10): A♠, K♠, Q♠, J♠, 10♠ — same suit.",
                            "",
                            "• Chips Points (Base Value per Card):",
                            "- Each card gives chips based on its rank:",
                            "  - 2 = 2 chips",
                            "  - 3 = 3 chips",
                            "  - ...",
                            "  - 10 = 10 chips",
                            "  - Jack = 10 chips",
                            "  - Queen = 10 chips",
                            "  - King = 13 chips",
                            "  - Ace = 11 chips",
                            "- Total hand value = sum of card values + bonus for hand ranking.",
                            "",
                            "• Jokers:",
                            "- Some jokers provide flat bonus chips per card rank or suit.",
                            "- Others multiply total chip value or only for specific hands.",
                            "",
                            "• Payouts Based on Final Score:",
                            "Your winnings depend on the final score calculated as (multiplier * chips):",
                            "- Final Score < 120: no winnings (0 chips).",
                            "- 120 ≤ Final Score < 150: half of your bet is returned.",
                            "- 150 ≤ Final Score < 200: double your bet.",
                            "- 200 ≤ Final Score < 400: triple your bet.",
                            "- 400 ≤ Final Score < 600: 5x your bet.",
                            "- 600 ≤ Final Score < 1000: 8x your bet.",
                            "- 1000 ≤ Final Score < 1400: 12x your bet.",
                            "- Final Score ≥ 1400: 20x your bet."
                        ),
                        name
                    );

                case "case":
                    return loadGameHelp("Open cases and get random items of varying value.",
                        List.of(
                            "• Available Commands:",
                            "   Use prefixes: /case, /c.",
                            "- /case <amount> — open a case costing the specified amount (valid amounts: 10, 100, 1000).",
                            "",
                            "• Case Details:",
                            "- Case costs: 10, 100, or 1000 coins.",
                            "- Each case contains random items with values ranging depending on the case:",
                            "   • 10-coin case: item values from 0 to 48 coins.",
                            "   • 100-coin case: item values from 0 to 1050 coins.",
                            "   • 1000-coin case: item values from 17 to 13000 coins.",
                            "",
                            "",
                            "",
                            "",
                            "",
                            ""
                        ),
                        name
                    );

                case "colors":
                    return loadGameHelp(
                        "Bet on color outcomes in a game where you pick one or multiple colors and try to win based on random draws.",
                        List.of(
                            "• Available Commands:",
                            "   Use prefixes: `/colors`, `/c`.",
                            "- `colors <amount> <red|green|blue|gold|black>` — place a bet on a single color.",
                            "- `colors <blackBet> <redBet> <blueBet> <goldBet>` — place bets on multiple colors at once.",
                            "",
                            "• How to play:",
                            "- The game randomly selects a winning color from black, red, blue, or gold.",
                            "- You win if your chosen color matches the winning color.",
                            "",
                            "• Colors and Payout Multipliers:",
                            "- Black: 2x your bet.",
                            "- Red: 3x your bet.",
                            "- Blue: 5x your bet.",
                            "- Gold: 50x your bet (rare and high reward).",
                            ""
                        ),
                        name
                    );

                case "crash":
                    return loadGameHelp(
                        "Cash out before the multiplier crashes! Try to stop at the right moment to maximize your winnings.",
                        List.of(
                            "• Available Commands:",
                            "- `/crash <amount> <multiplier>` — place a bet and choose the multiplier at which you want to cash out.",
                            "",
                            "• How to play:",
                            "- Place your bet with an amount and decide at which multiplier you want to cash out.",
                            "",
                            "- Multiplier must be between 1.00 and 100.00.",
                            "",
                            "",
                            "",
                            "",
                            ""
                        ),
                        name
                    );

                case "dice":
                    return loadGameHelp(
                        "Roll dice and try to get the highest multiplier after one reroll.",
                        List.of(
                            "• Available Commands:",
                            "   Use prefixes: `/dice`, `/d`.",
                            "- `/dice bet <amount>` — start a new game and place your bet.",
                            "- `/dice reroll <dice indices>` — reroll selected dice (indices from 1 to 6, comma-separated).",
                            "- `/dice stand` — end your turn and cash out your winnings.",
                            "",
                            "• How to play:",
                            "- Start by placing a bet with `dice bet <amount>`.",
                            "- You get 6 dice rolled automatically.",
                            "- You can reroll any dice once by specifying their indices with `/dice reroll 1,3,5`",
                            "- If you choose not to reroll, use `/dice stand` to finish.",
                            "- Your winnings are calculated by a multiplier based on the dice combination.",
                            "",
                            "• Multipliers and rewards:",
                            "- Six of a kind or a straight = 7x multiplier.",
                            "- Five of a kind or three pairs = 3x multiplier.",
                            "- Four of a kind + a pair = 2x multiplier.",
                            "- Two triplets or four of a kind alone = 1.5x multiplier.",
                            "- One triplet + one pair = 0.4x multiplier.",
                            "- One triplet alone = 0.2x multiplier.",
                            "- Otherwise, no multiplier (0).",
                            ""
                        ),
                        name
                    );

                case "race":
                    return loadGameHelp(
                        "Bet on a horse and see if it wins the race. Each horse has unique stats affecting the race outcome: " +
                        "min move (minimum distance per round), max move (maximum distance per round), and fall chance (probability the horse will fall in a round). " +
                        "After falling, the horse will not make a move that round.",
                        List.of(
                            "",
                            "/race horses — display all horses with their numbers and images",
                            "",
                            "/race bet <amount> <horseNumber> —",
                            "   place a bet of <amount> coins",
                            "   on horse number <horseNumber>",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            ""
                        ),
                        name
                    );

                case "jackpot":
                    return loadGameHelp(
                        "Contribute coins to the jackpot pot. After 10 minutes, a winner is randomly drawn to take the entire pot. " +
                        "If only one player joins, the game will add a bot with the same bet amount to compete.",
                        List.of(
                            "/jackpot <amount> — place a bet of <amount> coins to join the jackpot pot",
                            "",
                            "",
                            "",
                            "",
                            ""
                        ),
                        name
                    );

                case "lotto":
                    return loadGameHelp(
                        "Buy a lottery ticket by choosing 6 unique numbers from 1 to 49 or get random numbers. " +
                        "You can also play a multi-ticket mode (5 tickets at once) with chosen or random numbers to increase your chances. " +
                        "The prize pool is randomly set every 10 minutes and can range from 1,000,000 to 20,000,000 coins.",
                        List.of(
                            "",
                            "Prefix can be /lotto or /l",
                            "",
                            "/lotto <amount> <num1,num2,num3,num4,num5,num6> — buy a ticket with your chosen numbers",
                            "/lotto <amount> random — buy a ticket with randomly generated numbers",
                            "/lotto multi <amount> <num1,num2,num3,num4,num5,num6|random> — buy 5 tickets",
                            "",
                            "Prize tiers and winnings based on your matches:",
                            "- 0 or 1 match: lose your bet",
                            "- 2 matches: partial refund between 50% to 150% of your bet",
                            "- 3 matches: small prize between 10x and 50x your bet",
                            "- 4 matches: medium prize between 300x and 600x your bet",
                            "- 5 matches: big prize, roughly 0.1% of the prize pool times your bet",
                            "- 6 matches: jackpot prize, roughly 1% of the prize pool times your bet",
                            "",
                            "The prize pool changes every 10 minutes",
                            "and can be from 1,000,000 up to 20,000,000 coins."
                        ),
                        name
                    );

                case "sports":
                    return loadGameHelp(
                        "Place bets on upcoming sports matches and win by predicting the correct outcome (home win, away win, or draw). " +
                        "Check results and your payouts anytime, and view available matches with current odds.",
                        List.of(
                            "/sports bet <amount> <match_id> <outcome: home, away, draw>",
                            "/sports checkresults",
                            "/sports showmatches",
                            "",
                            "",
                            "",
                            "",
                            ""
                        ),
                        name
                    );

                case "tree":
                    return loadGameHelp(
                        "Grow a tree by planting coins and watering it over time to increase your rewards. " +
                        "Each growth phase increases your potential profit, but beware — there is a 10% chance the tree will wither at a random, pre-chosen phase, causing you to lose your investment. ",
                        List.of(
                            "",
                            "You can cut the tree early to cash out your profit based on the current growth phase:",
                            " - Phase 0: 50% of your investment",
                            " - Phase 1: 105% of your investment",
                            " - Phase 2: 110% of your investment",
                            " - Phase 3: 115% of your investment",
                            " - Phase 4: 125% of your investment",
                            " - Phase 5: 150% of your investment",
                            "",
                            "/tree plant <amount> - Plant a tree by investing coins.",
                            "/tree water - Check the current status and growth phase of your tree.",
                            "/tree cut - Cut down the tree to collect your coins and profit.",
                            "/tree help - Show this help message."
                        ),
                        name
                    );

                default:
                    return new GameHelp("Unknown game", List.of(), new BufferedImage(1, 1, BufferedImage.TYPE_INT_ARGB));
            }
    }

    private static GameHelp loadGameHelp(String description, List<String> commands, String name) {
        try {
            String fileName = name + "_example.png";
            Path fullPath = Paths.get("src", "resources", "help_images", fileName);
            BufferedImage image = ImageIO.read(fullPath.toFile());
            return new GameHelp(description, commands, image);
        } catch (Exception e) {
            e.printStackTrace();
            return new GameHelp(description + " (image not found)", commands,
                new BufferedImage(1, 1, BufferedImage.TYPE_INT_ARGB));
        }
    }
}
