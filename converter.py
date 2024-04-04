#coding: UTF-8
from cgitb import text
import sys
import os
import glob
import json
import hashlib
from unziplib import unzip
import datetime

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
def get_line_text(users, item, channel):

    text = f'{item[TEXT_KEY]}'.replace('"', '\"').replace('"', '""')
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
        timestamp = standard_time.strftime("%Y-%m-%d %H:%M:%S")

    msg_id = ''
    if CLIENT_MSG_ID_KEY in item.keys():
        msg_id = item[CLIENT_MSG_ID_KEY]
    else:
        # msg_idが無い場合は作成する
        msg = timestamp+name+text+urls+channel
        msg_id = hashlib.sha256(msg.encode()).hexdigest()

    return f'"{timestamp}","{name}","{text}","{urls}","{msg_id}","{channel}"\n'

# 失敗手続き
def failed(text):
    print(f'[error] {text}')
    print('failed...')
    exit()


# core logics =====================

def convert_json_to_csv_for_slack(source_dir):

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

    users = get_users(f'{source_dir}/{USER_FILE_NAME}')

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

                lines += get_line_text(users, item, channel)

            print(f'\t{date} ({len(json_dic)})')

        # 変換した情報をチャンネル名のcsvファイルに書き込み
        out_file_path = f"{output_dir}/{channel}.csv"
        f = open(out_file_path, 'w')
        f.write(header)
        f.write(lines)
        f.close()

        # 全チャンネルのcsvファイルに書き込み
        out_file_path = f"{output_dir}/ALL_CHANNEL_TALK_DATA.csv"
        f = open(out_file_path, 'a')
        if(hasHeader == False):
            f.write(header)
            hasHeader = True
        f.write(lines)
        f.close()

    print(f'{len(channels)} channels converted.')

if __name__ == '__main__':
    # 引数からソースフォルダ情報取得
    argv = sys.argv

    if len(argv) < 2:
        failed('Please add argument of zip file')

    source_file = argv[1]
    unzip_source_dir = os.path.splitext(source_file)[0]

    unzip([source_file,unzip_source_dir])

    convert_json_to_csv_for_slack(unzip_source_dir)