CREATE TABLE user_skins (
    user_name TEXT NOT NULL,
    skin_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (user_name),
    FOREIGN KEY (user_name) REFERENCES users(user_name)
);