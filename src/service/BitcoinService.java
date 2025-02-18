package service;

import model.CommandContext;
import repository.BitcoinRepository;
import repository.UserRepository;
import utils.BitcoinPriceChecker;

public class BitcoinService {

    public static void handleBitcoinCommand(CommandContext context) {
        String userName = context.getUserName();
        String command = context.getFirstArgument().trim().toLowerCase();
        String amount = context.getSecondArgument();
        Double amountParsed = -1.0;

        try {
            amountParsed = Double.parseDouble(amount);
        } catch (NumberFormatException e) {
        }

        switch (command) {
            case "price":
            if (amountParsed != -1.0) {
                double bitcoinPrice = BitcoinPriceChecker.getBitcoinPrice();
                double totalCost = amountParsed * bitcoinPrice;
                MessageService.sendMessage("Price for " + amountParsed + " BTC: " + totalCost);
            } else {
                MessageService.sendMessage("Bitcoin price: " + BitcoinPriceChecker.getBitcoinPrice());
            }
                break;

            case "buy":
                if( amountParsed == -1.0){
                    MessageService.sendMessage("Invalid amount. Please provide a valid number.");
                    break;
                }
                buyBitcoin(userName, amountParsed);
                break;

            case "sell":
                if( amountParsed == -1.0){
                    MessageService.sendMessage("Invalid amount. Please provide a valid number.");
                    break;
                }
                sellBitcoin(userName, amountParsed);
                break;

            case "balance":
                showBitcoinBalance(userName);
                break;

            default:
                MessageService.sendMessage("Available commands: 'price', 'buy', 'sell', 'balance'.");
                break;
        }
    }

    private static void buyBitcoin(String userName, double quantity) {
        int balance = UserRepository.getCurrentUserBalance(userName, true);
        double bitcoinPrice = BitcoinPriceChecker.getBitcoinPrice();
        int cost = (int) Math.ceil(quantity * bitcoinPrice);

        if (quantity <= 0) {
            MessageService.sendMessage(userName + " BTC amount too small or invalid.");
            return;
        }

        if (cost > balance) {
            MessageService.sendMessage(userName + " Insufficient balance. Bitcoin price for " + quantity + " BTC = " + cost);
            return;
        }

        if (cost <= 0) {
            MessageService.sendMessage(userName + " btc amount too small");
            return;
        }

        UserRepository.updateUserBalance(userName, balance - cost);
        
        double currentBtcBalance = BitcoinRepository.getBitcoinBalance(userName);
        BitcoinRepository.updateBitcoinBalance(userName, currentBtcBalance + quantity);

        MessageService.sendMessage(userName + " Bitcoin purchased successfully ("+bitcoinPrice+"/BTC). New balance: " + (balance - cost));
    }

    private static void sellBitcoin(String userName, double quantity) {
        double currentBtcBalance = BitcoinRepository.getBitcoinBalance(userName);
        
        if (currentBtcBalance < quantity) {
            MessageService.sendMessage(userName + " Insufficient Bitcoin balance. You have " + currentBtcBalance + " BTC.");
            return;
        }

        if (quantity <= 0) {
            MessageService.sendMessage(userName + " BTC amount too small or invalid.");
            return;
        }
        
        int balance = UserRepository.getCurrentUserBalance(userName, true);
        double bitcoinPrice = BitcoinPriceChecker.getBitcoinPrice();
        int cost = (int) Math.floor(quantity * bitcoinPrice);

        if (cost <= 0) {
            MessageService.sendMessage(userName + " BTC amount too small or invalid.");
            return;
        }

        BitcoinRepository.updateBitcoinBalance(userName, currentBtcBalance - quantity);

        UserRepository.updateUserBalance(userName, balance + cost);
        MessageService.sendMessage(userName + " Bitcoin sold successfully ("+bitcoinPrice+"/BTC). New balance: " + (balance + cost));
    }

    private static void showBitcoinBalance(String userName) {
        double btcBalance = BitcoinRepository.getBitcoinBalance(userName);
        MessageService.sendMessage(userName + " your Bitcoin balance: " + btcBalance + " BTC");
    }
}