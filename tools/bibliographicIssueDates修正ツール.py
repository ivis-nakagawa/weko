# -*- coding: utf-8 -*-
"""
bibliographicIssueDates の値を修正するツール
ログ例
* データベース名,テーブル名,{レコードID},アイテムタイプID,[削除対象の項目]
"""
import csv, json, psycopg2, sys, traceback, re
from os import getenv
from os.path import dirname, join

TARGET_LIST_FILENAME = 'db_list.tsv'
# ログ用変数
fix_flag = False
before_value = ""
after_value = ""
has_unexpected_value = False

def fix_value(value):
    # 正常な場合(データ取得時点で弾けているが...)
    if re.match(r'^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$', value):
        return False, value
    match = re.match(r'^\[(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?\]$', value)
    # 修正が必要な場合
    if match:
        result = ""
        year, month, day = match.groups()
        if year:
            result += year
        if month:
            if len(month) == 1:
                month = f"0{month}"
            result += f"-{month}"
        if day:
            if len(day) == 1:
                day = f"0{day}"
            result += f"-{day}"
        return True, result
    # 想定外の値の場合
    else:
        has_unexpected_value = True
        return False, value

def get_value(key, value):
    if isinstance(value, list):
        return [get_value(key, v) for v in value]
    elif isinstance(value, dict):
        return {k: get_value(key, v) for k, v in value.items()}
    elif key == "bibliographicIssueDates":
        before_value = value
        fix_flag, after_value = fix_value(value)
        return after_value
    return value

def get_db_list(filename):
    db_list = []
    with open(filename, "r") as f:
        reader = csv.reader(f, delimiter='\t')
        l = [row for row in reader]
        for ll in l:
            db_list.append(ll[0])
    return db_list

def get_connection(db_name):
    return psycopg2.connect(
        database=db_name,
        user=getenv('INVENIO_POSTGRESQL_DBUSER'),
        password=getenv('INVENIO_POSTGRESQL_DBPASS'),
        host=getenv('INVENIO_POSTGRESQL_HOST'),
        port=5432,
        connect_timeout=10
    )

def fix_form_title(db_list):
    try:
        for db_name in db_list:
            detection_logs = []
            with get_connection(db_name) as conn, conn.cursor() as cur:
                # for key in ['checkbox', 'radio', 'select']:
                cur.execute(
                    "SELECT id, json \
                    FROM records_metadata \
                    WHERE json::text LIKE '%%\"bibliographicIssueDates\": \"[%%' \
                    ORDER BY created;"
                )
                data = cur.fetchall()

                result = {}

                for record in data:
                    recid = ""
                    record_uuid = str(record[0])
                    json = record[1]

                    # bibliographicIssueDates の値を取得
                    for key, values in json.items():
                        if key == "recid":
                            recid = values
                            continue
                        a = get_value(key, values)
                        if fix_flag:
                            json[key] = a
                            detection_logs.append(f"{db_name},records_metadata,{{{recid}}},{before_value},{after_value}")
                            break
                        if has_unexpected_value:
                            detection_logs.append(f"Unexpected value found: {db_name},records_metadata,{{{recid}}},{before_value}")
                            break

                fix_flag = False
                before_value = ""
                after_value = ""
                has_unexpected_value = False

                for log in detection_logs:
                    print(log)
                # print(f"=====================================")
                # for key, value in missing_count.items():
                #     keys = sorted(value.keys(), key=int)
                #     for k in keys:
                #         print(f"{key}[{k}]\t: {value[k]}")
                # print(f"=====================================")

    except:
        print(f'has_unexpected_value: {traceback.print_exc()}')
        for log in detection_logs:
            print("rollback: "+log)

if __name__ == '__main__':
    #args = sys.argv

    #input_file_path = args[1] if len(args) == 2 else join(dirname(__file__), TARGET_LIST_FILENAME)
    #db_list = get_db_list(input_file_path)

    db_list = [getenv('INVENIO_POSTGRESQL_DBNAME')]

    fix_form_title(db_list)
