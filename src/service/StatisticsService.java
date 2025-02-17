package service;

import model.CommandContext;
import utils.StatisticsImageGenerator;
import java.util.HashMap;
import java.util.Map;

public class StatisticsService {
    private static final Map<String, String> STATISTICS_VIEWS_MAP = new HashMap<>();

    static {
        STATISTICS_VIEWS_MAP.put("colors", "Colors_statistic_view");
        STATISTICS_VIEWS_MAP.put("games", "Games_statistics_view");
        STATISTICS_VIEWS_MAP.put("global", "Global_statistics_view");
        STATISTICS_VIEWS_MAP.put("lotto", "Lotto_statistics_view");
        STATISTICS_VIEWS_MAP.put("main", "Main_global_statistics_view");
        STATISTICS_VIEWS_MAP.put("mines", "Mines_statistic_view");
        STATISTICS_VIEWS_MAP.put("race", "Race_statistic_view");
        STATISTICS_VIEWS_MAP.put("roulette", "Roulette_statistic_view");
        STATISTICS_VIEWS_MAP.put("slots", "Slots_statistic_view");
        STATISTICS_VIEWS_MAP.put("blackjack", "Blackjack_statistic_view");
        STATISTICS_VIEWS_MAP.put("case", "Case_statistic_view");
        STATISTICS_VIEWS_MAP.put("case", "Case_statistic_view");
    }

    public static void handleStatsCommand(CommandContext context) {
        String userName = context.getUserName();
        String statisticsType = context.getFirstArgument().trim().toLowerCase();

        String viewName = STATISTICS_VIEWS_MAP.get(statisticsType);

        if (statisticsType == null || viewName == null) {
            sendAvailableViewsMessage();
            return;
        }

        StatisticsImageGenerator.generateViewImage(viewName, userName);

        MessageService.sendMessageFromClipboard(true);
    }

    private static void sendAvailableViewsMessage() {
        StringBuilder message = new StringBuilder("Available statistics types: ");
        for (String key : STATISTICS_VIEWS_MAP.keySet()) {
            message.append(key).append(", ");
        }
        message.delete(message.length() - 2, message.length());
        MessageService.sendMessage(message.toString());
    }
}
