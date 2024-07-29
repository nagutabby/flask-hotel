DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS reservation;

CREATE TABLE user(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    age INTEGER NOT NULL,
    UNIQUE(username, age)
);

CREATE TABLE reservation(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  number_rooms INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id)
);
