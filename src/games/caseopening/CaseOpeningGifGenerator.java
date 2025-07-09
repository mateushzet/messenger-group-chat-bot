package games.caseopening;

import com.madgag.gif.fmsware.AnimatedGifEncoder;
import repository.UserAvatarRepository;
import utils.GradientGenerator;
import utils.ImageUtils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.*;
import java.util.List;
import java.util.concurrent.*;

public class CaseOpeningGifGenerator {

    private static final int WIDTH = 800;
    private static final int HEIGHT = 300;
    private static final int OUTPUT_WIDTH = WIDTH / 2;
    private static final int OUTPUT_HEIGHT = HEIGHT / 2;
    private static final int FRAME_COUNT = 60;
    private static final int FINAL_FRAME_REPEAT = 40;
    private static final int SKIN_WIDTH = 256 / 2;
    private static final int SKIN_HEIGHT = 192 / 2;
    private static final int SKIN_SPACING = 270 / 2;
    private static final String SKIN_FOLDER = "src/games/caseopening/skins";
    private static final int FINAL_FRAME_COUNT = 1;

    private static final Map<String, Map<BufferedImage, String>> skinsCache = new ConcurrentHashMap<>();

    private static final List<String> CONDITIONS = Arrays.asList(
        "Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"
    );
    private static final List<String> STATTRAK_STATUSES = Arrays.asList("StatTrak", "No");

    private static final ExecutorService executor = Executors.newFixedThreadPool(
        Runtime.getRuntime().availableProcessors()
    );

    private static BufferedImage cachedBackgroundGradient;

    public static int generateCaseOpeningGif(String playerName, int totalBalance, int priceMin, int priceMax) throws IOException {
        Future<Map<BufferedImage, String>> skinsFuture = executor.submit(() -> loadSkins(priceMin, priceMax));
        Map<BufferedImage, String> skins;
        try {
            skins = skinsFuture.get();
        } catch (InterruptedException | ExecutionException e) {
            throw new IOException("Error during GIF generation", e);
        }

        if (skins.isEmpty()) throw new IOException("No skins found in " + SKIN_FOLDER);

        List<Map.Entry<BufferedImage, String>> skinEntries = new ArrayList<>(skins.entrySet());
        Collections.shuffle(skinEntries);

    

        List<BufferedImage> skinsImages = new ArrayList<>(skinEntries.size());
        List<String> skinNames = new ArrayList<>(skinEntries.size());



        for (Map.Entry<BufferedImage, String> entry : skinEntries) {
            skinsImages.add(entry.getKey());
            skinNames.add(entry.getValue());
        }

        Random random = ThreadLocalRandom.current();
        int randomStopOffset = random.nextInt(110);

        String skinName = skinNames.get(1);
        skinName = skinName.substring(0, skinName.lastIndexOf('.'));

        SkinInfo skinInfo = findSuitableSkin(skinName, priceMin, priceMax);
        if (skinInfo == null) {
            throw new IOException("No suitable skin found for the given price range");
        }

        if (skinInfo.price >= 50) {
            String avatarName = (skinName + " " + skinInfo.condition +
                    (skinInfo.stattrakStatus.equals("StatTrak") ? " ST" : "")).toLowerCase();
            UserAvatarRepository.assignAvatarToUser(playerName, avatarName);
        }

        cachedBackgroundGradient = generateBackgroundGradient(playerName);

            if (skinsImages.size() > 13) {
                skinsImages = new ArrayList<>(skinsImages.subList(0, 13));
            }

        List<BufferedImage> frames = generateFrames(skinsImages, randomStopOffset, skinName,
                skinInfo.condition, skinInfo.stattrakStatus,
                skinInfo.price, playerName, totalBalance);

        byte[] gifBytes = createGif(frames);

        if (gifBytes != null) {
            ImageUtils.setClipboardGif(gifBytes);
        }

        return skinInfo.price;
    }

    private static SkinInfo findSuitableSkin(String skinName, int priceMin, int priceMax) {
        List<String> shuffledConditions = new ArrayList<>(CONDITIONS);
        Collections.shuffle(shuffledConditions);

        List<String> shuffledStattrakStatuses = new ArrayList<>(STATTRAK_STATUSES);
        Collections.shuffle(shuffledStattrakStatuses);

        for (String condition : shuffledConditions) {
            for (String stattrakStatus : shuffledStattrakStatuses) {
                int price = SkinPriceRepository.getSkinPrice(skinName, condition, stattrakStatus);
                if (price > 0 && price >= priceMin && price <= priceMax) {
                    return new SkinInfo(condition, stattrakStatus, price);
                }
            }
        }
        return null;
    }

private static Map<BufferedImage, String> loadSkins(int priceMin, int priceMax) throws IOException {
    String cacheKey = priceMin + "-" + priceMax;
    if (skinsCache.containsKey(cacheKey)) {
        return skinsCache.get(cacheKey);
    }

    List<String> skinsFilesNames = SkinPriceRepository.getSkinsFilesNames(priceMin, priceMax);
    File[] skinFiles = new File(SKIN_FOLDER).listFiles();

    if (skinFiles == null) {
        throw new IOException("Skins folder is empty or does not exist: " + SKIN_FOLDER);
    }

    Map<BufferedImage, String> skins = new ConcurrentHashMap<>();
    List<Future<?>> futures = new ArrayList<>();

    for (File skinFile : skinFiles) {
        if (skinsFilesNames.contains(skinFile.getName())) {
            futures.add(executor.submit(() -> {
                try {
                    BufferedImage skin = ImageIO.read(skinFile);
                    if (skin != null) {
                        BufferedImage resizedSkin = resizeImage(skin, SKIN_WIDTH, SKIN_HEIGHT);
                        skins.put(resizedSkin, skinFile.getName());
                    }
                } catch (IOException e) {
                    System.err.println("Error loading skin: " + skinFile.getName());
                }
            }));
        }
    }

    for (Future<?> future : futures) {
        try {
            future.get();
        } catch (InterruptedException | ExecutionException e) {
            throw new IOException("Error loading skins", e);
        }
    }

    skinsCache.put(cacheKey, skins);
    return skins;
}

    private static List<BufferedImage> generateFrames(List<BufferedImage> skins, int randomStopOffset,
                                                     String skinName, String skinCondition, String skinStattrakStatus,
                                                     int skinPrice, String playerName, int totalBalance) {
        List<BufferedImage> frames = new ArrayList<>(FRAME_COUNT + FINAL_FRAME_REPEAT);

        double maxSpeed = 1500;
        double minSpeed = 50;

        int totalFrames = FRAME_COUNT;
        double slowDownStart = 0.2;

        for (int i = 0; i < totalFrames; i++) {
            double progress = (double) i / (totalFrames - 1);

            double speed;
            if (progress < slowDownStart) {
                speed = maxSpeed;
            } else {
                double t = (progress - slowDownStart) / (1.0 - slowDownStart);
                speed = minSpeed + (maxSpeed - minSpeed) * Math.pow(1 - t, 2);
            }

            boolean finalFrames = i >= (FRAME_COUNT - FINAL_FRAME_COUNT);
            frames.add(generateFrame(skins, (int) speed, randomStopOffset, skinName,
                    skinCondition, skinStattrakStatus, skinPrice,
                    finalFrames, playerName, totalBalance));
        }

        for (int j = 0; j < FINAL_FRAME_REPEAT; j++) {
            frames.add(generateFrame(skins, (int) minSpeed, randomStopOffset, skinName,
                    skinCondition, skinStattrakStatus, skinPrice,
                    true, playerName, totalBalance));
        }

        return frames;
    }

    private static BufferedImage generateFrame(List<BufferedImage> skins, int speed, int randomStopOffset,
                                               String skinName, String skinCondition, String skinStattrakStatus,
                                               int skinPrice, boolean finalFrames,
                                               String playerName, int totalBalance) {
        BufferedImage image = new BufferedImage(OUTPUT_WIDTH, OUTPUT_HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        try {
            g.drawImage(cachedBackgroundGradient, 0, 0, null);

            int totalSkins = skins.size();
            int offset = -(speed) % (totalSkins * SKIN_SPACING) + randomStopOffset;

            for (int i = 0; i < totalSkins * 2; i++) {
                int index = i % totalSkins;
                int x = offset + i * SKIN_SPACING;
                g.drawImage(skins.get(index), x, 25, SKIN_WIDTH, SKIN_HEIGHT, null);
            }

            g.setColor(Color.YELLOW);
            g.setStroke(new BasicStroke(2));
            g.drawRect(OUTPUT_WIDTH / 2, 0, 2, OUTPUT_HEIGHT);

            if (finalFrames) {
                drawFinalFrameInfo(g, skinName, skinCondition, skinStattrakStatus, skinPrice, playerName, totalBalance);
            }

            return image;
        } finally {
            g.dispose();
        }
    }

    private static BufferedImage generateBackgroundGradient(String playerName) {
        BufferedImage bg = new BufferedImage(OUTPUT_WIDTH, OUTPUT_HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = bg.createGraphics();
        try {
            g.setPaint(GradientGenerator.generateGradientFromUsername(playerName, true, OUTPUT_WIDTH, OUTPUT_HEIGHT));
            g.fillRect(0, 0, OUTPUT_WIDTH, OUTPUT_HEIGHT);
            return bg;
        } finally {
            g.dispose();
        }
    }

    private static void drawFinalFrameInfo(Graphics2D g, String skinName, String skinCondition,
                                           String skinStattrakStatus, int skinPrice,
                                           String playerName, int totalBalance) {
        GradientPaint gradient = new GradientPaint(
            10, 10, new Color(0, 0, 0, 200),
            390, 140, new Color(50, 50, 50, 200)
        );
        g.setPaint(gradient);
        g.fillRoundRect(10, 40, 380, 100, 20, 20);

        g.setFont(new Font("Arial", Font.BOLD, 16));
        drawTextWithShadow(g,
            skinStattrakStatus.equals("StatTrak") ? "StatTrak™ " + skinName : skinName,
            30, 70,
            skinStattrakStatus.equals("StatTrak") ? Color.ORANGE : Color.WHITE
        );

        g.setFont(new Font("Arial", Font.PLAIN, 14));
        drawTextWithShadow(g, skinCondition, 30, 95, Color.WHITE);
        drawTextWithShadow(g, "Price: $" + skinPrice, 30, 115, Color.WHITE);

        g.setColor(Color.ORANGE);
        g.fillOval(15, 45, 15, 15);
        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 12));
        g.drawString("$", 20, 57);

        g.setColor(Color.ORANGE);
        g.setFont(new Font("Arial", Font.BOLD, 14));
        String balanceText = playerName + ": " + (totalBalance + skinPrice);
        g.drawString(balanceText, 200, 115);

        g.setColor(new Color(255, 255, 255, 100));
        g.setStroke(new BasicStroke(2));
        g.drawRoundRect(10, 40, 380, 100, 20, 20);
    }

    private static void drawTextWithShadow(Graphics2D g, String text, int x, int y, Color color) {
        g.setColor(Color.BLACK);
        g.drawString(text, x + 2, y + 2);
        g.setColor(color);
        g.drawString(text, x, y);
    }

    private static byte[] createGif(List<BufferedImage> frames) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        AnimatedGifEncoder encoder = new AnimatedGifEncoder();

        encoder.start(baos);
        encoder.setDelay(40);
        encoder.setRepeat(0);

        for (BufferedImage frame : frames) {
            encoder.addFrame(frame);
        }

        encoder.finish();
        return baos.toByteArray();
    }

    private static BufferedImage resizeImage(BufferedImage originalImage, int targetWidth, int targetHeight) {
        Image resultingImage = originalImage.getScaledInstance(targetWidth, targetHeight, Image.SCALE_SMOOTH);
        BufferedImage outputImage = new BufferedImage(targetWidth, targetHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g2d = outputImage.createGraphics();
        try {
            g2d.drawImage(resultingImage, 0, 0, null);
        } finally {
            g2d.dispose();
        }
        return outputImage;
    }

    private static class SkinInfo {
        String condition;
        String stattrakStatus;
        int price;

        SkinInfo(String condition, String stattrakStatus, int price) {
            this.condition = condition;
            this.stattrakStatus = stattrakStatus;
            this.price = price;
        }
    }

}
