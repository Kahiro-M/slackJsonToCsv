-- データベース: `slack_log`
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

--
-- データベース: `slack_log`
--

-- --------------------------------------------------------

--
-- テーブルの構造 `channels`
--

CREATE TABLE IF NOT EXISTS `channels` (
  `channel_id` TEXT NOT NULL,
  `name` TEXT DEFAULT NULL,
  `is_private` INTEGER DEFAULT NULL
);

-- --------------------------------------------------------

--
-- テーブルの構造 `message`
--

CREATE TABLE IF NOT EXISTS `message` (
  `timestamp` TEXT DEFAULT NULL,
  `name` TEXT DEFAULT NULL,
  `text` TEXT,
  `files` TEXT DEFAULT NULL,
  `msgid` TEXT NOT NULL,
  `channel` TEXT DEFAULT NULL
);

-- --------------------------------------------------------

--
-- テーブルの構造 `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `user_id` TEXT NOT NULL,
  `display_name` TEXT DEFAULT NULL
);

COMMIT;


