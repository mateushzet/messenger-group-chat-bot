package model;

public class MinesGame {

    private String userName;
    private int betAmount;
    private int totalBombs;
    private int revealedFields;
    private boolean gameInProgress;
    private boolean[][] bombBoard;
    private boolean[][] revealedBoard;

    public MinesGame(String userName, int betAmount, int totalBombs, int revealedFields, boolean gameInProgress, boolean[][] bombBoard, boolean[][] revealedBoard) {
        this.userName = userName;
        this.betAmount = betAmount;
        this.totalBombs = totalBombs;
        this.revealedFields = revealedFields;
        this.gameInProgress = gameInProgress;
        this.bombBoard = bombBoard;
        this.revealedBoard = revealedBoard;
    }

    public String getUserName() {
        return userName;
    }

    public void setUserName(String userName) {
        this.userName = userName;
    }

    public int getBetAmount() {
        return betAmount;
    }

    public void setBetAmount(int betAmount) {
        this.betAmount = betAmount;
    }

    public int getTotalBombs() {
        return totalBombs;
    }

    public void setTotalBombs(int totalBombs) {
        this.totalBombs = totalBombs;
    }

    public int getRevealedFields() {
        return revealedFields;
    }

    public void setRevealedFields(int revealedFields) {
        this.revealedFields = revealedFields;
    }

    public boolean isGameInProgress() {
        return gameInProgress;
    }

    public void setGameInProgress(boolean gameInProgress) {
        this.gameInProgress = gameInProgress;
    }

    public boolean[][] getBombBoard() {
        return bombBoard;
    }

    public void setBombBoard(boolean[][] bombBoard) {
        this.bombBoard = bombBoard;
    }

    public boolean[][] getRevealedBoard() {
        return revealedBoard;
    }

    public void setRevealedBoard(boolean[][] revealedBoard) {
        this.revealedBoard = revealedBoard;
    }

    public void startNewGame(int gridSize, int totalBombs) {
        this.bombBoard = new boolean[gridSize][gridSize];
        this.revealedBoard = new boolean[gridSize][gridSize];
        this.totalBombs = totalBombs;
        this.revealedFields = 0;
        this.gameInProgress = true;

        placeBombsOnBoard(gridSize, totalBombs);
    }

    private void placeBombsOnBoard(int gridSize, int totalBombs) {
        int bombsPlaced = 0;
        while (bombsPlaced < totalBombs) {
            int row = (int) (Math.random() * gridSize);
            int col = (int) (Math.random() * gridSize);

            if (!bombBoard[row][col]) {
                bombBoard[row][col] = true;
                bombsPlaced++;
            }
        }
    }

    public boolean revealField(int row, int col) {
        if (gameInProgress && !revealedBoard[row][col]) {
            revealedBoard[row][col] = true;
            revealedFields++;

            if (bombBoard[row][col]) {
                gameInProgress = false;
                return false;
            }
            return true;
        }
        return false;
    }

    public boolean checkIfWon(int totalFields) {
        return revealedFields == (totalFields - totalBombs);
    }

    public String convertToString(boolean[][] board) {
        StringBuilder sb = new StringBuilder();
        for (boolean[] row : board) {
            for (boolean cell : row) {
                sb.append(cell ? "1" : "0");
            }
            sb.append("\n");
        }
        return sb.toString();
    }

    public boolean[][] convertFromString(String boardString, int rows, int cols) {
        boolean[][] board = new boolean[rows][cols];
        String[] rowsData = boardString.split("\n");
        for (int i = 0; i < rowsData.length; i++) {
            for (int j = 0; j < rowsData[i].length(); j++) {
                board[i][j] = rowsData[i].charAt(j) == '1';
            }
        }
        return board;
    }
}