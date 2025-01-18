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
        // Load the background and horse images
        int trackLength = 600;
        BufferedImage background = ImageIO.read(new File("src/utils/horseRace/background.png"));
        BufferedImage[] horses = new BufferedImage[9];
        for (int i = 0; i < horses.length; i++) {
            horses[i] = ImageIO.read(new File("src/utils/horseRace/horse" + (i + 1) + ".png"));
        }

        int width = background.getWidth();
        int height = background.getHeight();

        // Create a new image with the same dimensions as the background
        BufferedImage result = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = result.createGraphics();

        // Draw the background
        g.drawImage(background, 0, 0, null);

        // Scaling factor (e.g., reduce the horse image size by 30%)
        double scale = 0.3;
        int scaledWidth, scaledHeight;

        // Automatic Y positions based on the number of horses
        int startY = 50;
        int endY = 350;
        int stepY = (endY - startY) / (allHorses.size() - 1);

        // Draw each horse
        for (int i = 0; i < allHorses.size(); i++) {
            Horse horse = allHorses.get(i);
            int x = (int) (horse.getPosition() * (width / (double) trackLength)); // Scale X position based on track length
            int y = startY + i * stepY; // Automatically calculated Y position
            BufferedImage horseImage = horses[horse.getImageNumber()-1];

            // Scale the horse image
            scaledWidth = (int) (horseImage.getWidth() * scale);
            scaledHeight = (int) (horseImage.getHeight() * scale);
            Image scaledHorse = horseImage.getScaledInstance(scaledWidth, scaledHeight, Image.SCALE_SMOOTH);

            if (horse.isFallen()) {
                // Flip the image upside down for fallen horses
                AffineTransform transform = AffineTransform.getScaleInstance(1, -1);
                transform.translate(0, -scaledHeight);
                AffineTransform translate = AffineTransform.getTranslateInstance(x, y + scaledHeight / 4);
                translate.concatenate(transform);
                g.drawImage(scaledHorse, translate, null);
            } else {
                // Draw the horse normally
                g.drawImage(scaledHorse, x, y, null);
            }
        }

        g.dispose();

        // Copy the generated image to the clipboard
        setClipboardImage(result);
    }

    private static void drawHorse(Graphics2D g, String name, int x, int y) {
        // Draw horse (simple representation, can be more complex based on your needs)
        g.setColor(HORSE_COLOR);
        g.fillOval(x, y, 30, 30);  // Draw a simple circle as the horse body
        g.setColor(Color.BLACK);
        g.drawString(name, x - 10, y + 45);  // Horse name below the circle
    }

    public static void showHorses() throws IOException {
        // Lista koni z przykładowymi danymi (nazwy, pozycje, itp.)
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
    

       // Load the horse images
       BufferedImage[] horseImages = new BufferedImage[allHorses.size()];
       for (int i = 0; i < allHorses.size(); i++) {
           // Load images for horses (ensure these files exist)
           horseImages[i] = ImageIO.read(new File("src/utils/horseRace/horse" + (i + 1) + ".png"));
       }
   
       // Create a white background (600x400 size)
       int imageWidth = 700;
       int imageHeight = 640;
       BufferedImage result = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_ARGB);
       Graphics2D g = result.createGraphics();
   
       // Fill background with white color
       g.setColor(Color.WHITE);
       g.fillRect(0, 0, imageWidth, imageHeight);
   
       // Set font and color for drawing text
       g.setFont(new Font("Arial", Font.BOLD, 14));
       g.setColor(TEXT_COLOR);
   
       // Define the positions for horses in 3 columns and 3 rows
       int xOffset = 20; // Left margin
       int yOffset = 20; // Top margin
       int xSpacing = 220; // Horizontal space between horses
       int ySpacing = 200; // Vertical space between horses
   
       // Draw each horse with their name, number, and image
       for (int i = 0; i < allHorses.size(); i++) {
           Horse horse = allHorses.get(i);
   
           // Calculate x and y positions based on the 3x3 grid
           int x = xOffset + (i % 3) * xSpacing; // Position in column
           int y = yOffset + (i / 3) * ySpacing; // Position in row
   
           // Draw the horse's number and name
           g.drawString("#" + (i + 1), x+20, y);
           g.drawString(horse.getName(), x+20, y + 20);
   
           // Draw the horse's image next to the name and number
           BufferedImage horseImage = horseImages[i];
           int imageWidthScaled = (int) (horseImage.getWidth() * 0.2); // Scale image size (20%)
           int imageHeightScaled = (int) (horseImage.getHeight() * 0.2);
   
           // Draw the image to the right of the name and number
           g.drawImage(horseImage, x + 50, y - 10, imageWidthScaled, imageHeightScaled, null);
       }
   
       g.dispose();
   
       // Copy the generated image to the clipboard
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