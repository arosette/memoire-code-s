CREATE TABLE "users" (
    "userid" VARCHAR(255) PRIMARY KEY  NOT NULL,
    "pwd" VARCHAR(255) NOT NULL,
    "phone_serial_number" VARCHAR(255) NOT NULL,
    "challenge" BINARY(64) DEFAULT (null),
    "challenge_exp_date" DATETIME DEFAULT (null),
    "qr_code_token" BINARY(64) DEFAULT (null),
    "qr_code_exp_date" DATETIME DEFAULT (null),
    "tmp_session_key" BINARY(64) DEFAULT (null),
    "tmp_session_key_exp" DATETIME DEFAULT (null),
    "session_key" BINARY(64) DEFAULT (null),
    "session_key_exp" DATETIME DEFAULT (null)
    )
