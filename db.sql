-- ================================================================
-- 0) GENEL AYARLAR
-- ================================================================
CREATE DATABASE social_platform;
\c social_platform;

-- ------------------------------------------------
-- 1) USERS
-- ------------------------------------------------
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin','moderator')),
    profile_picture_url VARCHAR(255),
    bio TEXT,
    location VARCHAR(100),
    date_of_birth DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login TIMESTAMP,
    notification_preferences JSONB,
    post_count INTEGER NOT NULL DEFAULT 0,
    account_status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (account_status IN ('active','suspended','deactivated')),
    subscription_level VARCHAR(20) NOT NULL DEFAULT 'free' CHECK (subscription_level IN ('free','premium','vip')),
    subscription_expiration DATE
);

-- ------------------------------------------------
-- 2) POSTS
-- ------------------------------------------------
CREATE TABLE Posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    community_id INTEGER REFERENCES Communities(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    media_url VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    likes_count INTEGER NOT NULL DEFAULT 0,
    comments_count INTEGER NOT NULL DEFAULT 0,
    shares_count INTEGER NOT NULL DEFAULT 0,
    views_count INTEGER NOT NULL DEFAULT 0,
    visibility VARCHAR(20) NOT NULL DEFAULT 'public' CHECK (visibility IN ('public','private','followers')),
    tags JSONB,
    allow_comments BOOLEAN NOT NULL DEFAULT TRUE,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_posts_user_created ON Posts(user_id, created_at DESC);
CREATE INDEX idx_posts_likes_views ON Posts(likes_count DESC, views_count DESC);

-- ------------------------------------------------
-- 3) COMMENTS
-- ------------------------------------------------
CREATE TABLE Comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES Posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES Comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    likes_count INTEGER NOT NULL DEFAULT 0,
    replies_count INTEGER NOT NULL DEFAULT 0,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    anonymous BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_comments_post_created ON Comments(post_id, created_at);
CREATE INDEX idx_comments_user_created ON Comments(user_id, created_at);

-- ------------------------------------------------
-- 4) COMMUNITIES
-- ------------------------------------------------
CREATE TABLE Communities (
    id SERIAL PRIMARY KEY,
    creator_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    visibility VARCHAR(20) NOT NULL DEFAULT 'public' CHECK (visibility IN ('public','private','restricted')),
    member_count INTEGER NOT NULL DEFAULT 0,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    rules TEXT,
    post_count INTEGER NOT NULL DEFAULT 0,
    tags JSONB,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    cover_image_url VARCHAR(255)
);

CREATE INDEX idx_comm_membercount ON Communities(member_count DESC, is_verified);

-- ------------------------------------------------
-- 5) USER_COMMUNITIES
-- ------------------------------------------------
CREATE TABLE User_Communities (
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    community_id INTEGER NOT NULL REFERENCES Communities(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member' CHECK (role IN ('member','moderator','admin')),
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, community_id)
);

CREATE INDEX idx_uc_comm_role ON User_Communities(community_id, role);

-- ------------------------------------------------
-- 6) LIKES
-- ------------------------------------------------
CREATE TABLE Likes (
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES Posts(id) ON DELETE CASCADE,
    liked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, post_id)
);

-- ------------------------------------------------
-- 7) MESSAGES
-- ------------------------------------------------
CREATE TABLE Messages (
    id BIGSERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'sent' CHECK (status IN ('sent','delivered','read'))
);

CREATE INDEX idx_messages_pair_time ON Messages(sender_id, receiver_id, sent_at);
CREATE INDEX idx_messages_receiver_unread ON Messages(receiver_id, status);

-- ------------------------------------------------
-- 8) FOLLOWS
-- ------------------------------------------------
CREATE TABLE Follows (
    follower_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    followee_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    followed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, followee_id),
    CHECK (follower_id <> followee_id)
);

CREATE INDEX idx_follows_followee ON Follows(followee_id);

-- ------------------------------------------------
-- 9) NOTIFICATIONS
-- ------------------------------------------------
CREATE TABLE Notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('like','comment','follow','chat')),
    reference_id BIGINT,
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notif_user_read_time ON Notifications(user_id, is_read, created_at);

-- ------------------------------------------------
-- 10) SUBTITLES & USER_SUBTITLES
-- ------------------------------------------------
CREATE TABLE Subtitles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE User_Subtitles (
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    subtitle_id INTEGER NOT NULL REFERENCES Subtitles(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, subtitle_id)
);

-- ------------------------------------------------
-- 11) LIVESTREAMS
-- ------------------------------------------------
CREATE TABLE LiveStreams (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'live' CHECK (status IN ('live','ended')),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE INDEX idx_ls_status_started ON LiveStreams(status, started_at);

-- ------------------------------------------------
-- 12) ROLES
-- ------------------------------------------------
CREATE TABLE Roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------
-- 13) USER TAG INTERACTIONS (Recommendation)
-- ------------------------------------------------
CREATE TABLE User_Tag_Interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    interaction_type VARCHAR(50) NOT NULL CHECK (interaction_type IN ('like','view','share','comment')),
    interaction_count INTEGER NOT NULL DEFAULT 1,
    last_interacted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tag, interaction_type)
);
CREATE INDEX idx_uti_user_tag_type ON UserTagInteractions(user_id, tag, interaction_type);
CREATE INDEX idx_uti_user_count ON UserTagInteractions(user_id, interaction_count DESC, last_interacted_at DESC);
