package games.coinflip;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.util.List;

import model.CoinflipGame;
import utils.ImageUtils;

public class CoinflipGamesImageGenerator {
    
    public static void generateActiveGamesImage(List<CoinflipGame> openGames) {
        int imageWidth = 700;
        int imageHeight = 100 + openGames.size() * 50;
        BufferedImage image = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_RGB);

        Graphics2D g = image.createGraphics();

        Color color1 = new Color(102, 204, 255);
        Color color2 = new Color(102, 178, 255);
    
        GradientPaint gradient = new GradientPaint(0, 0, color1, 600, 646, color2);

        g.setPaint(gradient);
        g.fillRect(0, 0, imageWidth, imageHeight);

        g.setFont(new Font("Arial", Font.BOLD, 22));
        g.setColor(Color.BLACK);
        g.drawString("Active Coinflip Games", 20, 50);

        int yPosition = 100;
        for (int i = 0; i < openGames.size(); i++) {
            CoinflipGame game = openGames.get(i);
            String player1 = game.getPlayer1Username();
            int betAmount = game.getBetAmount();
            int gameId = game.getGameId();

          
                g.setColor(new Color(50, 50, 50));

            g.drawString("Game ID: " + gameId + " | " + player1 + " | Bet: " + betAmount + " coins |", 20, yPosition);

            yPosition += 50;
        }

        g.dispose();
        ImageUtils.setClipboardImage(image);
    }

}
