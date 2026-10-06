CREATE TABLE users (
	user_id INTEGER NOT NULL, 
	role VARCHAR(50) NOT NULL, 
	username VARCHAR(126) NOT NULL, 
	email VARCHAR(126) NOT NULL, 
	hash_pwd VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (user_id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE TABLE real_estate (
	real_estate_id INTEGER NOT NULL, 
	ref VARCHAR(20) NOT NULL, 
	slug VARCHAR(100) NOT NULL, 
	title VARCHAR(100) NOT NULL, 
	property_type VARCHAR(9) NOT NULL, 
	country VARCHAR(2) NOT NULL, 
	city VARCHAR(50) NOT NULL, 
	neighborhood VARCHAR(50) NOT NULL, 
	description VARCHAR(1000) NOT NULL, 
	price_amount NUMERIC(12, 2), 
	price_currency VARCHAR(6), 
	private_area NUMERIC(8, 2), 
	built_area NUMERIC(8, 2), 
	land_area NUMERIC(8, 2), 
	bedrooms INTEGER, 
	bathrooms INTEGER, 
	parking_spaces INTEGER, 
	floor INTEGER, 
	partner VARCHAR(100) NOT NULL, 
	status VARCHAR(9) NOT NULL, 
	sold_at DATETIME, 
	PRIMARY KEY (real_estate_id), 
	UNIQUE (ref), 
	UNIQUE (slug)
);

CREATE TABLE real_estate_photos (
	photo_id INTEGER NOT NULL, 
	real_estate_id INTEGER NOT NULL, 
	file_path VARCHAR(255) NOT NULL, 
	alt VARCHAR(255) NOT NULL, 
	"order" INTEGER NOT NULL, 
	is_cover BOOLEAN NOT NULL, 
	PRIMARY KEY (photo_id), 
	FOREIGN KEY(real_estate_id) REFERENCES real_estate (real_estate_id)
);
