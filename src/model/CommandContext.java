package model;

import java.util.List;

public class CommandContext {
    private final String command;
    private final List<String> arguments;
    private final String userName;

    public CommandContext(String command, List<String> arguments, String userName) {
        this.command = command;
        this.arguments = arguments;
        this.userName = userName;
    }

    public String getCommand() {
        return this.command;
    }

    public List<String> getArguments() {
        return this.arguments;
    }

    public String getFirstArgument() {
        try {
            return this.arguments.get(0);
        } catch (IndexOutOfBoundsException e) {
            return "";
        }
    }

    public String getSecondArgument() {
        try {
            return this.arguments.get(1);
        } catch (IndexOutOfBoundsException e) {
            return "";
        }
    }

    public String getThirdArgument() {
        try {
            return this.arguments.get(2);
        } catch (IndexOutOfBoundsException e) {
            return "";
        }
    }

    public String getUserName() {
        return this.userName;
    }
}
