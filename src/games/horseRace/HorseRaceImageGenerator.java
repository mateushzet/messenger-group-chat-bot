package games.horseRace;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.awt.geom.AffineTransform;
import java.io.File;
import java.io.IOException;
import java.util.List;

import javax.imageio.ImageIO;

import model.Horse;
import utils.ImageUtils;

public class HorseRaceImageGenerator {

    private static final Color TEXT_COLOR = new Color(50, 50, 50);

    public static BufferedImage drawHorseRace(List<Horse> allHorses, int selectedHorse, boolean lastFrame, int userBalance, int betAmount, String playerName) throws IOException {
        int trackLength = 600;
        BufferedImage background = ImageIO.read(new File("src/games/horseRace/horseRaceImages/background.png"));
        BufferedImage[] horses = new BufferedImage[9];
        for (int i = 0; i < horses.length; i++) {
            horses[i] = ImageIO.read(new File("src/games/horseRace/horseRaceImages/horse" + (i + 1) + ".png"));
        }
    
        int width = background.getWidth();
        int height = background.getHeight();
    
        BufferedImage result = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = result.createGraphics();
    
        g.drawImage(background, 0, 0, null);
    
        double scale = 0.3;
        int scaledWidth, scaledHeight;
    
        int startY = 50;
        int endY = 350;
        int stepY = (endY - startY) / (allHorses.size() - 1);
    
        for (int i = 0; i < allHorses.size(); i++) {
            Horse horse = allHorses.get(i);
            int x = (int) (horse.getPosition() * (width / (double) trackLength));
            int y = startY + i * stepY;
            BufferedImage horseImage = horses[horse.getImageNumber() - 1];
    
            scaledWidth = (int) (horseImage.getWidth() * scale);
            scaledHeight = (int) (horseImage.getHeight() * scale);
            Image scaledHorse = horseImage.getScaledInstance(scaledWidth, scaledHeight, Image.SCALE_SMOOTH);
    
            if (horse.isFallen()) {
                AffineTransform transform = AffineTransform.getScaleInstance(1, -1);
                transform.translate(0, -scaledHeight);
                AffineTransform translate = AffineTransform.getTranslateInstance(x, y + scaledHeight / 4);
                translate.concatenate(transform);
                g.drawImage(scaledHorse, translate, null);
            } else {
                g.drawImage(scaledHorse, x, y, null);
            }
        }
    
        if (lastFrame) {
            Horse winner = allHorses.stream()
                    .max((h1, h2) -> Integer.compare(h1.getPosition(), h2.getPosition()))
                    .orElse(null);
    
            if (winner != null) {
                boolean isWinner = winner.getImageNumber() == selectedHorse;
                int winnings = isWinner ? betAmount * 6 : 0;
                int newBalance = userBalance + winnings;
    
                g.setFont(new Font("Arial", Font.BOLD, 24));
                g.setColor(Color.WHITE);
    
                g.setColor(new Color(0, 0, 0, 150));
                g.fillRoundRect(100, 100, 600, 350, 20, 20);
    
                g.setColor(Color.WHITE);
                g.drawString("Winner: Horse #" + winner.getImageNumber() + " - " + winner.getName(), 120, 150);
                g.drawString(playerName + ", your balance: " + (isWinner ? newBalance + betAmount : newBalance), 120, 180);
                g.drawString("You " + (isWinner ? "won: " + winnings : "lost: " + betAmount), 120, 210);
    

                BufferedImage winnerImage = horses[winner.getImageNumber() - 1];
                double winnerScale = 0.1;
                int winnerWidth = (int) (winnerImage.getWidth() * winnerScale);
                int winnerHeight = (int) (winnerImage.getHeight() * winnerScale);
                Image scaledWinner = winnerImage.getScaledInstance(winnerWidth, winnerHeight, Image.SCALE_SMOOTH);
    
                g.drawImage(scaledWinner, 120, 230, null);
            }
        }
    
        g.dispose();
    
        return result;
    }

    public static void showHorses() throws IOException {
    
        int horseCount = 9;

       BufferedImage[] horseImages = new BufferedImage[horseCount];
       for (int i = 0; i < horseCount; i++) {
           horseImages[i] = ImageIO.read(new File("src/games/horseRace/horseRaceImages/horse" + (i + 1) + ".png"));
       }
   
       int imageWidth = 700;
       int imageHeight = 640;
       BufferedImage result = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_ARGB);
       Graphics2D g = result.createGraphics();
   
       g.setColor(Color.WHITE);
       g.fillRect(0, 0, imageWidth, imageHeight);
   
       g.setFont(new Font("Arial", Font.BOLD, 14));
       g.setColor(TEXT_COLOR);
   
       int xOffset = 20;
       int yOffset = 20;
       int xSpacing = 220;
       int ySpacing = 200;
   
       List<Horse> allHorses = Horse.copyHorses(HorseRaceBettingService.allHorses);

       for (int i = 0; i < horseCount; i++) {
           Horse horse = allHorses.get(i);
   
           int x = xOffset + (i % 3) * xSpacing;
           int y = yOffset + (i / 3) * ySpacing;
   
           g.drawString("#" + (i + 1), x+20, y);
           g.drawString(horse.getName(), x+20, y + 20);
   
           BufferedImage horseImage = horseImages[i];
           int imageWidthScaled = (int) (horseImage.getWidth() * 0.2);
           int imageHeightScaled = (int) (horseImage.getHeight() * 0.2);
   
           g.drawImage(horseImage, x + 50, y - 10, imageWidthScaled, imageHeightScaled, null);
       }
   
       g.dispose();
   
       ImageUtils.setClipboardImage(result);
    }
    
}