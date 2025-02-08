package games.caseopening;

import com.madgag.gif.fmsware.AnimatedGifEncoder;
import utils.ImageUtils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.*;
import java.util.List;

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

    public static String generateCaseOpeningGif(String playerName, int totalBalance, boolean includeStatraks) throws IOException {
        Map<BufferedImage, String> skins = loadSkins();
        if (skins.isEmpty()) throw new IOException("No skins found in " + SKIN_FOLDER);

        List<Map.Entry<BufferedImage, String>> skinEntries = new ArrayList<>(skins.entrySet());
        Collections.shuffle(skinEntries);

        List<BufferedImage> skinsImages = new ArrayList<>();
        List<String> skinNames = new ArrayList<>();

        for (Map.Entry<BufferedImage, String> entry : skinEntries) {
            skinsImages.add(entry.getKey());
            skinNames.add(entry.getValue());
        }

        Random random = new Random();
        int randomStopOffset = random.nextInt(121) - 70;

        Collections.shuffle(CONDITIONS);
        Collections.shuffle(STATTRAK_STATUSES);

        String skinName = skinNames.get(2);
        skinName = skinName.substring(0, skinName.lastIndexOf('.'));

        String skinCondition = "";
        String skinStattrakStatus = "";
        int skinPrice = 0;

        outerLoop:
        for (String condition : CONDITIONS) {
            for (String stattrakStatus : STATTRAK_STATUSES) {
                if(includeStatraks) skinPrice = SkinPriceRepository.getSkinPrice(skinName, condition, stattrakStatus);
                else skinPrice = SkinPriceRepository.getSkinPrice(skinName, condition, "No");
                if (skinPrice > 0) {
                    skinCondition = condition;
                    skinStattrakStatus = stattrakStatus;
                    break outerLoop;
                }
            }
        }

        List<BufferedImage> frames = generateFrames(skinsImages, randomStopOffset, skinName, skinCondition, skinStattrakStatus, skinPrice, playerName, totalBalance);

        byte[] gifBytes = createGif(frames);
        if (gifBytes != null) {
            ImageUtils.setClipboardGif(gifBytes);
        }

        return skinNames.get(2);
    }

    private static Map<BufferedImage, String> loadSkins() throws IOException {
        File[] skinFiles = new File(SKIN_FOLDER).listFiles();
        if (skinFiles == null) {
            throw new IOException("Skins folder is empty or does not exist: " + SKIN_FOLDER);
        }

        Map<BufferedImage, String> skins = new HashMap<>();
        for (File skinFile : skinFiles) {
            BufferedImage skin = ImageIO.read(skinFile);
            if (skin != null) {
                skins.put(skin, skinFile.getName());
            }
        }
        return skins;
    }

    private static List<BufferedImage> generateFrames(List<BufferedImage> skins, int randomStopOffset, String skinName, String skinCondition, 
                                                        String skinStattrakStatus, int skinPrice, String playerName, int totalBalance) {
        List<BufferedImage> frames = new ArrayList<>();

        double speed = 8000;
        double deceleration = 0.97;

        for (int i = 0; i < FRAME_COUNT; i++) {
            boolean finalFrames = i >= 120;
            if(finalFrames){
                for (int j = 0; j < 400; j++) {
                    frames.add(generateFrame(skins, (int) speed, randomStopOffset, skinName, skinCondition, skinStattrakStatus, skinPrice, finalFrames, playerName, totalBalance));
                }
            }
            frames.add(generateFrame(skins, (int) speed, randomStopOffset, skinName, skinCondition, skinStattrakStatus, skinPrice, finalFrames, playerName, totalBalance));
            speed *= deceleration;
            if (speed <= 200) {
                speed = 200;
            }
        }
        
        return frames;
    }

    private static BufferedImage generateFrame(List<BufferedImage> skins, int speed, int randomStopOffset, String skinName, String skinCondition, String skinStattrakStatus,
                                              int skinPrice, boolean finalFrames, String playerName, int totalBalance) {
        BufferedImage image = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        g.setColor(Color.BLACK);
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
            GradientPaint gradient = new GradientPaint(100, 100, new Color(0, 0, 0, 200), 700, 200, new Color(50, 50, 50, 200));
            g.setPaint(gradient);
            g.fillRoundRect(100, 100, 600, 150, 20, 20);

            g.setColor(Color.WHITE);
            g.setFont(new Font("Arial", Font.BOLD, 24));

            g.setColor(new Color(0, 0, 0, 150));
            g.drawString(skinStattrakStatus.equals("StatTrak") ? "StatTrak™ " + skinName : skinName, 152, 152);
            g.drawString(skinCondition, 152, 182);
            g.drawString("Price: $" + skinPrice, 152, 212);

            g.setColor(Color.WHITE);
            if (skinStattrakStatus.equals("StatTrak")) g.setColor(Color.ORANGE);
            g.drawString(skinStattrakStatus.equals("StatTrak") ? "StatTrak™ " + skinName : skinName, 150, 150);
            if (skinStattrakStatus.equals("StatTrak")) g.setColor(Color.WHITE);
            g.drawString(skinCondition, 150, 180);
            g.drawString("Price: $" + skinPrice, 150, 210);

            g.setColor(Color.ORANGE);
            g.fillOval(110, 130, 20, 20);
            g.setColor(Color.WHITE);
            g.setFont(new Font("Arial", Font.BOLD, 16));
            g.drawString("$", 115, 145);

            g.drawString(playerName + ": " + (totalBalance + skinPrice), 515, 230);

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

}