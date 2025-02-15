package utils;

import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

import javax.imageio.ImageIO;

import repository.UserAvatarRepository;

public class ImageUtils {

    public static void setClipboardImage(final BufferedImage image) {
        TransferableImage transferable = new TransferableImage(image);
        Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
        clipboard.setContents(transferable, null);
    }

    private static class TransferableImage implements Transferable {
        private final BufferedImage image;

        public TransferableImage(BufferedImage image) {
            this.image = image;
        }

        @Override
        public DataFlavor[] getTransferDataFlavors() {
            return new DataFlavor[]{DataFlavor.imageFlavor};
        }

        @Override
        public boolean isDataFlavorSupported(DataFlavor flavor) {
            return DataFlavor.imageFlavor.equals(flavor);
        }

        @Override
        public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, IOException {
            if (!isDataFlavorSupported(flavor)) {
                throw new UnsupportedFlavorException(flavor);
            }
            return image;
        }
    }

    public static void setClipboardGif(byte[] gifBytes) {
        try {
            Transferable transferable = new Transferable() {
                @Override
                public DataFlavor[] getTransferDataFlavors() {
                    return new DataFlavor[]{DataFlavor.javaFileListFlavor};
                }

                @Override
                public boolean isDataFlavorSupported(DataFlavor flavor) {
                    return DataFlavor.javaFileListFlavor.equals(flavor);
                }

                @Override
                public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException {
                    try {
                        File tempFile = File.createTempFile("plinko", ".gif");
                        try (FileOutputStream fos = new FileOutputStream(tempFile)) {
                            fos.write(gifBytes);
                        }
                        return java.util.Collections.singletonList(tempFile);
                    } catch (Exception e) {
                        e.printStackTrace();
                        return null;
                    }
                }
            };

            Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
            clipboard.setContents(transferable, null);

            System.out.println("GIF skopiowano do schowka.");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    public static void drawUserAvatar(Graphics2D g, String username, int x, int y, int width, int height) {
        try {
            String avatarName = UserAvatarRepository.getActiveAvatarForUser(username);
            if (avatarName == null || avatarName.isEmpty()) return;

            File avatarFile = new File("src\\resources\\user_avatars\\" + avatarName + ".png");
            if (!avatarFile.exists()) return;

            BufferedImage avatar = ImageIO.read(avatarFile);

            Image scaledAvatar = avatar.getScaledInstance(width, height, Image.SCALE_SMOOTH);

            g.drawImage(scaledAvatar, x, y, null);

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static String getUserAvatarName(String username) {
        try {
            String avatarName = UserAvatarRepository.getActiveAvatarForUser(username);
            if (avatarName == null || avatarName.isEmpty()) return "";

            File avatarFile = new File("src\\resources\\user_avatars\\" + avatarName + ".png");
            if (!avatarFile.exists()) return "";

            return avatarName;

        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static void drawUserAvatarFromAvatarName(Graphics2D g, String username, int x, int y, int width, int height, String avatarName) {
        try {
            File avatarFile = new File("src\\resources\\user_avatars\\" + avatarName + ".png");
            if (!avatarFile.exists()) return;

            BufferedImage avatar = ImageIO.read(avatarFile);

            Image scaledAvatar = avatar.getScaledInstance(width, height, Image.SCALE_SMOOTH);

            g.drawImage(scaledAvatar, x, y, null);

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

}