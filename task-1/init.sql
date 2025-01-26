CREATE TABLE user_counter
(
    user_id SERIAL PRIMARY KEY,
    counter INTEGER NOT NULL,
    version INTEGER NOT NULL
);

INSERT INTO user_counter (user_id, counter, version)
VALUES (1, 0, 0);