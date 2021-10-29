BEGIN TRANSACTION;
DROP TABLE IF EXISTS "alembic_version";
CREATE TABLE IF NOT EXISTS "alembic_version" (
	"version_num"	VARCHAR(32) NOT NULL,
	CONSTRAINT "alembic_version_pkc" PRIMARY KEY("version_num")
);
DROP TABLE IF EXISTS "ecwid";
CREATE TABLE IF NOT EXISTS "ecwid" (
	"id"	INTEGER NOT NULL,
	"partners_key"	VARCHAR(128),
	"client_id"	VARCHAR(128),
	"client_secret"	VARCHAR(128),
	"token"	VARCHAR(128),
	"name"	VARCHAR(128),
	"email"	VARCHAR(128),
	"url"	VARCHAR,
	"hub_id"	INTEGER,
	FOREIGN KEY("hub_id") REFERENCES "ecwid"("id"),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "app_settings";
CREATE TABLE IF NOT EXISTS "app_settings" (
	"id"	INTEGER NOT NULL,
	"hub_id"	INTEGER NOT NULL,
	"notify_1C"	BOOLEAN NOT NULL DEFAULT 1,
	"email_1C"	VARCHAR(128),
	FOREIGN KEY("hub_id") REFERENCES "ecwid"("id"),
	CHECK("notify_1C" IN (0, 1)),
	UNIQUE("hub_id"),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "cashflow_statement";
CREATE TABLE IF NOT EXISTS "cashflow_statement" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(128) NOT NULL,
	"hub_id"	INTEGER NOT NULL,
	FOREIGN KEY("hub_id") REFERENCES "ecwid"("id"),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "income_statement";
CREATE TABLE IF NOT EXISTS "income_statement" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(128) NOT NULL,
	"hub_id"	INTEGER NOT NULL,
	FOREIGN KEY("hub_id") REFERENCES "ecwid"("id"),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "position";
CREATE TABLE IF NOT EXISTS "position" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(128) NOT NULL,
	"hub_id"	INTEGER NOT NULL,
	FOREIGN KEY("hub_id") REFERENCES "ecwid"("id"),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "project";
CREATE TABLE IF NOT EXISTS "project" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(128) NOT NULL,
	"hub_id"	INTEGER NOT NULL,
	"enabled"	BOOLEAN NOT NULL DEFAULT 1,
	"uid"	VARCHAR(128),
	FOREIGN KEY("hub_id") REFERENCES "ecwid"("id"),
	CHECK("enabled" IN (0, 1)),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "category";
CREATE TABLE IF NOT EXISTS "category" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(128) NOT NULL,
	"children"	VARCHAR NOT NULL,
	"hub_id"	INTEGER NOT NULL,
	"responsible"	VARCHAR(128),
	"functional_budget"	VARCHAR(128),
	"income_id"	INTEGER,
	"cashflow_id"	INTEGER,
	"code"	VARCHAR(128),
	FOREIGN KEY("hub_id") REFERENCES "ecwid"("id"),
	FOREIGN KEY("cashflow_id") REFERENCES "cashflow_statement"("id") ON DELETE SET NULL,
	FOREIGN KEY("income_id") REFERENCES "income_statement"("id") ON DELETE SET NULL,
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "site";
CREATE TABLE IF NOT EXISTS "site" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(128) NOT NULL,
	"project_id"	INTEGER NOT NULL,
	"uid"	VARCHAR(128),
	FOREIGN KEY("project_id") REFERENCES "project"("id"),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "user";
CREATE TABLE IF NOT EXISTS "user" (
	"id"	INTEGER NOT NULL,
	"email"	VARCHAR(128) NOT NULL,
	"password"	VARCHAR(128) NOT NULL,
	"role"	VARCHAR(10) NOT NULL DEFAULT 'default',
	"name"	VARCHAR(128),
	"phone"	VARCHAR(128),
	"position_id"	INTEGER,
	"location"	VARCHAR(128),
	"hub_id"	INTEGER,
	"email_new"	BOOLEAN NOT NULL DEFAULT 1,
	"email_modified"	BOOLEAN NOT NULL DEFAULT 1,
	"email_disapproved"	BOOLEAN NOT NULL DEFAULT 1,
	"email_approved"	BOOLEAN NOT NULL DEFAULT 1,
	"last_seen"	DATETIME,
	"note"	VARCHAR,
	"registered"	DATETIME,
	FOREIGN KEY("hub_id") REFERENCES "ecwid"("id"),
	FOREIGN KEY("position_id") REFERENCES "position"("id") ON DELETE SET NULL,
	CHECK("email_disapproved" IN (0, 1)),
	CHECK("email_new" IN (0, 1)),
	CHECK("email_approved" IN (0, 1)),
	CONSTRAINT "userroles" CHECK("role" IN ('default', 'admin', 'initiative', 'validator', 'purchaser', 'supervisor')),
	CHECK("email_modified" IN (0, 1)),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "order";
CREATE TABLE IF NOT EXISTS "order" (
	"id"	VARCHAR(128) NOT NULL,
	"initiative_id"	INTEGER NOT NULL,
	"create_timestamp"	INTEGER NOT NULL,
	"products"	VARCHAR NOT NULL,
	"total"	FLOAT NOT NULL,
	"status"	VARCHAR(15) NOT NULL DEFAULT 'new',
	"site_id"	INTEGER,
	"income_id"	INTEGER,
	"cashflow_id"	INTEGER,
	"hub_id"	INTEGER NOT NULL,
	"purchased"	BOOLEAN NOT NULL DEFAULT 0,
	"exported"	BOOLEAN NOT NULL DEFAULT 0,
	"dealdone"	BOOLEAN NOT NULL DEFAULT 0,
	FOREIGN KEY("cashflow_id") REFERENCES "cashflow_statement"("id") ON DELETE SET NULL,
	FOREIGN KEY("initiative_id") REFERENCES "user"("id"),
	FOREIGN KEY("hub_id") REFERENCES "ecwid"("id"),
	FOREIGN KEY("income_id") REFERENCES "income_statement"("id") ON DELETE SET NULL,
	FOREIGN KEY("site_id") REFERENCES "site"("id") ON DELETE SET NULL,
	CONSTRAINT "orderstatus" CHECK("status" IN ('new', 'not_approved', 'partly_approved', 'approved', 'modified')),
	CHECK("dealdone" IN (0, 1)),
	CHECK("exported" IN (0, 1)),
	CHECK("purchased" IN (0, 1)),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "user_category";
CREATE TABLE IF NOT EXISTS "user_category" (
	"user_id"	INTEGER NOT NULL,
	"category_id"	INTEGER NOT NULL,
	FOREIGN KEY("category_id") REFERENCES "category"("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id"),
	PRIMARY KEY("user_id","category_id")
);
DROP TABLE IF EXISTS "user_project";
CREATE TABLE IF NOT EXISTS "user_project" (
	"user_id"	INTEGER NOT NULL,
	"project_id"	INTEGER NOT NULL,
	FOREIGN KEY("project_id") REFERENCES "project"("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id"),
	PRIMARY KEY("user_id","project_id")
);
DROP TABLE IF EXISTS "order_approval";
CREATE TABLE IF NOT EXISTS "order_approval" (
	"id"	INTEGER NOT NULL,
	"order_id"	VARCHAR(128) NOT NULL,
	"product_id"	INTEGER,
	"user_id"	INTEGER NOT NULL,
	"remark"	VARCHAR(128),
	FOREIGN KEY("order_id") REFERENCES "order"("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id"),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "order_category";
CREATE TABLE IF NOT EXISTS "order_category" (
	"order_id"	VARCHAR(128) NOT NULL,
	"category_id"	INTEGER NOT NULL,
	FOREIGN KEY("order_id") REFERENCES "order"("id"),
	FOREIGN KEY("category_id") REFERENCES "category"("id"),
	PRIMARY KEY("order_id","category_id")
);
DROP TABLE IF EXISTS "order_event";
CREATE TABLE IF NOT EXISTS "order_event" (
	"id"	INTEGER NOT NULL,
	"order_id"	VARCHAR(128),
	"user_id"	INTEGER NOT NULL,
	"timestamp"	DATETIME NOT NULL DEFAULT (datetime('now')),
	"type"	VARCHAR(18) NOT NULL,
	"data"	VARCHAR NOT NULL DEFAULT '',
	CONSTRAINT "eventtype" CHECK("type" IN ('commented', 'approved', 'disapproved', 'quantity', 'duplicated', 'purchased', 'exported', 'merged', 'dealdone', 'income_statement', 'cashflow_statement', 'site', 'measurement', 'splitted')),
	FOREIGN KEY("order_id") REFERENCES "order"("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id"),
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "order_position";
CREATE TABLE IF NOT EXISTS "order_position" (
	"order_id"	VARCHAR(128) NOT NULL,
	"position_id"	INTEGER NOT NULL,
	"approved"	BOOLEAN NOT NULL DEFAULT 0,
	"user_id"	INTEGER,
	"timestamp"	DATETIME,
	CHECK("approved" IN (0, 1)),
	PRIMARY KEY("order_id","position_id"),
	FOREIGN KEY("position_id") REFERENCES "position"("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id") ON DELETE SET NULL,
	FOREIGN KEY("order_id") REFERENCES "order"("id")
);
DROP TABLE IF EXISTS "order_relationship";
CREATE TABLE IF NOT EXISTS "order_relationship" (
	"order_id"	VARCHAR(128) NOT NULL,
	"child_id"	VARCHAR(128) NOT NULL,
	PRIMARY KEY("order_id","child_id"),
	FOREIGN KEY("order_id") REFERENCES "order"("id"),
	FOREIGN KEY("child_id") REFERENCES "order"("id")
);
INSERT INTO "alembic_version" ("version_num") VALUES ('1');
INSERT INTO "ecwid" ("id","partners_key","client_id","client_secret","token","name","email","url","hub_id") VALUES (1,'partners_key','client_id','client_secret','token','hub','email@email.email','http://url.url',NULL),
 (2,'partners_key','client_id','client_secret','token','vendor','email@email.email','http://url.url',1);
INSERT INTO "app_settings" ("id","hub_id","notify_1C","email_1C") VALUES (1,1,1,'email@email.email');
INSERT INTO "cashflow_statement" ("id","name","hub_id") VALUES (1,'name',1);
INSERT INTO "income_statement" ("id","name","hub_id") VALUES (1,'name',1);
INSERT INTO "position" ("id","name","hub_id") VALUES (1,'name',1);
INSERT INTO "project" ("id","name","hub_id","enabled","uid") VALUES (1,'name',1,1,'uid');
INSERT INTO "category" ("id","name","children","hub_id","responsible","functional_budget","income_id","cashflow_id","code") VALUES (1,'name','[1]',1,'responsible','functional_budget',1,1,'code');
INSERT INTO "site" ("id","name","project_id","uid") VALUES (1,'name',1,'uid');
INSERT INTO "user" ("id","email","password","role","name","phone","position_id","location","hub_id","email_new","email_modified","email_disapproved","email_approved","last_seen","note","registered") VALUES (1,'email@email.email','pbkdf2:sha256:150000$UoJZNku2$101f30eba5ae59618526af9d6db8483d7a5341a2b723ac7627aba7c040be8ec1','admin','name','phone',1,'location',1,1,1,1,1,'2021-10-29 04:43:13','note','2021-10-29 04:43:13');
INSERT INTO "order" ("id","initiative_id","create_timestamp","products","total","status","site_id","income_id","cashflow_id","hub_id","purchased","exported","dealdone") VALUES ('1',1,0,'[]',1.0,'new',1,1,1,1,1,1,1);
INSERT INTO "user_category" ("user_id","category_id") VALUES (1,1);
INSERT INTO "user_project" ("user_id","project_id") VALUES (1,1);
INSERT INTO "order_approval" ("id","order_id","product_id","user_id","remark") VALUES (1,'1',NULL,1,'remark');
INSERT INTO "order_category" ("order_id","category_id") VALUES ('1',1);
INSERT INTO "order_event" ("id","order_id","user_id","timestamp","type","data") VALUES (1,'1',1,'2021-10-28 17:09:41','approved','data');
INSERT INTO "order_position" ("order_id","position_id","approved","user_id","timestamp") VALUES ('1',1,1,1,'2021-10-29 05:02:03');
INSERT INTO "order_relationship" ("order_id","child_id") VALUES ('1','1');
DROP INDEX IF EXISTS "ix_cashflow_statement_name";
CREATE INDEX IF NOT EXISTS "ix_cashflow_statement_name" ON "cashflow_statement" (
	"name"
);
DROP INDEX IF EXISTS "ix_income_statement_name";
CREATE INDEX IF NOT EXISTS "ix_income_statement_name" ON "income_statement" (
	"name"
);
DROP INDEX IF EXISTS "ix_position_name";
CREATE INDEX IF NOT EXISTS "ix_position_name" ON "position" (
	"name"
);
DROP INDEX IF EXISTS "ix_project_enabled";
CREATE INDEX IF NOT EXISTS "ix_project_enabled" ON "project" (
	"enabled"
);
DROP INDEX IF EXISTS "ix_project_name";
CREATE INDEX IF NOT EXISTS "ix_project_name" ON "project" (
	"name"
);
DROP INDEX IF EXISTS "ix_category_name";
CREATE INDEX IF NOT EXISTS "ix_category_name" ON "category" (
	"name"
);
DROP INDEX IF EXISTS "ix_site_name";
CREATE INDEX IF NOT EXISTS "ix_site_name" ON "site" (
	"name"
);
DROP INDEX IF EXISTS "ix_user_email";
CREATE UNIQUE INDEX IF NOT EXISTS "ix_user_email" ON "user" (
	"email"
);
DROP INDEX IF EXISTS "ix_user_role";
CREATE INDEX IF NOT EXISTS "ix_user_role" ON "user" (
	"role"
);
DROP INDEX IF EXISTS "ix_order_approval_product_id";
CREATE INDEX IF NOT EXISTS "ix_order_approval_product_id" ON "order_approval" (
	"product_id"
);
COMMIT;
