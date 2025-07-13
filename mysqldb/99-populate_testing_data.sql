-- Insert Users
INSERT INTO User (UserID, Username, Email, Role, TOTPSecretEncrypted, CreationTime) VALUES
(1, 'admin', 'admin@example.com', 'admin', 'gAAAAABoRAJyn3YxtVNzPYDFhXIUuHBOxlogOPckjK_CX94XM6N_Ll3IbaX30FyR5Palf4DeJohKd4Or20k0_5UBdaOEO2npzg48rnHlSfIR8c4c9ez1pN5qsd0UUnhfxCatgWSYwIpM', NOW()),
(2, 'alice', 'alice@example.com', 'user',  'gAAAAABoRAJ_5kuMcxkNJoEpBs5jLRORr-1CIzYShKMUMtZ4bmtHbyUx57FcjFZQEl7QTqc0L55Ki9SryT4h-XaKzMXz4biTUtZa31fgEsqcs5pq0-27XhlMc5k1Er_UN0sTB5Zhub-r', NOW());

-- Insert Devices
INSERT INTO Device (DeviceID, UserID, DeviceHMACSignature, DeviceType, LastLogin) VALUES
('e1e1d2634929125249c7a4626573724b', 1, '29fe80ba56d4a5b3a5f503119686790fd2141489f9b576d190ae4b83924cfc41', 'Windows Firefox', NOW()),
('88039525d4f12b8fc4e0c4fc84fd4db4', 2, 'd7395981c9c11019cae570d553c20ecc8f2a9910e8f7778d6b37cdf7baad35e9', 'Iphone Safari', NOW());

-- Insert Services
INSERT INTO Service (ServiceID, ServiceName, ServiceTokenHash, HashSalt, CreationTime) VALUES
(1, 'EmailService', 'ae0fda32f8c12d9f63c7f229e9f30a44b661a2e61e028b80b931907a35fe0b6f29437088a004571dd903c4c69106bf27fd91b2566ab615ea1a38d7ac11d57db7', 'e2861b0f9808f59ae8bc6df8a0fe30b8', NOW()),
(2, 'CloudStorage', '74d555bde5a584549052c44a85e9f9200905f01181ef90b58823a2d805a0e431d7b6c59a19de49ba242ee3716a39d58aa9981fe69bc0edf6b2c173352f51e97e', '36206de129479fb757b54a2e46971e6c', NOW());

-- Link Users to Services (UserService)
INSERT INTO UserService (UserID, ServiceID, Scope, UserServiceTokenEncrypted, LastLogin) VALUES
(1, 1, 'read:user-role,', 'gAAAAABoRe3TyYxqA_bHwPMOSXTlrDPP3d5XSXLFow9Oyu3x-EzBIGsJyRlzmTnVZn3MW-JjjeOdcBapbH7xP3Xr2nwTdFYgmm0LuRjagu50F2va_LyfbkRM4q1kMBmz1rtn6gTka8AD', NOW()),
(1, 2, 'read:user-role,read:username,', 'gAAAAABoRe2uoYfhjENBspDJLbhckCQQxIf2Qbxah7gcWsk4vum0oz1XYI0FX9f6Jgt3Yw5cOfHFianoSCttHN6mE0AG3eCTv45Keu_VaUhMpZwHKlTrlyyXOpzFMjwrrH4EuW8NQ9sE', NOW()),
(2, 1, 'read:email,', 'gAAAAABoRe3bPfb0QUtNhUJhoVMO93olKoFmfckjX-0rubEIMcw_1ue_7U40AEk1cAKpE7XY9MC0MaRlsxmFB9xad5adL7ccQSu3Z3ODVWCKIAVcebP3SAdl_cr4WsCo6YA1bQQFAknq', NOW());

