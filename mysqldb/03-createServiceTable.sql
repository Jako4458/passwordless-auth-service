CREATE TABLE Service (
    ServiceID INT AUTO_INCREMENT PRIMARY KEY,
    ServiceName VARCHAR(100) NOT NULL,
    ServiceTokenHash VARCHAR(255) NOT NULL,
    HashSalt CHAR(32) NOT NULL,
    CreationTime DATETIME DEFAULT CURRENT_TIMESTAMP
);

