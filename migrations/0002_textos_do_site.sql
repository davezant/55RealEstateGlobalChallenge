CREATE TABLE site_texts (
	text_id INTEGER NOT NULL, 
	page VARCHAR(40) NOT NULL, 
	field VARCHAR(40) NOT NULL, 
	value TEXT NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (text_id), 
	CONSTRAINT uq_site_texts_page_field UNIQUE (page, field)
);
