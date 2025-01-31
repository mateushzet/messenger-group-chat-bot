package utils;

import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
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
        BufferedImage image = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();

        Paint gradient = GradientGenerator.generateGradientFromUsername(playerName, false, imageWidth, imageHeight);
        
        g.setPaint(gradient);
        g.fillRect(0, 0, imageWidth, imageHeight);

        g.setFont(new Font("Arial", Font.BOLD, 24));
        g.setColor(Color.BLACK);
        g.drawString("Stats: " + viewName, 20, 40);

        String[] headers = data.get(0);
        int yPosition = 80;
        
        g.setFont(new Font("Arial", Font.BOLD, 18));
        for (int i = 0; i < headers.length; i++) {
            String[] words = headers[i].split("_");
            int headerY = yPosition;
            
            for (String word : words) {
                g.drawString(word, 20 + (i * columnWidth), headerY);
                headerY += 20;
            }
        }
        
        yPosition += rowHeight + 50;

        g.setFont(new Font("Arial", Font.PLAIN, 16));
        for (int i = 1; i < data.size(); i++) {
            String[] row = data.get(i);
            for (int j = 0; j < row.length; j++) {
                String value = row[j] != null ? row[j] : "N/A";
                g.drawString(value, 20 + (j * 200), yPosition);
            }
            yPosition += rowHeight;
        }

        g.dispose();
        saveImageToClipboard(image);
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

    private static void saveImageToClipboard(BufferedImage image) {
        TransferableImage transferable = new TransferableImage(image);
        Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
        clipboard.setContents(transferable, null);
        System.out.println("Image saved to clipboard.");
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