package service;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import model.CommandContext;

public class AskCommandService {
    private static final String API_KEY = "key";
    private static final String API_URL = "https://api.aimlapi.com/v1/chat/completions";

    public static void handleAskCommand(CommandContext context) {

        String text = String.join(" ", context.getArguments());

        try {
            String aiResponse = sendRequestToAI(text);
            
            MessageService.sendMessage(aiResponse);
        } catch (Exception e) {
            
            e.printStackTrace();
            MessageService.sendMessage("ERROR");
        }
    }

    private static String sendRequestToAI(String inputText) throws Exception {

        ObjectMapper objectMapper = new ObjectMapper();


        ObjectNode requestBody = objectMapper.createObjectNode();
        requestBody.put("model", "gpt-4o");

        ArrayNode messages = objectMapper.createArrayNode();
        messages.add(objectMapper.createObjectNode()
                .put("role", "system")
                .put("content", "You are an AI assistant who knows everything."));
        messages.add(objectMapper.createObjectNode()
                .put("role", "user")
                .put("content", inputText));

        requestBody.set("messages", messages);

        URL url = new URL(API_URL);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();

        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Authorization", "Bearer " + API_KEY);
        connection.setDoOutput(true);

        try (OutputStream os = connection.getOutputStream()) {
            byte[] input = objectMapper.writeValueAsBytes(requestBody);
            os.write(input, 0, input.length);
        }

    int responseCode = connection.getResponseCode();
    if (responseCode != 200 && responseCode != 201) {
        System.out.println("Request Body: " + objectMapper.writeValueAsString(requestBody));

        InputStream errorStream = connection.getErrorStream();
        if (errorStream != null) {
            BufferedReader errorReader = new BufferedReader(new InputStreamReader(errorStream, "UTF-8"));
            StringBuilder errorResponse = new StringBuilder();
            String errorLine;
            while ((errorLine = errorReader.readLine()) != null) {
                errorResponse.append(errorLine);
            }
            errorReader.close();
            System.out.println("Error Response: " + errorResponse.toString());
        }

        throw new RuntimeException("HTTP Error Code: " + responseCode);
    }

        BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream(), "UTF-8"));

        String inputLine;
        StringBuilder response = new StringBuilder();

        while ((inputLine = in.readLine()) != null) {
            response.append(inputLine);
        }
        in.close();

        ObjectNode jsonResponse = objectMapper.readValue(response.toString(), ObjectNode.class);
        String aiMessage = jsonResponse.get("choices")
                                     .get(0)
                                     .get("message")
                                     .get("content")
                                     .asText();

        return aiMessage;
    }
}