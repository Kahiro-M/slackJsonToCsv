-- データベース: `slack_log`
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+09:00";

--
-- データベース: `slack_log`
--
CREATE DATABASE IF NOT EXISTS `slack_log` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `slack_log`;

-- --------------------------------------------------------

--
-- テーブルの構造 `channels`
--

CREATE TABLE `channels` (
  `channel_id` varchar(16) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `is_private` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='チャンネル情報';

-- --------------------------------------------------------

--
-- テーブルの構造 `message`
--

CREATE TABLE `message` (
  `timestamp` timestamp NULL DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `text` text,
  `files` varchar(2083) DEFAULT NULL,
  `msgid` varchar(255) NOT NULL,
  `channel` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- --------------------------------------------------------

--
-- テーブルの構造 `users`
--

CREATE TABLE `users` (
  `user_id` varchar(16) NOT NULL,
  `display_name` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- ダンプしたテーブルのインデックス
--

--
-- テーブルのインデックス `channels`
--
ALTER TABLE `channels`
  ADD PRIMARY KEY (`channel_id`);

--
-- テーブルのインデックス `message`
--
ALTER TABLE `message`
  ADD PRIMARY KEY (`msgid`);

--
-- テーブルのインデックス `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`);
COMMIT;


