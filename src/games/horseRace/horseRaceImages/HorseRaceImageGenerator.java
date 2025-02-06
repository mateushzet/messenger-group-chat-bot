package games.horseRace.horseRaceImages;

import javax.imageio.ImageIO;

import model.Horse;
import utils.ImageUtils;

import java.util.List;
import java.awt.*;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;

public class HorseRaceImageGenerator {

    public static void drawHorseRace(List<model.Horse> allHorses) throws IOException {

        int trackLength = 600;

        BufferedImage background = ImageIO.read(new File("src/utils/horseRace/background.png"));
        BufferedImage[] horsesImages = new BufferedImage[9];
        for (int i = 0; i < 9; i++) {
            horsesImages[i] = ImageIO.read(new File("src/utils/horseRace/horse" + (i + 1) + ".png"));
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
            BufferedImage horseImage = horsesImages[horse.getImageNumber()-1];
    
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
    
        g.dispose();
    
        ImageUtils.setClipboardImage(result);
    }
}