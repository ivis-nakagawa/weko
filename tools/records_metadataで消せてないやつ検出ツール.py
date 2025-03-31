# -*- coding: utf-8 -*-
"""
item_type_edit_historyで削除されたが、
records_metadata及びitem_metadataでは削除されていないキーを検出するツール
ログ例
* データベース名,テーブル名,{レコードID},アイテムタイプID,[削除対象の項目]
"""
import csv, json, psycopg2, sys, traceback
from os import getenv
from os.path import dirname, join

TARGET_LIST_FILENAME = 'db_list.tsv'
# metadataには含まれるが、item_type_edit_historyには含まれないキー
IGNORE_KEYS = [
    '_buckets',
    '_deposit',
    '_oai',
    'author_link',
    'item_title',
    'item_type_id',
    'owner',
    'path',
    'pubdate',
    'publish_date',
    'publish_status',
    'recid',
    'relation_version_is_last',
    'title',
    'weko_shared_id',
    'control_number',
    'system_identifier_doi',
    '$schema',
    'edit_mode',
    'id',
    'pid',
    'lang',
    'shared_user_id',
    'created_by',
    'status',
    'owners',
    'owners_ext',
    'deleted_items',
    'feedback_mail_list',
    'either_valid_0',
]

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
                stmt_formats = ','.join(['%s'] * len(IGNORE_KEYS))
                cur.execute(
                    "SELECT item_type_id, string_agg(key, ',') as keys \
                    FROM ( \
                        SELECT item_type_id, jsonb_object_keys(notes::jsonb) as key \
                        FROM ( \
                            SELECT item_type_id, notes, ROW_NUMBER() OVER (PARTITION BY item_type_id ORDER BY id DESC) as rn \
                            FROM item_type_edit_history \
                        ) t \
                        WHERE rn = 1 \
                    ) k \
                    GROUP BY item_type_id;"
                )
                itemtypes = cur.fetchall()

                cur.execute(
                    "SELECT id, item_type_id, string_agg(key, ',') as keys \
                    FROM ( \
                        SELECT id, jsonb_extract_path_text(json, 'item_type_id') as item_type_id, s.key \
                        FROM records_metadata, jsonb_object_keys(json) s(key) \
                    ) k \
                    WHERE k.key NOT IN (%s) \
                    GROUP BY id, item_type_id"%stmt_formats, tuple(IGNORE_KEYS)
                )
                records = cur.fetchall()

                cur.execute(
                    "SELECT id, item_type_id, string_agg(key, ',') as keys \
                    FROM ( \
                        SELECT id, item_type_id, s.key \
                        FROM item_metadata, jsonb_object_keys(json) s(key) \
                    ) k \
                    WHERE k.key NOT IN (%s) \
                    GROUP BY id, item_type_id"%stmt_formats, tuple(IGNORE_KEYS)
                )
                items = cur.fetchall()

                itemtypes_dict = {}
                for itemtype in itemtypes:
                    itemtype_id = str(itemtype[0])
                    itemtypes_dict[itemtype_id] = itemtype[1].split(',')

                data = {"records_metadata": records, "item_metadata": items}
                missing_count = {}
                for table_name, records in data.items():
                    missing_count[table_name] = missing_count.get(table_name, {})
                    for record in records:
                        missing_keys = []
                        record_id = record[0]
                        itemtype_id = str(record[1])
                        record_keys = record[2].split(',')
                        itemtype_keys = itemtypes_dict.get(itemtype_id, [])
                        # itemtypeに存在しないキーを取得
                        missing_keys = list(set(record_keys) - set(itemtype_keys))
                        if missing_keys:
                            # データベース名,テーブル名,{レコードID},アイテムタイプID,[削除対象の項目]
                            detection_logs.append(f"{db_name},{table_name},{{{record_id}}},{itemtype_id},[{','.join(missing_keys)}]")
                            missing_count[table_name][itemtype_id] = missing_count[table_name].get(itemtype_id, 0) + 1

                for log in detection_logs:
                    print(log)
                print(f"=====================================")
                for key, value in missing_count.items():
                    keys = sorted(value.keys(), key=int)
                    for k in keys:
                        print(f"{key}[{k}]\t: {value[k]}")
                print(f"=====================================")

    except:
        print(f'ERROR: {traceback.print_exc()}')
        for log in detection_logs:
            print("rollback: "+log)

if __name__ == '__main__':
    #args = sys.argv

    #input_file_path = args[1] if len(args) == 2 else join(dirname(__file__), TARGET_LIST_FILENAME)
    #db_list = get_db_list(input_file_path)

    db_list = [getenv('INVENIO_POSTGRESQL_DBNAME')]

    fix_form_title(db_list)
