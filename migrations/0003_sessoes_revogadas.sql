CREATE TABLE revoked_tokens (
	jti VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	PRIMARY KEY (jti)
);
