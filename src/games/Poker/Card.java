package games.Poker;

class Card {
    private final int value;  // Format: xxxAKQJT 98765432 CDHSrrrr xxPPPPPP

    // Ranks
    public static final int DEUCE = 0;
    public static final int TREY = 1;
    public static final int FOUR = 2;
    public static final int FIVE = 3;
    public static final int SIX = 4;
    public static final int SEVEN = 5;
    public static final int EIGHT = 6;
    public static final int NINE = 7;
    public static final int TEN = 8;
    public static final int JACK = 9;
    public static final int QUEEN = 10;
    public static final int KING = 11;
    public static final int ACE = 12;

    // Suits
    public static final int CLUBS = 0x8000;
    public static final int DIAMONDS = 0x4000;
    public static final int HEARTS = 0x2000;
    public static final int SPADES = 0x1000;

    // Rank symbols
    private static final String RANKS = "23456789TJQKA";
    private static final String SUITS = "shdc";

    public Card(int rank, int suit) {
        if (!isValidRank(rank)) {
            throw new IllegalArgumentException("Invalid rank.");
        }

        if (!isValidSuit(suit)) {
            throw new IllegalArgumentException("Invalid suit.");
        }

        value = (1 << (rank + 16)) | suit | (rank << 8) | Tables.PRIMES[rank];
    }

    public static Card fromString(String string) {
        if (string == null || string.length() != 2) {
            throw new IllegalArgumentException("Card string must be non-null with length of exactly 2.");
        }

        final int rank = RANKS.indexOf(string.charAt(0));
        final int suit = SPADES << SUITS.indexOf(string.charAt(1));

        return new Card(rank, suit);
    }

    public int getRank() {
        return (value >> 8) & 0xF;
    }

    public int getSuit() {
        return value & 0xF000;
    }

    public String toString() {
        char rank = RANKS.charAt(getRank());
        char suit = SUITS.charAt((int) (Math.log(getSuit()) / Math.log(2)) - 12);
        return "" + rank + suit;
    }

    int getValue() {
        return value;
    }

    private static boolean isValidRank(int rank) {
        return rank >= DEUCE && rank <= ACE;
    }

    private static boolean isValidSuit(int suit) {
        return suit == CLUBS || suit == DIAMONDS || suit == HEARTS || suit == SPADES;
    }
}