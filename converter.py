#coding: UTF-8
from cgitb import text
import sys
import os
import glob
import json
import hashlib
import datetime
import shutil
import sqlite3

# defines =====================

ID_KEY = 'id'
TEXT_KEY = 'text'
USER_KEY = 'user'
PROFILE_KEY = 'profile'
REAL_NAME_KEY = 'real_name'
DISPLAY_NAME_KEY = 'display_name'
FILES_KEY = 'files'
URL_KEY = 'url_private'
CLIENT_MSG_ID_KEY = 'client_msg_id'
DATETIME_KEY = 'ts'

OUT_PUT_DIR_NAME = 'slack_csv_output'
USER_FILE_NAME = 'users.json'
TIMESTAMP_MODE = ['kintone','iso8601']
OUTPUT_MODE = ['csv','mysql','sqlite']
OUTPUT_SQL_MODE = ['mysql','sqlite']
UNZIP_MODE = ['1','true','nozip','notzip','not_zip']

# functions =====================

# jsonファイルをjson辞書に変換
def json_file_to_data(full_path):
        f = open(full_path, 'r', encoding='utf-8')

        converted = json.load(f)

        f.close()

        return converted

# ユーザー情報を取得
def get_users(source_dir):
    users_json = json_file_to_data(source_dir)
    users = {}

    for user in users_json:
        
        name = user[PROFILE_KEY][DISPLAY_NAME_KEY]
        if not name:
            name = user[PROFILE_KEY][REAL_NAME_KEY]
        id = user[ID_KEY]
        users[id] = name

    return users

# メンションをuserデータから名称に変換
def replace_mentions(text, mentions_dict):
    for user_id, username in mentions_dict.items():
        mention_tag = f'<@{user_id}>'
        text = text.replace(mention_tag, '@'+f'{username}')
    return text

# 1メッセージのjson辞書データをカンマ区切りの1行データに変換
def get_line_text(users, item, channel, timestamp_mode, output_mode):

    text = f'{item[TEXT_KEY]}'.replace('"', '\"').replace('"', '""').replace("'","''")
    text = replace_mentions(text, users)

    name = ''
    if USER_KEY in item.keys():
        user_id = item[USER_KEY]
        if user_id in users.keys():
            name = users[user_id]

    urls = ''
    if FILES_KEY in item.keys():
        for attachmentFile in item[FILES_KEY]:

            if not URL_KEY in attachmentFile.keys():
                continue

            url = f"{attachmentFile[URL_KEY]}".replace('"', '\"')
            urls += f'{url}'

    # UNIX時間を標準時間に変換()
    timestamp = ''
    if DATETIME_KEY in item.keys():
        # UNIX時間を整数部分と小数部分に分ける
        unix_timestamp_int = int(float(item[DATETIME_KEY]))
        unix_timestamp_frac = int((float(item[DATETIME_KEY]) - unix_timestamp_int) * 1e6)  # マイクロ秒単位に変換
        standard_time = datetime.datetime.fromtimestamp(unix_timestamp_int) + datetime.timedelta(microseconds=unix_timestamp_frac)
        if(output_mode.lower() in OUTPUT_SQL_MODE):
            timestamp = standard_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            if(timestamp_mode.lower() in TIMESTAMP_MODE):
                timestamp = standard_time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
            else:
                timestamp = standard_time.strftime("%Y-%m-%d %H:%M:%S")

    msg_id = ''
    if CLIENT_MSG_ID_KEY in item.keys():
        msg_id = item[CLIENT_MSG_ID_KEY]
    else:
        # msg_idが無い場合は作成する
        msg = timestamp+name+text+urls+channel
        msg_id = hashlib.sha256(msg.encode()).hexdigest()
    
    if(output_mode.lower() in OUTPUT_SQL_MODE):
        return f"('{timestamp}','{name}','{text}','{urls}','{msg_id}','{channel}')"
    else:
        return f'"{timestamp}","{name}","{text}","{urls}","{msg_id}","{channel}"\n'

# 失敗手続き
def failed(text):
    print(f'[error] {text}')
    print('failed...')
    exit()

# 外部SQLファイルからクエリ作成
def get_query(query_file_path):
    with open(query_file_path, 'r', encoding='utf-8') as f:
        query = f.read()
    return query

# core logics =====================

def convert_json_to_csv_for_slack(source_dir,timestamp_mode='',output_mode='csv'):

    if not os.path.exists(source_dir):
        failed(f'not exists directory: {source_dir}')

    print(f'Source directory > {source_dir}')

    # 出力フォルダの作成
    output_dir = f'{source_dir}/../{OUT_PUT_DIR_NAME}'

    if os.path.exists(output_dir):
        failed(f'already exists output directory: {output_dir}')

    print(f'Create output dir > {output_dir}/')
    os.makedirs(output_dir)

    # jsonファイルを省いたチャンネル名のフォルダ一覧の取得
    channels = sorted(os.listdir(path=source_dir))
    channels = [x for x in channels if not x.endswith('.json')] 
    if(output_mode.lower() in OUTPUT_SQL_MODE):
        if(output_mode.lower() in ['mysql']):
            out_file_path = shutil.copy2("slack_log_mysql_template.sql",f"{output_dir}/slack_log_mysql.sql")
        elif(output_mode.lower() in ['sqlite']):
            out_file_path = shutil.copy2("slack_log_sqlite_template.sql",f"{output_dir}/slack_log_sqlite.sql")
        else:
            out_file_path = shutil.copy2("slack_log_mysql_template.sql",f"{output_dir}/slack_log_mysql.sql")

        hasHeader = False
        isFirst = True
        header = """
            --
            -- テーブルのデータのダンプ `channels`
            --
            
            INSERT INTO `channels` (`channel_id`, `name`, `is_private`) VALUES
        """
        lines = ''

        channels_json_dic = json_file_to_data(f"{source_dir}/channels.json")

        for channel in channels_json_dic: 
            if(isFirst == True):
                lines = f"('{channel['id']}','{channel['name']}','{'False' if channel.get('is_private') == None  else channel['is_private']}')"
                isFirst = False
            else:
                lines = f",\n('{channel['id']}','{channel['name']}','{'False' if channel.get('is_private') == None  else channel['is_private']}')"
            
            
            # SlackLogSQLファイルに書き込み
            f = open(out_file_path, 'a', encoding='utf-8')
            if(hasHeader == False):
                f.write(header)
                hasHeader = True
            f.write(lines)
            f.close()

        # SlackLogSQLファイルの末尾に;を書き込む
        f = open(out_file_path, 'a', encoding='utf-8')
        f.write(';')
        f.close()
        print(f'{len(channels_json_dic)} channels SQL converted.')
        

    users = get_users(f'{source_dir}/{USER_FILE_NAME}')
    if(output_mode.lower() in OUTPUT_SQL_MODE):
        hasHeader = False
        isFirst = True
        header = """
            --
            -- テーブルのデータのダンプ `users`
            --
            
            INSERT INTO `users` (`user_id`, `display_name`) VALUES
        """
        lines = ''

        users_json_dic = json_file_to_data(f"{source_dir}/users.json")

        for user in users_json_dic: 
            if(isFirst == True):
                lines = f"('{user['id']}','{user['profile']['display_name']}')"
                isFirst = False
            else:
                lines = f",\n('{user['id']}','{user['profile']['display_name']}')"
            
            
            # SlackLogSQLファイルに書き込み
            f = open(out_file_path, 'a', encoding='utf-8')
            if(hasHeader == False):
                f.write(header)
                hasHeader = True
            f.write(lines)
            f.close()

        # SlackLogSQLファイルの末尾に;を書き込む
        f = open(out_file_path, 'a', encoding='utf-8')
        f.write(';')
        f.close()
        print(f'{len(users_json_dic)} users SQL converted.')


    # channelフォルダ単位でループ
    hasHeader = False
    isFirst = True

    # SQL出力
    if(output_mode.lower() in OUTPUT_SQL_MODE):
        for channel in channels: 

            print(f'[{channel}]')

            json_files = sorted(glob.glob(f"{source_dir}/{channel}/*.json"))
            header = """
                --
                -- テーブルのデータのダンプ `message`
                --
                
                INSERT INTO `message` (`timestamp`, `name`, `text`, `files`, `msgid`, `channel`) VALUES
            """
            
            lines = ''

            # 日付名のjsonファイル単位でループ
            for file_full_path in json_files: 

                file_name = os.path.split(file_full_path)[1]
                date = file_name.replace('.json', '')

                json_dic = json_file_to_data(file_full_path)

                # メッセージ単位ループ
                for item in json_dic: 

                    if not TEXT_KEY in item.keys():
                        continue

                    if(isFirst == True):
                        lines += get_line_text(users, item, channel,timestamp_mode,output_mode)
                        isFirst = False
                    else:
                        lines += ',\n'+get_line_text(users, item, channel,timestamp_mode,output_mode)

                print(f'\t{date} ({len(json_dic)})')


            # SlackLogSQLファイルに書き込み
            f = open(out_file_path, 'a', encoding='utf-8')
            if(hasHeader == False):
                f.write(header)
                hasHeader = True
            f.write(lines)
            f.close()

        # SlackLogSQLファイルの末尾に;を書き込む
        f = open(out_file_path, 'a', encoding='utf-8')
        f.write(';')
        f.close()

        print(f'{len(channels)} channels SQL converted.')

        # SQLiteはDBファイルも作成
        if(output_mode.lower() in ['sqlite']):
            dbname = f"{output_dir}/SlackLog.db"
            conn = sqlite3.connect(dbname)
            # sqliteを操作するカーソルオブジェクトを作成
            cur = conn.cursor()

            # SQL実行
            query = get_query(out_file_path)
            cur.executescript(query)
            
            # コミット
            conn.commit()
            conn.close()


    # CSV出力
    else:
        # channelフォルダ単位でループ
        hasHeader = False
        for channel in channels: 

            print(f'[{channel}]')

            json_files = sorted(glob.glob(f"{source_dir}/{channel}/*.json"))
            header = '"timestamp","name","text","files","msgid","channel"\n'
            lines = ''

            # 日付名のjsonファイル単位でループ
            for file_full_path in json_files: 

                file_name = os.path.split(file_full_path)[1]
                date = file_name.replace('.json', '')

                json_dic = json_file_to_data(file_full_path)

                # メッセージ単位ループ
                for item in json_dic: 

                    if not TEXT_KEY in item.keys():
                        continue

                    lines += get_line_text(users, item, channel,timestamp_mode,output_mode)

                print(f'\t{date} ({len(json_dic)})')

            # 変換した情報をチャンネル名のcsvファイルに書き込み
            out_file_path = f"{output_dir}/{channel}.csv"
            f = open(out_file_path, 'wb')
            f.write(header.encode('cp932', 'ignore'))
            f.write(lines.encode('cp932', 'ignore'))
            f.close()

            # 全チャンネルのcsvファイルに書き込み
            out_file_path = f"{output_dir}/ALL_CHANNEL_TALK_DATA.csv"
            f = open(out_file_path, 'ab')
            if(hasHeader == False):
                f.write(header.encode('cp932', 'ignore'))
                hasHeader = True
            f.write(lines.encode('cp932', 'ignore'))
            f.close()

        print(f'{len(channels)} channels converted.')

def make_template(out_file_path,output_mode='mysql'):
    if(os.path.exists(out_file_path) == False):
        f = open(out_file_path, 'w', encoding='utf-8')
        if(output_mode=='mysql'):
            f.write(mysql_template())
            f.close()
        elif(output_mode=='sqlite'):
            f.write(sqlite_template())
            f.close()
        else:
            f.close()

def mysql_template():
    return """
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
    """


def sqlite_template():
    return """
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
    """



if __name__ == '__main__':
    print('=======================================')
    print('JSON to CSV/SQL for Slack')
    print('v.1.0.8')
    print('=======================================')
    # 引数からソースフォルダ情報取得
    argv = sys.argv

    if len(argv) < 2:
        failed('Please add argument of zip file')
    if len(argv) == 2:
        timestamp_mode = ''
        output_mode = ''
        unzip_mode = ''
    if len(argv) == 3:
        timestamp_mode = argv[2]
        output_mode = ''
        unzip_mode = ''
    if len(argv) == 4:
        timestamp_mode = argv[2]
        output_mode = argv[3]
        unzip_mode = ''
    if len(argv) == 5:
        timestamp_mode = argv[2]
        output_mode = argv[3]
        unzip_mode = argv[4]

    source_file = argv[1]
    unzip_source_dir = os.path.splitext(source_file)[0]

    if(unzip_mode.lower() in UNZIP_MODE):
        is_not_zip = True
    else:
        is_not_zip = False

    if(is_not_zip):
        unzip_source_dir = source_file
    else:
        shutil.unpack_archive(source_file,unzip_source_dir)

    # テンプレートファイルがない場合は作る
    if(output_mode in OUTPUT_SQL_MODE):
        if(output_mode=='mysql'):
            make_template('slack_log_mysql_template.sql',output_mode)
        elif(output_mode=='sqlite'):
            make_template('slack_log_sqlite_template.sql',output_mode)

    convert_json_to_csv_for_slack(unzip_source_dir,timestamp_mode,output_mode)