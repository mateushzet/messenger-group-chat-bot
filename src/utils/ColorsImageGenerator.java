package utils;
import java.awt.*;
import java.awt.geom.Arc2D;
import java.awt.image.BufferedImage;

import java.util.Queue;

public class ColorsImageGenerator {

    public static void generateColorsImage(int winAmount, String userName, int currentBalance, int shift, int betAmount, Queue<Integer> history){

        int[] colorOrder = {3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2};

        colorOrder = rotateArray(colorOrder, shift);
                
        Color yellow = new Color(252, 194, 120);
        Color blue = new Color(72, 179, 221);
        Color red = new Color(197, 52, 81);
        Color gray  = new Color(90, 90, 90);

        int width = 600;
        int height = 600;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        Paint gradient = GradientGenerator.generateGradientFromUsername(userName, false, width, height);
        
        g.setPaint(gradient);
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
        
            g.setPaint(gradient);
            g.setStroke(new BasicStroke(4));
            g.draw(arc);
        
            startAngle += anglePerSegment;
        }

        g.setPaint(gradient);
        g.fillOval(centerX - radius + 30, centerY - radius + 15, 440 , 440);


        
        double arrowX = 300;
        double arrowY = 490;

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

        float alpha = 0.4f;
        g.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, alpha));
        
        g.setColor(Color.BLACK);
        g.fillRoundRect(140, 155, 320, 260, 30, 30);
        
        g.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, 1.0f));

        g.setFont(new Font("Arial", Font.BOLD, 30));
        g.setColor(Color.WHITE);

        String winText = winAmount > 0 ? "WIN ":"LOSE ";
        winText += winAmount;
        String userText = userName;
        String balanceText = "Total: " + currentBalance;
        String betText = "Bet: " + Integer.toString(betAmount) ;

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

        textY += 50;
        textX = centerX - metrics.stringWidth(betText) / 2;
        g.drawString(betText, textX, textY);

        drawHistory(g, history, width, height);

        g.dispose();

        ImageUtils.setClipboardImage(image);
    }

    private static void drawHistory(Graphics2D g, Queue<Integer> colorHistory, int width, int height) {

        int margin = 20;
        int historyHeight = 50;
        int historyWidth = width - 2 * margin;
    

        int numColors = colorHistory.size();
        int barWidth = historyWidth / (16);
        int spaceBetweenBars = 5;
        
        int x = width; 
    
      
        g.setColor(Color.LIGHT_GRAY);
        g.setStroke(new BasicStroke(4));
        g.drawRect(x - barWidth, height - historyHeight +  2 * margin, barWidth - 6, (historyHeight - 2 * margin)-6);
    
        Integer[] reversedHistory = colorHistory.toArray(new Integer[0]);

        for (int i = reversedHistory.length - 1; i >= 0; i--) {
            int colorIndex = reversedHistory[i];
            Color color = getColorFromIndex(colorIndex);
            g.setColor(color);
            g.fillRect(x - barWidth, height - historyHeight + 2 * margin, barWidth - spaceBetweenBars, historyHeight - 2 * margin - 5);
            x -= (barWidth + spaceBetweenBars);
        }

            for (int i = 0; i < 17 - numColors; i++) {
                g.setColor(Color.BLACK);
                g.fillRect(x - barWidth - spaceBetweenBars, height - historyHeight + 2 * margin, barWidth, (historyHeight - 2 * margin)-5);
                x -= (barWidth + spaceBetweenBars);
            }
            
    }

    private static Color getColorFromIndex(int colorIndex) {
        switch (colorIndex) {
            case 0: return new Color(90, 90, 90); 
            case 1: return new Color(197, 52, 81);
            case 2: return new Color(72, 179, 221);
            case 3: return new Color(252, 194, 120);
            default: return Color.BLACK;
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