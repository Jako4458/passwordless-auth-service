CREATE TABLE UserService (
    UserID INT NOT NULL,
    ServiceID INT NOT NULL,
    UserServiceTokenEncrypted VARCHAR(255) NOT NULL,
    LastLogin DATETIME,

    PRIMARY KEY (UserID, ServiceID),

    CONSTRAINT fk_us_users FOREIGN KEY (UserID)
        REFERENCES User(UserID)
        ON DELETE CASCADE,

    CONSTRAINT fk_us_services FOREIGN KEY (ServiceID)
        REFERENCES Service(ServiceID)
        ON DELETE CASCADE
);

