BEGIN;
CREATE TABLE "bookmarks_link" (
    "id" integer NOT NULL PRIMARY KEY,
    "url" varchar(200) NOT NULL UNIQUE
)
;
CREATE TABLE "bookmarks_bookmarks" (
    "id" integer NOT NULL PRIMARY KEY,
    "title" varchar(200) NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "link_id" integer NOT NULL REFERENCES "bookmarks_link" ("id")
)
;
CREATE TABLE "bookmarks_tag_bookmarks" (
    "id" integer NOT NULL PRIMARY KEY,
    "tag_id" integer NOT NULL,
    "bookmarks_id" integer NOT NULL REFERENCES "bookmarks_bookmarks" ("id"),
    UNIQUE ("tag_id", "bookmarks_id")
)
;
CREATE TABLE "bookmarks_tag" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(64) NOT NULL UNIQUE
)
;
CREATE TABLE "bookmarks_sharedbookmark_users_voted" (
    "id" integer NOT NULL PRIMARY KEY,
    "sharedbookmark_id" integer NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    UNIQUE ("sharedbookmark_id", "user_id")
)
;
CREATE TABLE "bookmarks_sharedbookmark" (
    "id" integer NOT NULL PRIMARY KEY,
    "bookmark_id" integer NOT NULL UNIQUE REFERENCES "bookmarks_bookmarks" ("id"),
    "date" datetime NOT NULL,
    "votes" integer NOT NULL
)
;
CREATE TABLE "bookmarks_friendship" (
    "id" integer NOT NULL PRIMARY KEY,
    "from_friend_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "to_friend_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    UNIQUE ("to_friend_id", "from_friend_id")
)
;
CREATE TABLE "bookmarks_invitation" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(50) NOT NULL,
    "email" varchar(75) NOT NULL,
    "code" varchar(20) NOT NULL,
    "sender_id" integer NOT NULL REFERENCES "auth_user" ("id")
)
;
CREATE INDEX "bookmarks_bookmarks_403f60f" ON "bookmarks_bookmarks" ("user_id");
CREATE INDEX "bookmarks_bookmarks_bb3ce60" ON "bookmarks_bookmarks" ("link_id");
CREATE INDEX "bookmarks_friendship_46b2db40" ON "bookmarks_friendship" ("from_friend_id");
CREATE INDEX "bookmarks_friendship_1bc1380b" ON "bookmarks_friendship" ("to_friend_id");
CREATE INDEX "bookmarks_invitation_6fe0a617" ON "bookmarks_invitation" ("sender_id");
COMMIT;
