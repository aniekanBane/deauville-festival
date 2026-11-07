-- Tables

CREATE TABLE IF NOT EXISTS "festival" (
    "festival_id" INTEGER NOT NULL CONSTRAINT "pk_festival" PRIMARY KEY,
    "name" TEXT NOT NULL,
    "first_day" TEXT NOT NULL,
    "last_day" TEXT NOT NULL,
    CONSTRAINT "ck_festival_id" CHECK (festival_id = 1)
);

CREATE TABLE IF NOT EXISTS "venues" (
    "venue_id" INTEGER NOT NULL CONSTRAINT "pk_venues" PRIMARY KEY AUTOINCREMENT,
    "slug" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "capacity" INTEGER NOT NULL,
    "address" TEXT NOT NULL,
    CONSTRAINT "ak_venue_slug" UNIQUE ("slug"),
    CONSTRAINT "ck_capacity" CHECK (capacity > 0)
);

CREATE TABLE IF NOT EXISTS "artists" (
    "artist_id" INTEGER NOT NULL CONSTRAINT "pk_artists" PRIMARY KEY AUTOINCREMENT,
    "slug" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "bio" TEXT NOT NULL,
    "photo_url" TEXT NOT NULL,
    CONSTRAINT "ak_artist_slug" UNIQUE ("slug")
);

CREATE TABLE IF NOT EXISTS "performances" (
    "performance_id" INTEGER NOT NULL CONSTRAINT "pk_performances" PRIMARY KEY AUTOINCREMENT,
    "kind" TEXT NOT NULL,
    "venue_slug" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "start" TEXT NOT NULL,
    "duration_minutes" INTEGER NOT NULL,
    "description" TEXT NOT NULL,
    "host_slug" TEXT NULL,
    "artist_slug" TEXT NULL,
    "min_age" INTEGER NULL,
    "teacher_slug" TEXT NULL,
    "max_participants" INTEGER NULL,
    "participants" TEXT NULL,
    CONSTRAINT "ck_kind" CHECK (kind IN ('solo', 'lineup', 'workshop')),
    CONSTRAINT "ck_duration_minutes" CHECK (duration_minutes >= 1 AND duration_minutes <= 360),
    CONSTRAINT "ck_artist_slug" CHECK (kind <> 'solo' OR artist_slug IS NOT NULL),
    CONSTRAINT "ck_min_age" CHECK (kind <> 'solo' OR (min_age IS NOT NULL AND min_age >= 0 AND min_age <= 18)),
    CONSTRAINT "ck_host_slug" CHECK (kind <> 'lineup' OR host_slug IS NOT NULL),
    CONSTRAINT "ck_teacher_slug" CHECK (kind <> 'workshop' OR teacher_slug IS NOT NULL),
    CONSTRAINT "ck_max_participants" CHECK (kind <> 'workshop' OR (max_participants IS NOT NULL AND max_participants >= 1)),
    CONSTRAINT "ck_participants" CHECK (kind <> 'workshop' OR participants IS NOT NULL),
    CONSTRAINT "fk_performances_artists_artist_slug" 
        FOREIGN KEY ("artist_slug") REFERENCES "artists" ("slug") ON DELETE RESTRICT,
    CONSTRAINT "fk_performances_artists_host_slug" 
        FOREIGN KEY ("host_slug") REFERENCES "artists" ("slug") ON DELETE RESTRICT,
    CONSTRAINT "fk_performances_artists_teacher_slug" 
        FOREIGN KEY ("teacher_slug") REFERENCES "artists" ("slug") ON DELETE RESTRICT,
    CONSTRAINT "fk_performances_venues_venue_slug" 
        FOREIGN KEY ("venue_slug") REFERENCES "venues" ("slug") ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "lineup_performance_acts" (
    "performance_id" INTEGER NOT NULL,
    "artist_slug" TEXT NOT NULL,
    CONSTRAINT "pk_lineup_performance_acts" PRIMARY KEY ("performance_id", "artist_slug"),
    CONSTRAINT "fk_lineup_performance_acts_artist_artist_slug" 
        FOREIGN KEY ("artist_slug") 
        REFERENCES "artists" ("slug") 
        ON DELETE RESTRICT,
    CONSTRAINT "fk_lineup_performance_acts_performance_performance_id" 
        FOREIGN KEY ("performance_id")
        REFERENCES "performances" ("performance_id")
        ON DELETE CASCADE
);

-- Indexes

CREATE INDEX IF NOT EXISTS "ix_lineup_performance_acts_artist_slug" 
    ON "lineup_performance_acts" ("artist_slug");

CREATE INDEX IF NOT EXISTS "ix_performances_artist_slug" ON "performances" ("artist_slug");

CREATE INDEX IF NOT EXISTS "ix_performances_host_slug" ON "performances" ("host_slug");

CREATE INDEX IF NOT EXISTS "ix_performances_teacher_slug" ON "performances" ("teacher_slug");

CREATE INDEX IF NOT EXISTS "ix_performances_venue_slug" ON "performances" ("venue_slug");