package games.balatro;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class HandEvaluator {

    public static int calculateBaseMultiplier(List<String> hand) {
        List<Integer> values = getSortedCardValues(hand);
        Map<Integer, Long> valueCounts = values.stream()
                .collect(Collectors.groupingBy(v -> v, Collectors.counting()));
        Map<Character, Long> suitCounts = hand.stream()
                .map(s -> s.charAt(s.length() - 1))
                .collect(Collectors.groupingBy(s -> s, Collectors.counting()));

        boolean isFlush = suitCounts.size() == 1;
        boolean isStraight = isStraight(values);
        boolean isRoyal = isRoyal(values);

        if (isStraight && isFlush && isRoyal) return 10; // Royal Flush
        if (isStraight && isFlush) return 9;              // Straight Flush
        if (valueCounts.containsValue(4L)) return 8;      // Four of a Kind
        if (valueCounts.containsValue(3L) && valueCounts.containsValue(2L)) return 7; // Full House
        if (isFlush) return 6;                            // Flush
        if (isStraight) return 5;                         // Straight
        if (valueCounts.containsValue(3L)) return 4;      // Three of a Kind
        if (Collections.frequency(new ArrayList<>(valueCounts.values()), 2L) == 2) return 3; // Two Pair
        if (valueCounts.containsValue(2L)) return 2;      // Pair

        return 1; // High Card
    }

    private static boolean isStraight(List<Integer> sortedValues) {
        for (int i = 1; i < sortedValues.size(); i++) {
            if (sortedValues.get(i) - sortedValues.get(i - 1) != 1) {
                return isLowAceStraight(sortedValues);
            }
        }
        return true;
    }

    private static boolean isLowAceStraight(List<Integer> sortedValues) {
        return sortedValues.equals(Arrays.asList(2, 3, 4, 5, 14)); // Ace-low straight
    }

    private static boolean isRoyal(List<Integer> values) {
        return values.equals(Arrays.asList(10, 11, 12, 13, 14));
    }

    private static List<Integer> getSortedCardValues(List<String> hand) {
        return hand.stream()
                .map(HandEvaluator::getCardValue)
                .sorted()
                .collect(Collectors.toList());
    }

    private static int getCardValue(String card) {
        String rank = card.substring(0, card.length() - 1);
        switch (rank) {
            case "A": return 14;
            case "K": return 13;
            case "Q": return 12;
            case "J": return 11;
            case "T": return 10;
            default: return Integer.parseInt(rank);
        }
    }
}

