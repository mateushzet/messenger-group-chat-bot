package games.horseRace;

import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import com.madgag.gif.fmsware.AnimatedGifEncoder;

import model.Horse;
import service.MessageService;
import utils.ImageUtils;

public class HorseRaceService {
    private final static int horseLength = 270;
    private final static int trackLength = 980;
    private static int winnerHorse = 0;
    
    public static int generateFrames(int selectedHorse, int userBalance, int betAmmount, String playerName) {
        List<BufferedImage> frames = startRace(selectedHorse, userBalance, betAmmount, playerName);
        
        byte[] gifBytes = createGif(frames);
        if (gifBytes != null) {
            ImageUtils.setClipboardGif(gifBytes);
        }
        MessageService.sendMessageFromClipboard(true);
        return winnerHorse;
    }

        private static byte[] createGif(List<BufferedImage> frames) {
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream()) {
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(byteArrayOutputStream);
            encoder.setDelay(300);
            encoder.setRepeat(0);
            encoder.setQuality(10);
            BufferedImage frame;
            BufferedImage resizedFrame;

            for (int i = 0; i < frames.size() - 1; i ++) {
                frame = frames.get(i);
                resizedFrame = resizeImage(frame, 560, 300);
                encoder.addFrame(frame);
            }

            for (int j = 0; j < 20; j++) {
                frame = frames.get(frames.size() - 1);
                resizedFrame = resizeImage(frame, 560, 300);
                encoder.addFrame(frame);
            }

            encoder.finish();
            return byteArrayOutputStream.toByteArray();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
    
        public static List<BufferedImage> startRace(int selectedHorse, int userBalance, int betAmmount, String playerName) {
            List<BufferedImage> frames = new ArrayList<>();
            List<Horse> allHorses = Horse.copyHorses(HorseRaceBettingService.allHorses);
            List<Horse> raceHorses = new ArrayList<>();
            
            raceHorses.add(allHorses.get(selectedHorse - 1));

            
            Collections.shuffle(allHorses);

            for (Horse horse : allHorses) {
                if (horse.getImageNumber() != selectedHorse && raceHorses.size() < 6) {
                    raceHorses.add(horse);
                }
            }

            Collections.shuffle(raceHorses);

            boolean raceFinished = false;

            try {
                frames.add(HorseRaceImageGenerator.drawHorseRace(raceHorses, selectedHorse, false, userBalance, betAmmount, playerName));
            } catch (Exception e) {
                e.printStackTrace();
            }

            while (!raceFinished) {

                raceFinished = executeRound(raceHorses);
                            try {
                                frames.add(HorseRaceImageGenerator.drawHorseRace(raceHorses, selectedHorse, false, userBalance, betAmmount, playerName));
                            } catch (Exception e) {
                                e.printStackTrace();
                            }
                        }
                        try {
                            frames.add(HorseRaceImageGenerator.drawHorseRace(raceHorses, selectedHorse, true, userBalance, betAmmount, playerName));
                        } catch (Exception e) {
                        }
                        raceHorses.sort((h1, h2) -> Integer.compare(h2.getPosition(), h1.getPosition()));
                        winnerHorse = raceHorses.get(0).getImageNumber();
                        return frames;
                    }
                
        private static boolean executeRound(List<Horse> horses) {
            boolean raceFinished = false;
    
            for (Horse horse : horses) {
                horse.move();    
                if (horse.getPosition() >= trackLength - (2 * horseLength)) {
                raceFinished = true;
            }
        }
        return raceFinished;
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