package utils;
import java.awt.*;
import java.awt.geom.Arc2D;
import java.awt.image.BufferedImage;
import java.awt.datatransfer.*;
import java.io.IOException;

public class ColorsImageGenerator {

    public static void generateColorsImage(int winAmount, String userName, int currentBalance, int shift){

        int[] colorOrder = {3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2};

        colorOrder = rotateArray(colorOrder, shift);
                
                        Color navy = new Color(39, 38, 44);
                        Color yellow = new Color(252, 194, 120);
                        Color blue = new Color(72, 179, 221);
                        Color red = new Color(197, 52, 81);
                        Color gray  = new Color(90, 90, 90);
                
                        int width = 600;
                        int height = 600;
                        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
                        Graphics2D g = image.createGraphics();
                
                        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                
                        g.setColor(navy);
                        g.fillRect(0, 0, width, height);
                
                        int centerX = width / 2;
                        int centerY = height / 2;
                        int radius = 250;
                
                        Color[] colors = {gray, red, blue, yellow};
                
                        int totalSegments = colorOrder.length;
                        double anglePerSegment = 360.0 / totalSegments;
                
                        double startAngle = 0;
                        for (int colorIndex : colorOrder) {
                            g.setColor(colors[colorIndex]);
                            Arc2D.Double arc = new Arc2D.Double(
                                centerX - radius, centerY - radius,
                                radius * 2, radius * 2,
                                startAngle, anglePerSegment,
                                Arc2D.PIE
                            );
                            g.fill(arc);
                        
                            g.setColor(navy);
                            g.setStroke(new BasicStroke(4));
                            g.draw(arc);
                        
                            startAngle += anglePerSegment;
                        }
                
                        g.setColor(navy);
                        g.fillOval(centerX - radius + 11, centerY - radius + 11, 480 , 480);
                
                
                        
                        double arrowX = 300;
                        double arrowY = 500;
                
                        int arrowWidth = 20;
                        int arrowHeight = 30;
                        int[] xPoints = {
                            (int) arrowX,
                            (int) (arrowX - arrowWidth / 2),
                            (int) (arrowX + arrowWidth / 2)
                        };
                        int[] yPoints = {
                            (int) (arrowY + arrowHeight),
                            (int) arrowY,
                            (int) arrowY 
                        };
                
                        g.setColor(Color.WHITE);
                        g.fillPolygon(xPoints, yPoints, 3);
                
                        g.setFont(new Font("Arial", Font.BOLD, 40));
                        g.setColor(red);
                
                        String winText = winAmount > 0 ? "WIN ":"LOSE ";
                        winText += winAmount;
                        String userText = userName;
                        String balanceText = "Balance: " + currentBalance;
                

                        FontMetrics metrics = g.getFontMetrics();
                        int textX;
                        int textY = centerY - 70;
                
                        textX = centerX - metrics.stringWidth(winText) / 2;
                        g.drawString(winText, textX, textY);
                
                        textY += 50;
                        textX = centerX - metrics.stringWidth(userText) / 2;
                        g.drawString(userText, textX, textY);
                
                        textY += 50;
                        textX = centerX - metrics.stringWidth(balanceText) / 2;
                        g.drawString(balanceText, textX, textY);
                
                        g.dispose();
                
                        setClipboardImage(image);
                        System.out.println("Obraz skopiowany do schowka.");
                    }
                
                    public static void setClipboardImage(final BufferedImage image) {
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
                
            public static int[] rotateArray(int[] array, int shift) {
                int length = array.length;
                int[] rotated = new int[length];
                for (int i = 0; i < length; i++) {
                    rotated[(i + shift) % length] = array[i];
                }
                return rotated;
            }
        
}