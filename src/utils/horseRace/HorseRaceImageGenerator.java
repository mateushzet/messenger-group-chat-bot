package utils.horseRace;

import javax.imageio.ImageIO;

import model.Horse;

import java.util.List;
import java.awt.*;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;

public class HorseRaceImageGenerator {

    public static void drawHorseRace(List<model.Horse> allHorses) throws IOException {
        // Ładowanie obrazków
        int trackLength = 600;

        BufferedImage background = ImageIO.read(new File("src/utils/horseRace/background.png"));
        BufferedImage[] horsesImages = new BufferedImage[9];
        for (int i = 0; i < 9; i++) {
            horsesImages[i] = ImageIO.read(new File("src/utils/horseRace/horse" + (i + 1) + ".png"));
        }
    
        int width = background.getWidth();
        int height = background.getHeight();
    
        // Tworzenie nowego obrazu o wymiarach tła
        BufferedImage result = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = result.createGraphics();
    
        // Rysowanie tła
        g.drawImage(background, 0, 0, null);
    
        // Współczynnik skalowania (np. zmniejszenie obrazka o 30%)
        double scale = 0.3;
        int scaledWidth, scaledHeight;
    
        // Automatyczne generowanie pozycji Y
        int startY = 50;
        int endY = 350;
        int stepY = (endY - startY) / (allHorses.size() - 1);
    
        // Rysowanie każdego konia
        for (int i = 0; i < allHorses.size(); i++) {
            Horse horse = allHorses.get(i);
            int x = (int) (horse.getPosition() * (width / (double) trackLength)); // Przeskalowanie pozycji X
            int y = startY + i * stepY; // Automatycznie obliczone Y
            BufferedImage horseImage = horsesImages[horse.getImageNumber()-1];
    
            // Skalowanie rozmiaru konia
            scaledWidth = (int) (horseImage.getWidth() * scale);
            scaledHeight = (int) (horseImage.getHeight() * scale);
            Image scaledHorse = horseImage.getScaledInstance(scaledWidth, scaledHeight, Image.SCALE_SMOOTH);
    
            if (horse.isFallen()) {
                // Obracanie obrazu do góry nogami dla przewróconych koni
                AffineTransform transform = AffineTransform.getScaleInstance(1, -1);
                transform.translate(0, -scaledHeight);
                AffineTransform translate = AffineTransform.getTranslateInstance(x, y + scaledHeight / 4);
                translate.concatenate(transform);
                g.drawImage(scaledHorse, translate, null);
            } else {
                // Normalne rysowanie konia
                g.drawImage(scaledHorse, x, y, null);
            }
        }
    
        g.dispose();
    
        // Kopiowanie wygenerowanego obrazu do schowka
        setClipboardImage(result);
    }

    /**
     * Kopiuje obraz do schowka systemowego.
     *
     * @param image Obraz do skopiowania.
     */
    private static void setClipboardImage(final BufferedImage image) {
        TransferableImage transferable = new TransferableImage(image);
        Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
        clipboard.setContents(transferable, null);
    }

    /**
     * Klasa pomocnicza dla Transferable do obsługi obrazu.
     */
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