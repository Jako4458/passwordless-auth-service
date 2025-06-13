CREATE TABLE Device (
    DeviceID VARCHAR(128) PRIMARY KEY,
    UserID INT NOT NULL,
    DeviceHMACSignature VARCHAR(88) NOT NULL,
    DeviceType VARCHAR(32),
    LastLogin DATETIME,

    CONSTRAINT fk_devices_user FOREIGN KEY (UserID)
        REFERENCES User(UserID)
        ON DELETE CASCADE
);
