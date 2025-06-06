CREATE TABLE IF NOT EXISTS binds (
    username TEXT NOT NULL,
    bind_id INTEGER NOT NULL,
    command TEXT NOT NULL,
    PRIMARY KEY (username, bind_id)
);


select * from binds
select * from users