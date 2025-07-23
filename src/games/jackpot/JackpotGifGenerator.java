package games.jackpot;

import com.madgag.gif.fmsware.AnimatedGifEncoder;
import repository.UserRepository;
import utils.GradientGenerator;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;

public class JackpotGifGenerator {
    private static final int WIDTH = 800;
    private static final int HEIGHT = 300;
    private static final int NAME_SPACING = 270;
    private static final int FRAME_COUNT = 121;
    private static Paint gradient;
    private static final Map<String, BufferedImage> avatarCache = new HashMap<>();

    public static JackpotResult generateJackpotGif() throws IOException {
        Map<String, Integer> bets = JackpotGameRepository.getJackpotBets();
        List<String> participants = new ArrayList<>(bets.keySet());

        if (participants.size() <= 1) {
            int minBet = findMinimumBet(bets);
            participants.add("Bot");
            bets.put("Bot", minBet);
        }

        Map<String, String> avatarUrls = UserRepository.getUserAvatars(participants);
        avatarUrls.putIfAbsent("Bot", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgMQyeXHo2tzPRatT5CCO9xkei66IqM4Pn2g&s");

        int totalPot = bets.values().stream().mapToInt(Integer::intValue).sum();
        List<String> weightedParticipants = getWeightedParticipants(bets);
        Collections.shuffle(weightedParticipants);

        int winnerIndex = 2;
        String winnerName = weightedParticipants.get(winnerIndex);

        gradient = GradientGenerator.generateGradientFromUsername(participants.get(0), true, WIDTH, HEIGHT);
        Map<String, BufferedImage> avatars = loadAvatarsFromUrls(avatarUrls);

        int winnerNewBalance;

        if(participants.get(participants.size()-1).equals("Bot")){
            winnerNewBalance = UserRepository.getCurrentUserBalance(participants.get(0), false) + totalPot;
        } else {
            winnerNewBalance = UserRepository.getCurrentUserBalance(winnerName, false) + totalPot;
        }

        List<BufferedImage> frames = generateJackpotFrames(weightedParticipants, avatars, winnerName, totalPot, bets, winnerNewBalance);
        byte[] gifBytes = createGif(frames);

        return new JackpotResult(winnerName, totalPot, gifBytes);
    }

    public static byte[] generateParticipantPresentationGif() throws IOException {
        Map<String, Integer> bets = JackpotGameRepository.getJackpotBets();
        List<String> participants = new ArrayList<>(bets.keySet());

        Map<String, String> avatarUrls = UserRepository.getUserAvatars(participants);
        avatarUrls.putIfAbsent("Bot", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgMQyeXHo2tzPRatT5CCO9xkei66IqM4Pn2g&s");

        List<String> weightedParticipants = getWeightedParticipants(bets);
        Collections.shuffle(weightedParticipants);

        gradient = GradientGenerator.generateGradientFromUsername(weightedParticipants.get(0), true, WIDTH, HEIGHT);
        Map<String, BufferedImage> avatars = loadAvatarsFromUrls(avatarUrls);

        List<BufferedImage> frames = generatePresentationFrames(weightedParticipants, avatars, bets);
        return createGif(frames);
    }

    private static Map<String, BufferedImage> loadAvatarsFromUrls(Map<String, String> avatarUrls) throws IOException {
        for (Map.Entry<String, String> entry : avatarUrls.entrySet()) {
            String username = entry.getKey();
            if (avatarCache.containsKey(username)) continue;

            try {
                URL url = new URL(entry.getValue());
                BufferedImage avatar = ImageIO.read(url);
               avatarCache.put(username, avatar);
            } catch (IOException e) {
                File defaultAvatarFile = new File("src/resources/user_avatars/default.png");
                if (defaultAvatarFile.exists()) {
                    BufferedImage defaultAvatar = ImageIO.read(defaultAvatarFile);
                    avatarCache.put(username, defaultAvatar);
                }
            }
        }
        return avatarCache;
    }

    private static List<BufferedImage> generateJackpotFrames(List<String> participants, Map<String, BufferedImage> avatars, String winnerName, int totalPot, Map<String, Integer> bets, int winnerNewBalance) {
        List<BufferedImage> frames = new ArrayList<>();

        double speed = 8000;
        double deceleration = 0.97;
        int randomStopOffset = new Random().nextInt(60) - 30;
        int endSpeed = new Random().nextInt(301);

        BufferedImage finalFrame = null;

        for (int i = 0; i < FRAME_COUNT; i++) {
            boolean finalFrames = i >= FRAME_COUNT - 1;
            BufferedImage frame = generateFrame(participants, avatars, (int) speed, randomStopOffset, winnerName, totalPot, finalFrames, bets, winnerNewBalance);
            frames.add(frame);
            speed *= deceleration;
            if (speed <= endSpeed) speed = endSpeed;
            if (finalFrames && finalFrame == null) finalFrame = frame;
        }

        for (int i = 0; i < 100; i++) frames.add(finalFrame);
        return frames;
    }

    private static List<BufferedImage> generatePresentationFrames(List<String> participants, Map<String, BufferedImage> avatars, Map<String, Integer> bets) {
        List<BufferedImage> frames = new ArrayList<>();
        int speed = 6;
        String startTime = getStartTime();

        for (int i = 0; i < 225; i++) {
            int offset = -(i * speed) % (participants.size() * NAME_SPACING);
            frames.add(generatePresentationFrame(participants, avatars, offset, bets, startTime));
        }
        return frames;
    }

    private static BufferedImage generateFrame(List<String> participants, Map<String, BufferedImage> avatars, int speed, int offset, String winnerName, int totalPot, boolean finalFrame, Map<String, Integer> bets, int winnerNewBalance) {
        BufferedImage img = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setPaint(gradient);
        g.fillRect(0, 0, WIDTH, HEIGHT);

        int total = participants.size();
        int position = -(speed) % (total * NAME_SPACING) + offset;

        for (int i = 0; i < total * 2; i++) {
            String name = participants.get(i % total);
            int x = position + i * NAME_SPACING;
            BufferedImage avatar = avatars.get(name);
            if (avatar != null) g.drawImage(avatar, x, 50, 100, 100, null);
            g.setColor(Color.WHITE);
            g.setFont(new Font("Arial", Font.BOLD, 16));
            g.drawString(name, x + 10, 170);
            g.drawString("$" + bets.get(name), x + 10, 190);
        }

        g.setColor(Color.YELLOW);
        g.setStroke(new BasicStroke(3));
        g.drawRect(400, 0, 2, HEIGHT);

        if (finalFrame) {
            GradientPaint panel = new GradientPaint(100, 100, new Color(0, 0, 0, 200), 700, 200, new Color(50, 50, 50, 200));
            g.setPaint(panel);
            g.fillRoundRect(100, 100, 600, 150, 20, 20);

            g.setColor(Color.WHITE);
            g.setFont(new Font("Arial", Font.BOLD, 24));
            g.drawString("Winner: " + winnerName, 150, 150);
            g.drawString("Prize: $" + totalPot, 150, 180);
            if(winnerName.equals("Bot")){
                g.drawString("Your balance: $" + winnerNewBalance, 150, 210);
            } else {
                g.drawString("Balance: $" + winnerNewBalance, 150, 210);
            }
            
        }

        g.dispose();
        return img;
    }

    private static BufferedImage generatePresentationFrame(List<String> participants, Map<String, BufferedImage> avatars, int offset, Map<String, Integer> bets, String startTime) {
        BufferedImage img = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setPaint(gradient);
        g.fillRect(0, 0, WIDTH, HEIGHT);

        int total = participants.size();
        for (int i = 0; i < total * 2; i++) {
            String name = participants.get(i % total);
            int x = offset + i * NAME_SPACING;
            BufferedImage avatar = avatars.get(name);
            if (avatar != null) g.drawImage(avatar, x, 50, 100, 100, null);
            g.setColor(Color.WHITE);
            g.setFont(new Font("Arial", Font.BOLD, 16));
            g.drawString(name, x, 170);
            g.setFont(new Font("Arial", Font.BOLD, 24));
            g.drawString("$" + bets.get(name), x, 200);
        }

        GradientPaint panel = new GradientPaint(100, 100, new Color(0, 0, 0, 200), 700, 200, new Color(50, 50, 50, 200));
        g.setPaint(panel);
        g.fillRoundRect(-10, 230, 300, 150, 20, 20);

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 24));
        g.drawString("Starting: " + startTime, 22, 262);
        g.drawString("Prize: $" + bets.values().stream().mapToInt(Integer::intValue).sum(), 22, 292);

        g.dispose();
        return img;
    }

    private static byte[] createGif(List<BufferedImage> frames) {
        try (ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(out);
            encoder.setDelay(50);
            encoder.setRepeat(0);
            encoder.setQuality(10);
            for (int i = 0; i < frames.size(); i += 2) {
                BufferedImage frame = resizeImage(frames.get(i), WIDTH / 2, HEIGHT / 2);
                encoder.addFrame(frame);
            }
            encoder.finish();
            return out.toByteArray();
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    private static BufferedImage resizeImage(BufferedImage img, int w, int h) {
        BufferedImage resized = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = resized.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        g.drawImage(img, 0, 0, w, h, null);
        g.dispose();
        return resized;
    }

    private static int findMinimumBet(Map<String, Integer> bets) {
        return bets.isEmpty() ? 10 : Collections.min(bets.values());
    }

    private static List<String> getWeightedParticipants(Map<String, Integer> bets) {
        List<String> weighted = new ArrayList<>();
        int min = findMinimumBet(bets);
        for (Map.Entry<String, Integer> e : bets.entrySet()) {
            int weight = Math.max(1, e.getValue() / min);
            for (int i = 0; i < weight; i++) weighted.add(e.getKey());
        }
        while (weighted.size() < 3) weighted.addAll(weighted);
        return weighted;
    }

    private static String getStartTime() {
        Timestamp ts = JackpotGameRepository.getOldestTimestamp();
        if (ts == null) return "";
        LocalDateTime time = ts.toLocalDateTime().plusMinutes(10);
        return time.format(DateTimeFormatter.ofPattern("HH:mm"));
    }
}
 
