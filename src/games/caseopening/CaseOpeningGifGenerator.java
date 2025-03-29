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
    private static final int FRAME_COUNT = 121;
    private static final int SKIN_WIDTH = 256;
    private static final int SKIN_HEIGHT = 192;
    private static final int SKIN_SPACING = 270;
    private static final String SKIN_FOLDER = "src/games/caseopening/skins";
    
    private static final List<String> CONDITIONS = Arrays.asList(
        "Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"
    );
    private static final List<String> STATTRAK_STATUSES = Arrays.asList("StatTrak", "No");
    
    private static final ExecutorService executor = Executors.newFixedThreadPool(
        Runtime.getRuntime().availableProcessors()
    );

    public static int generateCaseOpeningGif(String playerName, int totalBalance, int priceMin, int priceMax) throws IOException {
        
        Future<Map<BufferedImage, String>> skinsFuture = executor.submit(() -> loadSkins(priceMin, priceMax));
        
        try {
            Map<BufferedImage, String> skins = skinsFuture.get();
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
            int randomStopOffset = random.nextInt(220) - 160;
            int randomEndSpeed = random.nextInt(301);

            String skinName = skinNames.get(2);
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

            List<BufferedImage> frames = generateFrames(
                skinsImages, randomStopOffset, skinName, 
                skinInfo.condition, skinInfo.stattrakStatus, 
                skinInfo.price, playerName, totalBalance, randomEndSpeed
            );

            byte[] gifBytes = createGif(frames);
            if (gifBytes != null) {
                ImageUtils.setClipboardGif(gifBytes);
            }

            return skinInfo.price;
        } catch (InterruptedException | ExecutionException e) {
            throw new IOException("Error during GIF generation", e);
        }
    }

    private static SkinInfo findSuitableSkin(String skinName, int priceMin, int priceMax) {
        List<String> shuffledConditions = new ArrayList<>(CONDITIONS);
        Collections.shuffle(shuffledConditions);
        
        List<String> shuffledStattrakStatuses = new ArrayList<>(STATTRAK_STATUSES);
        Collections.shuffle(shuffledStattrakStatuses);

        for (String condition : shuffledConditions) {
            for (String stattrakStatus : shuffledStattrakStatuses) {
                int skinPrice = SkinPriceRepository.getSkinPrice(skinName, condition, stattrakStatus);
                if (skinPrice > 0 && skinPrice >= priceMin && skinPrice <= priceMax) {
                    return new SkinInfo(condition, stattrakStatus, skinPrice);
                }
            }
        }
        return null;
    }

    private static Map<BufferedImage, String> loadSkins(int minPrice, int maxPrice) throws IOException {
        List<String> skinsFilesNames = SkinPriceRepository.getSkinsFilesNames(minPrice, maxPrice);
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
                            skins.put(skin, skinFile.getName());
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
        
        return skins;
    }

    private static List<BufferedImage> generateFrames(List<BufferedImage> skins, int randomStopOffset, 
                                                     String skinName, String skinCondition, String skinStattrakStatus, 
                                                     int skinPrice, String playerName, int totalBalance, int endSpeed) {
        List<BufferedImage> frames = new ArrayList<>(FRAME_COUNT + 400);
        
        double speed = 8000;
        double deceleration = 0.97;

        for (int i = 0; i < FRAME_COUNT; i++) {
            boolean finalFrames = i >= 120;
            if (finalFrames) {
                for (int j = 0; j < 400; j++) {
                    frames.add(generateFrame(skins, (int) speed, randomStopOffset, skinName, 
                                          skinCondition, skinStattrakStatus, skinPrice, 
                                          finalFrames, playerName, totalBalance));
                }
            }
            frames.add(generateFrame(skins, (int) speed, randomStopOffset, skinName, 
                                  skinCondition, skinStattrakStatus, skinPrice, 
                                  finalFrames, playerName, totalBalance));
            speed *= deceleration;
            if (speed <= endSpeed) {
                speed = endSpeed;
            }
        }
        
        return frames;
    }

    private static BufferedImage generateFrame(List<BufferedImage> skins, int speed, int randomStopOffset, 
                                             String skinName, String skinCondition, String skinStattrakStatus,
                                             int skinPrice, boolean finalFrames, 
                                             String playerName, int totalBalance) {
        BufferedImage image = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
        
        try {
            g.setPaint(GradientGenerator.generateGradientFromUsername(playerName, true, WIDTH, HEIGHT));
            g.fillRect(0, 0, WIDTH, HEIGHT);

            int totalSkins = skins.size();
            int offset = -(speed) % (totalSkins * SKIN_SPACING) + randomStopOffset;

            for (int i = 0; i < totalSkins * 2; i++) {
                int index = i % totalSkins;
                int x = offset + i * SKIN_SPACING;
                g.drawImage(skins.get(index), x, 50, SKIN_WIDTH, SKIN_HEIGHT, null);
            }

            g.setColor(Color.YELLOW);
            g.setStroke(new BasicStroke(3));
            g.drawRect(400, 0, 2, 300);

            if (finalFrames) {
                drawFinalFrameInfo(g, skinName, skinCondition, skinStattrakStatus, 
                                 skinPrice, playerName, totalBalance);
            }
            
            return image;
        } finally {
            g.dispose();
        }
    }

    private static void drawFinalFrameInfo(Graphics2D g, String skinName, String skinCondition, 
                                         String skinStattrakStatus, int skinPrice, 
                                         String playerName, int totalBalance) {
        GradientPaint gradient = new GradientPaint(100, 100, new Color(0, 0, 0, 200), 
                                             700, 200, new Color(50, 50, 50, 200));
        g.setPaint(gradient);
        g.fillRoundRect(100, 100, 600, 150, 20, 20);

        g.setFont(new Font("Arial", Font.BOLD, 24));
        drawTextWithShadow(g, 
            skinStattrakStatus.equals("StatTrak") ? "StatTrak™ " + skinName : skinName,
            150, 150, 
            skinStattrakStatus.equals("StatTrak") ? Color.ORANGE : Color.WHITE
        );
        drawTextWithShadow(g, skinCondition, 150, 180, Color.WHITE);
        drawTextWithShadow(g, "Price: $" + skinPrice, 150, 210, Color.WHITE);

        g.setColor(Color.ORANGE);
        g.fillOval(110, 130, 20, 20);
        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 16));
        g.drawString("$", 115, 145);

        g.drawString(playerName + ": " + (totalBalance + skinPrice), 470, 230);

        g.setColor(new Color(255, 255, 255, 100));
        g.setStroke(new BasicStroke(2));
        g.drawRoundRect(100, 100, 600, 150, 20, 20);
    }

    private static void drawTextWithShadow(Graphics2D g, String text, int x, int y, Color color) {
        g.setColor(new Color(0, 0, 0, 150));
        g.drawString(text, x+2, y+2);
        g.setColor(color);
        g.drawString(text, x, y);
    }

    private static byte[] createGif(List<BufferedImage> frames) {
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream()) {
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(byteArrayOutputStream);
            encoder.setDelay(50);
            encoder.setRepeat(0);
            encoder.setQuality(10);

            for (int i = 0; i < frames.size(); i += 2) {
                encoder.addFrame(resizeImage(frames.get(i), WIDTH / 2, HEIGHT / 2));
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
        try {
            g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
            g.drawImage(originalImage, 0, 0, targetWidth, targetHeight, null);
            return resizedImage;
        } finally {
            g.dispose();
        }
    }

    private static class SkinInfo {
        final String condition;
        final String stattrakStatus;
        final int price;

        SkinInfo(String condition, String stattrakStatus, int price) {
            this.condition = condition;
            this.stattrakStatus = stattrakStatus;
            this.price = price;
        }
    }

    public static void shutdown() {
        executor.shutdown();
    }
}