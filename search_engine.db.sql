BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "file" (
	"id"	INTEGER NOT NULL,
	"file"	VARCHAR(255) NOT NULL,
	"url"	TEXT,
	"uploaded_at"	DATETIME,
	"indexed_at"	DATETIME,
	"indexed"	INTEGER,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "redundace" (
	"word"	INTEGER NOT NULL,
	"file"	INTEGER NOT NULL,
	"wheight"	FLOAT NOT NULL,
	PRIMARY KEY("word","file"),
	FOREIGN KEY("file") REFERENCES "file"("id"),
	FOREIGN KEY("word") REFERENCES "word"("id")
);
CREATE TABLE IF NOT EXISTS "result" (
	"id"	INTEGER NOT NULL,
	"search"	INTEGER NOT NULL,
	"file"	INTEGER NOT NULL,
	"score"	FLOAT NOT NULL,
	"clicked"	INTEGER,
	PRIMARY KEY("id"),
	FOREIGN KEY("file") REFERENCES "file"("id"),
	FOREIGN KEY("search") REFERENCES "search"("id")
);
CREATE TABLE IF NOT EXISTS "search" (
	"id"	INTEGER NOT NULL,
	"query"	TEXT NOT NULL,
	"at"	DATETIME,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "word" (
	"id"	INTEGER NOT NULL,
	"word"	VARCHAR(255) NOT NULL,
	PRIMARY KEY("id"),
	UNIQUE("word")
);
COMMIT;
