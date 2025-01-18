package model;

import java.util.List;

public class CommandContext {
    private final String command;
    private final String userName;
    private List<String> arguments;

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

    public String getFourthArgument() {
        try {
            return this.arguments.get(3);
        } catch (IndexOutOfBoundsException e) {
            return "";
        }
    }


    public String getFifthArgument() {
        try {
            return this.arguments.get(3);
        } catch (IndexOutOfBoundsException e) {
            return "";
        }
    }

    public String getUserName() {
        return this.userName;
    }

    public String getFullCommand() {
        return this.command + arguments.toString();
    }

    public void setFirstArgument(String argument) {
        if (this.arguments == null || this.arguments.isEmpty()) {
            this.arguments = new java.util.ArrayList<>();
            this.arguments.add(argument);
        } else {
            this.arguments.set(0, argument);
        }
    }

    public void setSecondArgument(String argument) {
        if (this.arguments == null || this.arguments.isEmpty()) {
            this.arguments = new java.util.ArrayList<>();
            this.arguments.add(argument);
        } else {
            this.arguments.set(1, argument);
        }
    }
}
