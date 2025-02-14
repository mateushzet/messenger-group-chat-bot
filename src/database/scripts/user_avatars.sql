CREATE TABLE user_avatars (
    user_name TEXT NOT NULL,
    avatar_id VARCHAR(100) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_name, avatar_id),
    FOREIGN KEY (user_name) REFERENCES users(user_name)
);