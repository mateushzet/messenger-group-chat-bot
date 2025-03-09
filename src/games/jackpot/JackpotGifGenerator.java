package games.jackpot;

import com.madgag.gif.fmsware.AnimatedGifEncoder;

import utils.GradientGenerator;
import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;

public class JackpotGifGenerator {
    private static final int WIDTH = 800;
    private static final int HEIGHT = 300;
    private static final int FRAME_COUNT = 121;
    private static final int NAME_SPACING = 270;

    private static Paint gradient;

    public static JackpotResult generateJackpotGif() throws IOException {
        Map<String, Integer> bets = JackpotGameRepository.getJackpotBets();
        List<String> participants = new ArrayList<>(bets.keySet());
    
        if (participants.size()<=1) {
            int minBet = findMinimumBet(bets);
            participants.add("Bot");
            bets.put("Bot", minBet);
        }
    
        Map<String, String> avatarUrls = JackpotGameRepository.getUserAvatars(participants);
    
        avatarUrls.putIfAbsent("Bot", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgMQyeXHo2tzPRatT5CCO9xkei66IqM4Pn2g&s");
    
        
        int totalPot = bets.values().stream().mapToInt(Integer::intValue).sum();
    
        List<String> weightedParticipants = getWeightedParticipants(bets);
        Collections.shuffle(weightedParticipants);

        int winnerIndex = 2;
        String winnerName = weightedParticipants.get(winnerIndex);

        byte[] gifBytes = generateJackpotGif(winnerName, totalPot, weightedParticipants, bets, avatarUrls);
    
        return new JackpotResult(winnerName, totalPot, gifBytes);
    }

    public static byte[] generateJackpotGif(String winnerName, int totalPot, List<String> participants,
                                           Map<String, Integer> bets, Map<String, String> avatarUrls) throws IOException {

        String gradientUserName = participants.get(0).equals("Bot")?participants.get(1):participants.get(0);
        gradient = GradientGenerator.generateGradientFromUsername(gradientUserName, true, WIDTH, HEIGHT);

        Map<String, BufferedImage> avatars = loadAvatarsFromUrls(avatarUrls);

        List<BufferedImage> frames = generateFrames(avatars, winnerName, totalPot, bets, participants);

        return createGif(frames);
    }

    private static Map<String, BufferedImage> loadAvatarsFromUrls(Map<String, String> avatarUrls) throws IOException {
        Map<String, BufferedImage> avatars = new HashMap<>();
        for (Map.Entry<String, String> entry : avatarUrls.entrySet()) {
            String username = entry.getKey();
            String avatarUrl = entry.getValue();
            try {
                URL url = new URL(avatarUrl);
                BufferedImage avatar = ImageIO.read(url);
                avatars.put(username, avatar);
            } catch (IOException e) {
                File defaultAvatarFile = new File("src/resources/user_avatars/default.png");
                if (defaultAvatarFile.exists()) {
                    BufferedImage defaultAvatar = ImageIO.read(defaultAvatarFile);
                    avatars.put(username, defaultAvatar);
                }
            }
        }
        return avatars;
    }

private static List<BufferedImage> generateFrames(Map<String, BufferedImage> avatars, String winnerName, int totalPot, Map<String, Integer> bets, List<String> participants) {
    List<BufferedImage> frames = new ArrayList<>();

    double speed = 8000;
    double deceleration = 0.97;
    int randomStopOffset = new Random().nextInt(120) - 60;
    int endSpeed = new Random().nextInt(301);

    for (int i = 0; i < FRAME_COUNT; i++) {
        boolean finalFrames = i >= 120;
        if (finalFrames) {
            for (int j = 0; j < 400; j++) {
                frames.add(generateFrame(participants, avatars, (int) speed, randomStopOffset, winnerName, totalPot, finalFrames, bets));
            }
        }
        frames.add(generateFrame(participants, avatars, (int) speed, randomStopOffset, winnerName, totalPot, finalFrames, bets));
        speed *= deceleration;
        if (speed <= endSpeed) {
            speed = endSpeed;
        }
    }

    return frames;
}

private static BufferedImage generateFrame(List<String> weightedParticipants, Map<String, BufferedImage> avatars, int speed, int randomStopOffset,
                                          String winnerName, int totalPot, boolean finalFrames, Map<String, Integer> bets) {
    BufferedImage image = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
    Graphics2D g = image.createGraphics();

    g.setPaint(gradient);
    g.fillRect(0, 0, WIDTH, HEIGHT);

    int totalParticipants = weightedParticipants.size();
    if (totalParticipants == 0) {
        g.dispose();
        return image;
    }

    int offset = -(speed) % (totalParticipants * NAME_SPACING) + randomStopOffset;

    for (int i = 0; i < totalParticipants * 2; i++) {
        int index = i % totalParticipants;
        String participant = weightedParticipants.get(index);
        int x = offset + i * NAME_SPACING;
        BufferedImage avatar = avatars.get(participant);
        if (avatar != null) {
            g.drawImage(avatar, x, 50, 100, 100, null);
        }
        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 16));
        g.drawString(participant, x + 10, 170);
        g.drawString("$" + bets.get(participant), x + 10, 190);
    }

    g.setColor(Color.YELLOW);
    g.setStroke(new BasicStroke(3));
    g.drawRect(400, 0, 2, 300);

    if (finalFrames) {
        GradientPaint gradient = new GradientPaint(100, 100, new Color(0, 0, 0, 200), 700, 200, new Color(50, 50, 50, 200));
        g.setPaint(gradient);
        g.fillRoundRect(100, 100, 600, 150, 20, 20);

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 24));

        g.setColor(new Color(0, 0, 0, 150));
        g.drawString("Winner: " + winnerName, 152, 152);
        g.drawString("Prize: $" + totalPot, 152, 182);

        g.setColor(Color.WHITE);
        g.drawString("Winner: " + winnerName, 150, 150);
        g.drawString("Prize: $" + totalPot, 150, 180);

        g.setColor(Color.ORANGE);
        g.fillOval(110, 130, 20, 20);
        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 16));
        g.drawString("$", 115, 145);

        g.setColor(new Color(255, 255, 255, 100));
        g.setStroke(new BasicStroke(2));
        g.drawRoundRect(100, 100, 600, 150, 20, 20);
    }

    g.dispose();
    return image;
}

    private static byte[] createGif(List<BufferedImage> frames) {
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream()) {
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(byteArrayOutputStream);
            encoder.setDelay(50);
            encoder.setRepeat(0);
            encoder.setQuality(10);

            int frameSkip = 2;
            for (int i = 0; i < frames.size(); i += frameSkip) {
                BufferedImage frame = frames.get(i);
                BufferedImage resizedFrame = resizeImage(frame, WIDTH / 2, HEIGHT / 2);
                encoder.addFrame(resizedFrame);
            }

            encoder.finish();
            return byteArrayOutputStream.toByteArray();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    private static BufferedImage resizeImage(BufferedImage originalImage, int targetWidth, int targetHeight) {
        BufferedImage resizedImage = new BufferedImage(targetWidth, targetHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = resizedImage.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        g.drawImage(originalImage, 0, 0, targetWidth, targetHeight, null);
        g.dispose();
        return resizedImage;
    }

    private static int findMinimumBet(Map<String, Integer> bets) {
        if (bets.isEmpty()) {
            return 10;
        }
        return Collections.min(bets.values());
    }

    private static List<String> getWeightedParticipants(Map<String, Integer> bets) {
        List<String> weightedParticipants = new ArrayList<>();
        int minBet = findMinimumBet(bets);
    
        for (Map.Entry<String, Integer> entry : bets.entrySet()) {
            String username = entry.getKey();
            int betAmount = entry.getValue();
            int weight = betAmount / minBet;
    
            for (int i = 0; i < weight; i++) {
                weightedParticipants.add(username);
            }
        }

        while(weightedParticipants.size() <= 2){
            weightedParticipants.addAll(weightedParticipants);
        }

        return weightedParticipants;
    }

    public static byte[] generatePresentationGif(List<String> participants, Map<String, Integer> bets, Map<String, String> avatarUrls) throws IOException {
        gradient = GradientGenerator.generateGradientFromUsername(participants.get(0), true, WIDTH, HEIGHT);
    
        Map<String, BufferedImage> avatars = loadAvatarsFromUrls(avatarUrls);
    
        List<BufferedImage> frames = generatePresentationFrames(avatars, participants, bets);
    
        return createGif(frames);
    }

    private static List<BufferedImage> generatePresentationFrames(Map<String, BufferedImage> avatars, List<String> weightedParticipants, Map<String, Integer> bets) {
        List<BufferedImage> frames = new ArrayList<>();
    
        String startTime = printTimeAfter10Minutes();
        int speed = 7;
        int totalParticipants = weightedParticipants.size();
    
        for (int i = 0; i < 230; i++) {
            int offset = -(i * speed) % (totalParticipants * NAME_SPACING);
            frames.add(generatePresentationFrame(weightedParticipants, avatars, offset, bets, startTime));
        }
    
        return frames;
    }

    private static BufferedImage generatePresentationFrame(List<String> weightedParticipants, Map<String, BufferedImage> avatars, int offset, Map<String, Integer> bets, String startTime) {
        BufferedImage image = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
        int totalPot = bets.values().stream().mapToInt(Integer::intValue).sum();

        g.setPaint(gradient);
        g.fillRect(0, 0, WIDTH, HEIGHT);
    
        int totalParticipants = weightedParticipants.size();
        if (totalParticipants == 0) {
            g.dispose();
            return image;
        }
    
        for (int i = 0; i < totalParticipants * 2; i++) {
            int index = i % totalParticipants;
            String participant = weightedParticipants.get(index);
            int x = offset + i * NAME_SPACING;
            BufferedImage avatar = avatars.get(participant);
            if (avatar != null) {
                g.drawImage(avatar, x, 50, 100, 100, null);
            }
            g.setColor(Color.WHITE);
            g.setFont(new Font("Arial", Font.BOLD, 16));
            g.drawString(participant, x + 10, 170);
            g.drawString("$" + bets.get(participant), x + 10, 190);
        }
    
        g.setColor(Color.YELLOW);
        g.setStroke(new BasicStroke(3));
        g.drawRect(400, 0, 2, 300);
    
        GradientPaint gradient = new GradientPaint(100, 100, new Color(0, 0, 0, 200), 700, 200, new Color(50, 50, 50, 200));
        g.setPaint(gradient);
        g.fillRoundRect(-10, 230, 300, 150, 20, 20);

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 24));

        g.drawString("Starting: " + startTime, 22, 262);
        g.drawString("Prize: $" + totalPot, 22, 292);

        g.setColor(new Color(255, 255, 255, 100));
        g.setStroke(new BasicStroke(2));
        g.drawRoundRect(-10, 230, 300, 150, 20, 20);

        g.dispose();
        return image;
    }

    public static byte[] generateParticipantPresentationGif() throws IOException {
        Map<String, Integer> bets = JackpotGameRepository.getJackpotBets();
        List<String> participants = new ArrayList<>(bets.keySet());
     
        Map<String, String> avatarUrls = JackpotGameRepository.getUserAvatars(participants);
        avatarUrls.putIfAbsent("Bot", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgMQyeXHo2tzPRatT5CCO9xkei66IqM4Pn2g&s");
    
        List<String> weightedParticipants = getWeightedParticipants(bets);
        Collections.shuffle(weightedParticipants);

        return generatePresentationGif(weightedParticipants, bets, avatarUrls);
    }

     public static String printTimeAfter10Minutes() {
        java.sql.Timestamp oldestTimestamp = JackpotGameRepository.getOldestTimestamp();
        if (oldestTimestamp != null) {
            LocalDateTime oldestTime = oldestTimestamp.toLocalDateTime();
            LocalDateTime timeAfter10Minutes = oldestTime.plusMinutes(10);
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("HH:mm");
            String formattedTime = timeAfter10Minutes.format(formatter);

            return formattedTime;
        } else {
            return "";
        }
    }
    
}