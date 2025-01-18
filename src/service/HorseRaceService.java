package service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import model.Horse;
import utils.HorseRaceImageGenerator;

public class HorseRaceService {
    private final static int trackLength = 1000;
    private final static int horseLength = 270;
    
        public static int startRace(int selectedHorse) {
            List<Horse> allHorses = new ArrayList<>();
            allHorses.add(new Horse("Thunderbolt", 50, 150, 0.05, 1));
            allHorses.add(new Horse("Lightning", 100, 200, 0.1, 2));
            allHorses.add(new Horse("Shadow", 70, 120, 0.02, 3));
            allHorses.add(new Horse("Blaze", 80, 180, 0.08, 4));
            allHorses.add(new Horse("Spirit", 60, 140, 0.03, 5));
            allHorses.add(new Horse("Flash", 50, 120, 0, 6));
            allHorses.add(new Horse("Storm", 100, 250, 0.4, 7));
            allHorses.add(new Horse("Comet", 120, 200, 0.3, 8));
            allHorses.add(new Horse("Fury", 110, 190, 0.09, 9));
    
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
            int round = 1;
    
            try {
                HorseRaceImageGenerator.drawHorseRace(raceHorses);
                MessageService.sendMessageFromClipboard(true);
                Thread.sleep(3000);
            } catch (Exception e) {
                e.printStackTrace();
            }

            while (!raceFinished) {

                System.out.println("start");
                System.out.println("Runda " + round + ":");
                raceFinished = executeRound(raceHorses);
                            round++;
                
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
                        System.out.println("\nWyniki wyścigu:");
                        for (int i = 0; i < raceHorses.size(); i++) {
                            Horse horse = raceHorses.get(i);
                            System.out.println((i + 1) + ". " + horse.getName() + " - Pozycja: " + horse.getPosition());
                        }
                
                        return raceHorses.get(0).getImageNumber();
                    }
                
                    private static boolean executeRound(List<Horse> horses) {
            boolean raceFinished = false;
    
            for (Horse horse : horses) {
                horse.move();
                System.out.println(horse.getName() + " - Pozycja: " + horse.getPosition() + (horse.isFallen() ? " (przewrócony)" : ""));
    
                if (horse.getPosition() >= trackLength - (2 * horseLength)) {
                raceFinished = true;
            }
        }
        System.out.println();
        return raceFinished;
    }


}