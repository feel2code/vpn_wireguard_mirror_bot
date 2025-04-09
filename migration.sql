CREATE TABLE IF NOT EXISTS users (
	id integer PRIMARY KEY,
  user_id integer NOT NULL,
	obfuscated_user text,
	subscription_start datetime,
  subscription_end datetime
);

alter table users add is_proxy integer; 
update users set is_proxy=0;

