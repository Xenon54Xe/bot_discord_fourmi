/i:CREATE TABLE Guild (
    guildId            INTEGER NOT NULL
                               UNIQUE,
    guildName          TEXT    NOT NULL,
    event              TEXT,
    timeBeforeLastCall INTEGER NOT NULL
                               DEFAULT (900),
    ad                 TEXT,
    cmdChannelId       INTEGER,
    eventChannelId     INTEGER,
    adChannelId        INTEGER,
    suggestion         TEXT,
    id                 INTEGER PRIMARY KEY AUTOINCREMENT
                               NOT NULL
);/i:

/i:CREATE TABLE Role (
    roleId        INTEGER NOT NULL,
    guildId       INTEGER NOT NULL,
    roleName      TEXT    NOT NULL,
    isDataManager BOOLEAN DEFAULT (0)
                          NOT NULL,
    isMovable     BOOLEAN NOT NULL
                          DEFAULT (0),
    isEvent       BOOLEAN NOT NULL
                          DEFAULT (0),
    adValue       INTEGER NOT NULL
                          DEFAULT (1),
    id            INTEGER PRIMARY KEY AUTOINCREMENT
                          NOT NULL
);/i:

/i:CREATE TABLE User (
    userId       INTEGER NOT NULL,
    guildId      INTEGER NOT NULL,
    username     TEXT,
    choice       TEXT,
    availability TEXT,
    speciality   TEXT,
    percentage   TEXT,
    ad           TEXT,
    id           INTEGER PRIMARY KEY AUTOINCREMENT
                         NOT NULL
);/i:

