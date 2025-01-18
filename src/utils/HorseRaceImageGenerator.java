package utils;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.awt.datatransfer.*;
import java.awt.geom.AffineTransform;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import javax.imageio.ImageIO;

import model.Horse;

public class HorseRaceImageGenerator {

    private static final Color TEXT_COLOR = new Color(50, 50, 50);
    private static final Color WIN_COLOR = new Color(50, 200, 50);
    private static final Color LOSE_COLOR = new Color(200, 50, 50);
    private static final Color HORSE_COLOR = new Color(255, 200, 50);

    public static void drawHorseRace(List<Horse> allHorses) throws IOException {
        int trackLength = 600;
        BufferedImage background = ImageIO.read(new File("src/utils/horseRace/background.png"));
        BufferedImage[] horses = new BufferedImage[9];
        for (int i = 0; i < horses.length; i++) {
            horses[i] = ImageIO.read(new File("src/utils/horseRace/horse" + (i + 1) + ".png"));
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
            BufferedImage horseImage = horses[horse.getImageNumber()-1];

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

        setClipboardImage(result);
    }

    public static void showHorses() throws IOException {
         List<Horse> allHorses = new ArrayList<>();
            allHorses.add(new Horse("Thunderbolt", 50, 150, 0.05, 1));
            allHorses.add(new Horse("Lightning", 100, 200, 0.1, 2));
            allHorses.add(new Horse("Shadow", 70, 120, 0.02, 3));
            allHorses.add(new Horse("Blaze", 80, 180, 0.08, 4));
            allHorses.add(new Horse("Spirit", 60, 140, 0.03, 5));
            allHorses.add(new Horse("Flash", 90, 160, 0.07, 6));
            allHorses.add(new Horse("Storm", 100, 250, 0.12, 7));
            allHorses.add(new Horse("Comet", 120, 200, 0.1, 8));
            allHorses.add(new Horse("Fury", 110, 190, 0.09, 9));
    
       BufferedImage[] horseImages = new BufferedImage[allHorses.size()];
       for (int i = 0; i < allHorses.size(); i++) {
           horseImages[i] = ImageIO.read(new File("src/utils/horseRace/horse" + (i + 1) + ".png"));
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
   
       for (int i = 0; i < allHorses.size(); i++) {
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
   
       setClipboardImage(result);
    }
    

    private static void setClipboardImage(final BufferedImage image) {
        TransferableImage transferable = new TransferableImage(image);
        Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
        clipboard.setContents(transferable, null);
    }

    private static class TransferableImage implements Transferable {
        private final BufferedImage image;

        public TransferableImage(BufferedImage image) {
            this.image = image;
        }

        @Override
        public DataFlavor[] getTransferDataFlavors() {
            return new DataFlavor[]{DataFlavor.imageFlavor};
        }

        @Override
        public boolean isDataFlavorSupported(DataFlavor flavor) {
            return DataFlavor.imageFlavor.equals(flavor);
        }

        @Override
        public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, IOException {
            if (!isDataFlavorSupported(flavor)) {
                throw new UnsupportedFlavorException(flavor);
            }
            return image;
        }
    }
}