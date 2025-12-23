# add_client_id_sqlite.py
import sqlite3
from datetime import datetime, date
import warnings
warnings.filterwarnings("ignore")
#这个脚本会在数据库中添加一个ID列，ID列的格式为：前缀+8位日期（无时间）+3位序号，前缀可以自定义，如果已经有ID列，会删掉那一列，重新弄一列
# 例如：Q20251222001

# 配置项（SQLite 只需数据库文件路径）
SQLITE_DB_PATH = "crm.db"  # 和 CRM 工具共用的数据库文件
SQLITE_TABLE = "new_quote"  # 目标表名（与 CRM 表一致）

# 日期转换函数（强化：只保留日期，绝对无时间）
def convert_date_format(prefix, row_num, date_input):
    # 强制优先使用传入的询盘日期（只取日期部分，无时间）
    if date_input and date_input.strip():
        if isinstance(date_input, str):
            # 清理日期字符串（去掉可能的时间部分，只保留前10位）
            date_str_clean = date_input.strip().split(" ")[0]  # 分割空格，取日期部分（如 "2025-12-22 14:30" → "2025-12-22"）
            try:
                # 兼容两种核心日期格式，只取日期部分
                date_obj = datetime.strptime(date_str_clean, "%Y-%m-%d")
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_str_clean, "%Y%m%d")
                except ValueError:
                    print(f"⚠️ 日期格式错误：{date_input}，自动使用今天日期")
                    date_obj = datetime.now()
            # 只保留 8 位日期（无时间）
            date_str = date_obj.strftime("%Y%m%d")
        elif isinstance(date_input, (datetime, date)):
            # 直接取日期部分，忽略时间
            date_str = date_input.strftime("%Y%m%d")
        else:
            # 其他类型转字符串后取日期部分
            date_str = str(date_input).split(" ")[0].replace("-", "")[:8]
            # 若转换后不是8位，用今天日期兜底
            if len(date_str) != 8:
                date_str = datetime.now().strftime("%Y%m%d")
    else:
        # 无日期记录：用今天日期（只取日期，无时间）
        date_str = datetime.now().strftime("%Y%m%d")
    
    # 生成 ID：前缀+8位日期（无时间）+3位序号
    id_str = f"{prefix}{date_str}{str(row_num).zfill(3)}"
    return id_str

def drop_existing_id_column(cursor, table_name):
    """删除已存在的 Id 列（如果有），处理主键情况"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    if "Id" in columns:
        # 检查 Id 列是否为主键
        cursor.execute(f"PRAGMA table_info({table_name})")
        pk_column = [col[1] for col in cursor.fetchall() if col[5] == 1]
        if "Id" in pk_column:
            print("ℹ️ 发现 Id 列已为主键，需先通过临时表移除")
            # 获取原表所有字段（排除 Id 列）
            cursor.execute(f"PRAGMA table_info({table_name})")
            table_fields = [col[1] for col in cursor.fetchall() if col[1] != "Id"]
            fields_str = ", ".join([f"`{field}`" for field in table_fields])
            
            # 创建临时表→复制数据→删除原表→重命名
            temp_table = f"{table_name}_temp_drop"
            cursor.execute(f"CREATE TABLE {temp_table} ({fields_str});")
            cursor.execute(f"INSERT INTO {temp_table} SELECT {fields_str} FROM {table_name};")
            cursor.execute(f"DROP TABLE {table_name};")
            cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name};")
            print("✅ 已删除含主键的 Id 列")
        else:
            cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN Id;")
            print("✅ 已删除普通 Id 列")
        return True
    else:
        print("ℹ️ 未找到 Id 列，无需删除")
        return False

def ensure_id_first_column(cursor, table_name):
    """强制确保 Id 列在第一列（通过临时表重建表结构）"""
    # 检查当前 Id 列的位置（col[0] 是字段索引，0 为第一列）
    cursor.execute(f"PRAGMA table_info({table_name})")
    id_column = [col for col in cursor.fetchall() if col[1] == "Id"]
    if not id_column:
        print("❌ 未找到 Id 列，无法调整位置")
        return False
    
    id_index = id_column[0][0]
    if id_index == 0:
        print("ℹ️ Id 列已在第一列，无需调整")
        return True
    
    # 需调整：通过临时表重建，将 Id 列放在第一列
    print(f"ℹ️ Id 列当前在第 {id_index+1} 列，开始调整到第一列...")
    # 获取所有字段：Id 列放在最前面，其他字段紧随其后
    cursor.execute(f"PRAGMA table_info({table_name})")
    all_fields = [col[1] for col in cursor.fetchall()]
    new_fields_order = ["Id"] + [field for field in all_fields if field != "Id"]
    fields_str = ", ".join([f"`{field}`" for field in new_fields_order])
    
    # 创建临时表（按新字段顺序，Id 在第一列）
    temp_table = f"{table_name}_temp_reorder"
    create_temp_sql = f"CREATE TABLE {temp_table} ({fields_str});"
    cursor.execute(create_temp_sql)
    
    # 复制数据（按新字段顺序）
    insert_temp_sql = f"INSERT INTO {temp_table} SELECT {fields_str} FROM {table_name};"
    cursor.execute(insert_temp_sql)
    
    # 删除原表+重命名临时表
    cursor.execute(f"DROP TABLE {table_name};")
    cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name};")
    print("✅ 已强制将 Id 列调整到第一列")
    return True

def generate_client_id():
    prefix = "KZ"  # ID 前缀（可自定义）
    success_count = 0
    fail_count = 0
    no_date_start_num = 900  # 无日期记录序号起始值（避开有日期记录的 001-899）

    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        print(f"✅ 成功连接 SQLite 数据库：{SQLITE_DB_PATH}")

        # 步骤1：彻底删除原有 Id 列（清除错误数据）
        drop_existing_id_column(cursor, SQLITE_TABLE)
        conn.commit()

        # 步骤2：创建 Id 列（先添加，后续强制调整到第一列）
        cursor.execute(f"ALTER TABLE {SQLITE_TABLE} ADD COLUMN Id TEXT;")
        conn.commit()
        print("✅ 新增 Id 列")

        # 步骤3：强制将 Id 列调整到第一列（关键修复）
        ensure_id_first_column(cursor, SQLITE_TABLE)
        conn.commit()

        # 步骤4：处理有日期记录（核心：用询盘日期，序号 001-899，只含日期无时间）
        cursor.execute(f"""
            SELECT DISTINCT `日期` 
            FROM {SQLITE_TABLE} 
            WHERE `日期` IS NOT NULL AND `日期` != '' 
            ORDER BY `日期`;
        """)
        dates = [row[0] for row in cursor.fetchall()]
        print(f"ℹ️ 查到 {len(dates)} 个不同的询盘日期，开始处理有日期记录...")

        for date_val in dates:
            # 按「名字+国家+ROWID」排序，确保顺序唯一
            cursor.execute(f"""
                SELECT ROWID, `名字`, `国家`
                FROM {SQLITE_TABLE}
                WHERE `日期` = ?
                ORDER BY `名字`, `国家`, ROWID;
            """, (date_val,))
            date_records = cursor.fetchall()
            print(f"  - 询盘日期 {date_val}：{len(date_records)} 条记录")

            # 序号从 1 开始，最多到 899（避免和无日期记录重叠）
            for idx, record in enumerate(date_records, start=1):
                if idx > 899:
                    print(f"    ⚠️ 日期 {date_val} 记录数超过 899 条，序号将超过 3 位（不影响唯一性）")
                try:
                    rowid = record[0]
                    customer_name = record[1]
                    country = record[2]
                    # 生成 ID（只含日期，无时间）
                    client_id = convert_date_format(prefix, idx, date_val)
                    
                    # 精准更新
                    cursor.execute(f"UPDATE {SQLITE_TABLE} SET Id = ? WHERE ROWID = ?;", (client_id, rowid))
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    print(f"    ❌ 处理记录 [{customer_name}-{country}] 失败：{str(e)}")
                    continue

        # 步骤5：处理无日期记录（用今天日期，序号 900+，只含日期无时间）
        cursor.execute(f"""
            SELECT ROWID, `名字`, `国家`
            FROM {SQLITE_TABLE}
            WHERE `日期` IS NULL OR `日期` = ''
            ORDER BY `名字`, `国家`, ROWID;
        """)
        no_date_records = cursor.fetchall()
        today_date = datetime.now().strftime("%Y%m%d")
        print(f"ℹ️ 查到 {len(no_date_records)} 条无日期记录，用今天日期 {today_date}（无时间），序号从 {no_date_start_num} 开始...")

        for idx, record in enumerate(no_date_records, start=no_date_start_num):
            try:
                rowid = record[0]
                customer_name = record[1]
                country = record[2]
                # 生成 ID（只含日期，无时间）
                client_id = convert_date_format(prefix, idx, None)
                
                # 精准更新
                cursor.execute(f"UPDATE {SQLITE_TABLE} SET Id = ? WHERE ROWID = ?;", (client_id, rowid))
                success_count += 1
            except Exception as e:
                fail_count += 1
                print(f"  ❌ 处理无日期记录 [{customer_name}-{country}] 失败：{str(e)}")
                continue

        # 步骤6：最终验证 Id 唯一性和格式
        cursor.execute(f"""
            SELECT Id, COUNT(*) 
            FROM {SQLITE_TABLE} 
            GROUP BY Id 
            HAVING COUNT(*) > 1;
        """)
        duplicate_ids = cursor.fetchall()
        if duplicate_ids:
            print(f"\n⚠️ 发现 {len(duplicate_ids)} 个重复 Id（异常）：")
            for dup_id, count in duplicate_ids:
                print(f"  - {dup_id}：重复 {count} 次")
            print("❌ 存在重复 Id，请检查是否有同一日期下记录数超过 999 条")
        else:
            # 检查 Id 列是否有空白值
            cursor.execute(f"SELECT COUNT(*) FROM {SQLITE_TABLE} WHERE Id IS NULL OR Id = '';")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                print(f"\n⚠️ 发现 {null_count} 条记录的 Id 为空，无法设置主键！")
            else:
                # 检查 Id 格式（确保是 前缀+8位日期+3位序号，共 2+8+3=13 位）
                cursor.execute(f"SELECT Id FROM {SQLITE_TABLE} LIMIT 1;")
                sample_id = cursor.fetchone()[0]
                if len(sample_id) == 13 and sample_id.startswith(prefix):
                    print(f"\n✅ ID 格式验证通过：{sample_id}（前缀+8位日期+3位序号，无时间）")
                else:
                    print(f"\n⚠️ ID 格式异常：{sample_id}（应为 前缀+8位日期+3位序号）")
                
                # 设置 Id 为主键（确保后续操作唯一）
                cursor.execute(f"PRAGMA table_info({SQLITE_TABLE})")
                pk_column = [col[1] for col in cursor.fetchall() if col[5] == 1]
                if "Id" not in pk_column:
                    print("\nℹ️ 开始设置 Id 为主键...")
                    # 获取所有字段（Id 已在第一列）
                    cursor.execute(f"PRAGMA table_info({SQLITE_TABLE})")
                    table_fields = [col[1] for col in cursor.fetchall()]
                    fields_str = ", ".join([f"`{field}`" for field in table_fields])
                    
                    # 临时表方案设置主键
                    temp_table = f"{SQLITE_TABLE}_temp_pk"
                    create_temp_sql = f"""
                        CREATE TABLE {temp_table} (
                            {fields_str},
                            PRIMARY KEY (Id)
                        );
                    """
                    cursor.execute(create_temp_sql)
                    cursor.execute(f"INSERT INTO {temp_table} SELECT {fields_str} FROM {SQLITE_TABLE};")
                    cursor.execute(f"DROP TABLE {SQLITE_TABLE};")
                    cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {SQLITE_TABLE};")
                    conn.commit()
                    
                    # 最终验证 Id 列位置
                    cursor.execute(f"PRAGMA table_info({SQLITE_TABLE})")
                    id_position = [col[0] for col in cursor.fetchall() if col[1] == "Id"][0] + 1
                    print(f"✅ 主键设置完成！Id 列最终状态：")
                    print(f"  - 位置：第 {id_position} 列（确保为第一列）")
                    print(f"  - 格式：{prefix}+8位日期（无时间）+3位序号（示例：KZ20251222001）")
                    print(f"  - 唯一性：同一日期内序号唯一，无日期记录序号 900+ 不重叠")
                else:
                    print("\nℹ️ Id 已为主键，跳过设置")

        # 最终提交
        conn.commit()
        print(f"\n🎉 执行完成！成功更新 {success_count} 条记录，失败 {fail_count} 条")

    except Exception as e:
        print(f"\n❌ 全局执行失败：{str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 数据库连接已关闭")

if __name__ == "__main__":
    # 明确提示执行内容，避免误操作
    confirm = input(f"⚠️ 即将执行：\n1. 删除原有 Id 列（含主键）\n2. 新增 Id 列并强制调整到第一列\n3. 有日期记录：用询盘日期（无时间）+序号 001-899\n4. 无日期记录：用今天日期（无时间）+序号 900+\n5. 验证 ID 格式+设置为主键\n是否继续？(y/n)：").lower()
    if confirm == "y":
        generate_client_id()
    else:
        print("🚫 取消执行")