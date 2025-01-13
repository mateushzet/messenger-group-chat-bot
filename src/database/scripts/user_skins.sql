CREATE TABLE user_skins (
    user_name TEXT NOT NULL,
    skin_id VARCHAR(50) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_name, skin_id),
    FOREIGN KEY (user_name) REFERENCES users(user_name)
);