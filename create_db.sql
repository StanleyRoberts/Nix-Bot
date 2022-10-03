CREATE TABLE Guilds(ID INTEGER, CountingChannelID INTEGER, BirthdayChannelID INTEGER, FactChannelID INTEGER, CurrentCount INTEGER, LastCounterID INTEGER, HighScoreCounting INTEGER, FailRoleID INTEGER, PRIMARY KEY(ID));
CREATE TABLE Birthdays(GuildID INTEGER, UserID INTEGER, Birthdate TEXT, FOREIGN KEY(GuildID) REFERENCES Guilds(ID), PRIMARY KEY(GuildID, UserID));