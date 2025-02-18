package utils;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class BitcoinPriceChecker {

    public static double getBitcoinPrice() {
        try {
            String url = "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD";
            
            HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
            connection.setRequestMethod("GET");
            
            int responseCode = connection.getResponseCode();
            if (responseCode == HttpURLConnection.HTTP_OK) {
                BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
                String inputLine;
                StringBuilder response = new StringBuilder();

                while ((inputLine = in.readLine()) != null) {
                    response.append(inputLine);
                }
                in.close();

                String jsonResponse = response.toString();

                String priceString = jsonResponse.split(":")[1].replace("}", "").trim();
                double price = Double.parseDouble(priceString);
                return price;
            } else {
                System.err.println("getBitcoinPrice(): " + responseCode);
                return -1;
            }
        } catch (Exception e) {
            e.printStackTrace();
            return -1;
        }
    }
}