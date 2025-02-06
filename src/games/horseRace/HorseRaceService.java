package games.horseRace;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import model.Horse;
import service.MessageService;

public class HorseRaceService {
    private final static int horseLength = 270;
    private final static int trackLength = 980;
    
    
        public static int startRace(int selectedHorse) {

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
                HorseRaceImageGenerator.drawHorseRace(raceHorses);
                MessageService.sendMessageFromClipboard(true);
                Thread.sleep(3000);
            } catch (Exception e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }

            while (!raceFinished) {

                raceFinished = executeRound(raceHorses);
                            try {
                                HorseRaceImageGenerator.drawHorseRace(raceHorses);
                                MessageService.sendMessageFromClipboard(true);
                                Thread.sleep(3000);
                            } catch (Exception e) {
                                e.printStackTrace();
                            }
                
                            try {
                                Thread.sleep(1000);
                            } catch (Exception e) {
                            }
                
                        }
                
                        raceHorses.sort((h1, h2) -> Integer.compare(h2.getPosition(), h1.getPosition()));
                
                        return raceHorses.get(0).getImageNumber();
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


}