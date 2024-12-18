package service.roulette;

public enum BetType {
    RED(-1),
    BLACK(-2),
    GREEN(-3),
    INVALID(-4);

    private final int code;

    BetType(int code) {
        this.code = code;
    }

    public int getCode() {
        return code;
    }

    public static BetType fromString(String field) {
        switch (field.toLowerCase()) {
            case "red":
                return RED;
            case "black":
                return BLACK;
            case "green":
                return GREEN;
            default:
                return INVALID;
        }
    }
}