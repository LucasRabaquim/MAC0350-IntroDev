CREATE TABLE user {
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    date_birth TEXT NOT NULL
}

CREATE TABLE annotation {
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_ISBN TEXT NOT NULL,
    annotation_text TEXT NOT NULL,
    date_creation  TEXT NOT NULL,
    is_public INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (user_id) REFERENCES user(id)
}

CREATE TABLE follower {
    user_followed INTEGER NOT NULL,
    user_following INTEGER NOT NULL,

    FOREIGN KEY (user_followed) REFERENCES user(id),
    FOREIGN KEY (user_following) REFERENCES user(id)
}

CREATE TABLE following {
    user_following INTEGER NOT NULL,
    user_followed INTEGER NOT NULL,

    FOREIGN KEY (user_following) REFERENCES user(id),
    FOREIGN KEY (user_followed) REFERENCES user(id)
}

CREATE TABLE saved_annotation {
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    annotation_id INTEGER NOT NULL,
    book_ISBN TEXT NOT NULL,
    annotation_text TEXT NOT NULL,
    date_creation  TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES user(id)
    FOREIGN KEY (annotation_id) REFERENCES annotation(id)
}