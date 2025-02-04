package utils;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import database.DatabaseConnectionManager;

public class StatisticsImageGenerator {

    public static void generateViewImage(String viewName, String playerName) {
        List<String[]> data = fetchViewData(viewName);
        if (data.isEmpty()) {
            System.out.println("No data found: " + viewName);
            return;
        }
    
        int rowHeight = 40;
        int columnCount = data.get(0).length;
        int columnWidth = 200;
        int imageWidth = 40 + columnCount * columnWidth;
        int imageHeight = 100 + data.size() * rowHeight;
        BufferedImage image = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
    
        Paint gradient = GradientGenerator.generateGradientFromUsername(playerName, false, imageWidth, imageHeight);
        g.setPaint(gradient);
        g.fillRect(0, 0, imageWidth, imageHeight);
    
        g.setFont(new Font("Arial", Font.BOLD, 24));
        g.setColor(Color.BLACK);
        g.drawString("Stats: " + viewName, 20, 40);
    
        String[] headers = data.get(0);
        int yPosition = 80;
    
        g.setColor(new Color(200, 200, 200)); 
        g.fillRect(20, yPosition - 30, imageWidth - 40, rowHeight); 
    
        g.setColor(Color.BLACK);
        g.drawRect(19, 80 - 30, imageWidth - 39, yPosition + (data.size() * rowHeight) - 80);
    
        g.setFont(new Font("Arial", Font.BOLD, 17));
        g.setColor(Color.BLACK);
        for (int i = 0; i < headers.length; i++) {
            String header = headers[i].replace('_', ' ');
            int headerX = 20 + (i * columnWidth);
            int textWidth = g.getFontMetrics().stringWidth(header);
    
            if (textWidth > columnWidth - 20) { 
                String[] lines = wrapText(header, columnWidth - 20, g);
                int lineHeight = g.getFontMetrics().getHeight();
                int textY = yPosition - (lineHeight / 2) - 3;
                for (int j = 0; j < lines.length; j++) {
                    g.drawString(lines[j], headerX + (columnWidth - g.getFontMetrics().stringWidth(lines[j])) / 2, textY + (j * lineHeight));
                }
            } else {
                int headerXPosition = headerX + (columnWidth - textWidth) / 2;
                g.drawString(header, headerXPosition, yPosition);
            }
        }
    
        yPosition += rowHeight + 10;
    
        g.setFont(new Font("Arial", Font.PLAIN, 16));
        FontMetrics fontMetrics = g.getFontMetrics();
        for (int i = 1; i < data.size(); i++) {
            String[] row = data.get(i);
    
            g.setColor(Color.WHITE); 
            for (int j = 0; j < row.length; j++) {
                int cellX = 20 + (j * columnWidth);
                int cellY = yPosition + (i - 1) * rowHeight - rowHeight; 
                g.fillRect(cellX, cellY, columnWidth, rowHeight); 
            }
    
            for (int j = 0; j < row.length; j++) {
                String value = row[j] != null ? row[j] : "N/A";
                int cellX = 20 + (j * columnWidth);
                int cellY = yPosition + (i - 1) * rowHeight - rowHeight;
    
                int textWidth = fontMetrics.stringWidth(value);
                int textX = cellX + (columnWidth - textWidth) / 2;
                int textY = cellY + (rowHeight + fontMetrics.getAscent()) / 2 - 1;
    
                g.setColor(Color.BLACK);
                g.drawString(value, textX, textY);
            }
        }
    
        g.setColor(Color.BLACK);
        for (int i = 1; i < columnCount; i++) {
            int x = 20 + i * columnWidth;
            g.drawLine(x, 80 - 30, x, yPosition + ((data.size() - 2) * rowHeight));
        }
    
        for (int i = 0; i < data.size(); i++) {
            g.drawLine(20, yPosition - 40 + i * rowHeight, imageWidth - 20, yPosition - 40 + i * rowHeight);
        }
    
        g.dispose();
        ImageUtils.setClipboardImage(image);
    }
    
    private static List<String[]> fetchViewData(String viewName) {
        List<String[]> data = new ArrayList<>();
        String query = "SELECT * FROM " + viewName;

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query);
             ResultSet resultSet = statement.executeQuery()) {

            ResultSetMetaData metaData = resultSet.getMetaData();
            int columnCount = metaData.getColumnCount();
            String[] headers = new String[columnCount];

            for (int i = 1; i <= columnCount; i++) {
                headers[i - 1] = metaData.getColumnName(i);
            }
            data.add(headers);

            while (resultSet.next()) {
                String[] row = new String[columnCount];
                for (int i = 1; i <= columnCount; i++) {
                    row[i - 1] = resultSet.getString(i);
                }
                data.add(row);
            }
        } catch (SQLException e) {
            System.err.println("Error retrieving data from view: " + viewName);
            e.printStackTrace();
        }
        return data;
    }

    private static String[] wrapText(String text, int maxWidth, Graphics2D g) {
        List<String> lines = new ArrayList<>();
        String[] words = text.split(" ");
        StringBuilder currentLine = new StringBuilder();

        for (String word : words) {
            String testLine = currentLine.length() == 0 ? word : currentLine + " " + word;
            if (g.getFontMetrics().stringWidth(testLine) <= maxWidth) {
                currentLine.append(" ").append(word);
            } else {
                lines.add(currentLine.toString());
                currentLine = new StringBuilder(word);
            }
        }
        if (currentLine.length() > 0) {
            lines.add(currentLine.toString());
        }
        return lines.toArray(new String[0]);
    }

}
