package service;

import model.CommandContext;
import utils.StatisticsImageGenerator;

public class StatisticsService {
    

     public static void handleStatsCommand(CommandContext context) {
        String userName = context.getUserName();
        String statisticsType = context.getFirstArgument();

        StatisticsImageGenerator.generateViewImage(statisticsType, userName);
        MessageService.sendMessageFromClipboard(true);
     }
}
