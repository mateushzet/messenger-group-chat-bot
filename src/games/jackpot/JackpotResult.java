package games.jackpot;

public class JackpotResult {
    private final String winnerName;
    private final int prizeAmount;
    private final byte[] gifBytes;

    public JackpotResult(String winnerName, int prizeAmount, byte[] gifBytes) {
        this.winnerName = winnerName;
        this.prizeAmount = prizeAmount;
        this.gifBytes = gifBytes;
    }

    public String getWinnerName() {
        return winnerName;
    }

    public int getPrizeAmount() {
        return prizeAmount;
    }

    public byte[] getGifBytes() {
        return gifBytes;
    }
}