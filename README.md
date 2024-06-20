# json_to_csv_for_slack
Convert to csv from exported json data in slack service.

[Qiita](https://qiita.com/beckyJPN/items/4c94a35587d51a0fba0c)にフォーク元の制作者の記事があります。

# Environment

- OS: Windows 11 23H2
- python: 3.11.1
- pyinstaller: 6.5.0

# Export json file or SQL

check for [official site](https://slack.com/intl/ja-jp/help/articles/201658943-%E3%83%AF%E3%83%BC%E3%82%AF%E3%82%B9%E3%83%9A%E3%83%BC%E3%82%B9%E3%81%AE%E3%83%87%E3%83%BC%E3%82%BF%E3%82%92%E3%82%A8%E3%82%AF%E3%82%B9%E3%83%9D%E3%83%BC%E3%83%88%E3%81%99%E3%82%8B).

# How to use

```sh
# argv 1 : zip file path or unzipped folder path
# argv 2 : timestamp format
#          'kintone' or 'iso8601' -> YYYY-MM-DDTHH:MM:SS+09:00
#          other or NULL          -> YYYY-MM-DD HH:MM:SS
# argv 3 : output mode
#          'csv'         -> *.csv output
#          'mysql'       -> slack_log_mysql.sql (MySQL format) output
#                           (timestamp format [YYYY-MM-DD HH:MM:SS] only)
#          'sqlite'      -> slack_log_sqlite.sql (SQLite format) and SlackLog.db output
#                           (timestamp format [YYYY-MM-DD HH:MM:SS] only)
#          other or NULL ->  *.csv output
# argv 4 : SQL mode
#          'create'             -> create database and first insert
#          'upsert' or 'update' -> update or insert to database (MySQL ONLY)
#          other or NULL        -> create database and first insert
# argv 5 : unzip mode
#          '1' or 'true' or 'nozip' or 'notzip' or 'not_zip' -> argv 1 is unzipped folder path
#          other or NULL                                     -> argv 1 is zip file


# ex.)

$ python converter.py slack_log.zip kintone

# slack_csv_output/ALL_CHANNEL_TALK_DATA.csv
# slack_csv_output/[channel name].csv etc... 
# csv timestamp format is [YYYY-MM-DDTHH:MM:SS+09:00]


$ python converter.py slack_log.zip other sqlite

# slack_csv_output/slack_log_sqlite.sql
# slack_csv_output/SlackLog.db
# csv timestamp format is [YYYY-MM-DD HH:MM:SS]


$ python converter.py slack_log.zip other mysql upsert

# slack_csv_output/slack_log_sqlite.sql
# csv timestamp format is [YYYY-MM-DD HH:MM:SS]


$ python converter.py "Slack official export unzipped" other mysql create notzip

# slack_csv_output/slack_log_mysql.sql
# csv timestamp format is [YYYY-MM-DD HH:MM:SS]

```
