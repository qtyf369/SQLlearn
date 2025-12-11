# add_client_id.py
from sqlalchemy import create_engine, text
from datetime import datetime, date
import warnings
warnings.filterwarnings("ignore")

# 配置项（不变）
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
MYSQL_DB = "client_db"
MYSQL_TABLE = "new_quote"

# 关键：引擎加 future=True（支持 mappings()）
engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}",
    pool_size=1,
    pool_recycle=3600,
    pool_pre_ping=True,
    future=True  # 启用2.0特性，支持 mappings()
)

# 日期转换函数（不变）
def convert_date_format(prefix, row_num, date_input):
    if not date_input:
        date_str = datetime.now().strftime("%Y%m%d")
    else:
        if isinstance(date_input, str):
            try:
                date_obj = datetime.strptime(date_input, "%Y-%m-%d")
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_input, "%Y%m%d")
                except ValueError:
                    date_obj = datetime.now()
            date_str = date_obj.strftime("%Y%m%d")
        elif isinstance(date_input, (datetime, date)):
            date_str = date_input.strftime("%Y%m%d")
        else:
            date_str = datetime.now().strftime("%Y%m%d")
    id_str = f"{prefix}{date_str}{str(row_num).zfill(3)}"
    return id_str

def generate_client_id():
    prefix = "KZ"
    success_count = 0
    fail_count = 0

    try:
        with engine.connect() as conn:
            # 1. 检查并新增 Id 列（不变）
            check_col_sql = text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = :db_name 
                  AND TABLE_NAME = :table_name 
                  AND COLUMN_NAME = 'Id';
            """)
            col_exists = conn.execute(check_col_sql, {
                "db_name": MYSQL_DB,
                "table_name": MYSQL_TABLE
            }).scalar()

            if col_exists == 0:
                add_col_sql = text(f"ALTER TABLE `{MYSQL_DB}`.`{MYSQL_TABLE}` ADD COLUMN `Id` VARCHAR(50) FIRST")
                conn.execute(add_col_sql)
                print("✅ 成功新增 Id 列")
            else:
                print("ℹ️ Id 列已存在")

            # 2. 有日期记录：fetchall() → mappings().all()（关键修改1）
            select_sql = text(f"""
                SELECT 
                    ROW_NUMBER() OVER (PARTITION BY `日期` ORDER BY `名字`) AS row_num,
                    `名字`, `国家`, `日期`
                FROM `{MYSQL_DB}`.`{MYSQL_TABLE}`
                WHERE `日期` IS NOT NULL;
            """)
            all_rows = conn.execute(select_sql).mappings().all()  # 这里改
            print(f"ℹ️ 查到 {len(all_rows)} 条有日期记录")

            for row in all_rows:
                try:
                    # 依然用 row["字段名"] 取值（不变）
                    row_num = row["row_num"]
                    customer_name = row["名字"]
                    country = row["国家"]
                    quote_date = row["日期"]
                    Id = convert_date_format(prefix, row_num, quote_date)
                    
                    update_sql = text(f"""
                        UPDATE `{MYSQL_DB}`.`{MYSQL_TABLE}`
                        SET `Id` = :Id
                        WHERE `名字` = :name AND `国家` = :country AND `日期` = :date;
                    """)
                    result = conn.execute(update_sql, {
                        "Id": Id,
                        "name": customer_name,
                        "country": country,
                        "date": quote_date
                    })
                    success_count += result.rowcount
                except Exception as e:
                    fail_count += 1
                    print(f"❌ 处理 {customer_name} 失败：{str(e)}")
                    continue

            # 3. 无日期记录：fetchall() → mappings().all()（关键修改2）
            no_date_sql = text(f"""
                SELECT 
                    ROW_NUMBER() OVER () AS row_num,
                    `名字`, `国家`
                FROM `{MYSQL_DB}`.`{MYSQL_TABLE}`
                WHERE `日期` IS NULL;
            """)
            no_date_rows = conn.execute(no_date_sql).mappings().all()  # 这里改
            print(f"ℹ️ 查到 {len(no_date_rows)} 条无日期记录")

            for row in no_date_rows:
                customer_name = "未知记录"
                try:
                    row_num = row["row_num"]
                    customer_name = row["名字"]
                    country = row["国家"]
                    Id = convert_date_format(prefix, row_num, None)
                    
                    update_sql = text(f"""
                        UPDATE `{MYSQL_DB}`.`{MYSQL_TABLE}`
                        SET `Id` = :Id
                        WHERE `名字` = :name AND `国家` = :country AND `日期` IS NULL;
                    """)
                    result = conn.execute(update_sql, {
                        "Id": Id,
                        "name": customer_name,
                        "country": country
                    })
                    success_count += result.rowcount
                except Exception as e:
                    fail_count += 1
                    print(f"❌ 处理无日期 {customer_name} 失败：{str(e)}")
                    continue
         # 先检查是否已有主键（避免重复设置报错）
            # 用 KEY_COLUMN_USAGE 表（存储约束和字段的关联关系），这个表有 COLUMN_NAME 字段
            check_pk_sql = text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = :db_name 
                  AND TABLE_NAME = :table_name 
                  AND CONSTRAINT_NAME = 'PRIMARY'  -- 主键的约束名默认是 'PRIMARY'
                  AND COLUMN_NAME = 'Id';
            """)
            pk_exists = conn.execute(check_pk_sql, {
                "db_name": MYSQL_DB,
                "table_name": MYSQL_TABLE
            }).scalar()

            if pk_exists == 0:
                # 设 Id 为主键（主键默认非空+唯一，已有数据满足）
                set_pk_sql = text(f"ALTER TABLE `{MYSQL_DB}`.`{MYSQL_TABLE}` ADD PRIMARY KEY (`Id`);")
                conn.execute(set_pk_sql)
                print("✅ 成功设置 Id 为主键")
            else:
                print("ℹ️ Id 已为主键，跳过设置")

            conn.commit()
            print(f"\n🎉 执行完成！成功 {success_count} 条，失败 {fail_count} 条")

    except Exception as e:
        print(f"\n❌ 全局失败：{str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        engine.dispose()
        print("🔌 连接已关闭")

if __name__ == "__main__":
    if input(f"⚠️ 修改 `{MYSQL_DB}`.`{MYSQL_TABLE}`，继续？(y/n)：").lower() == "y":
        generate_client_id()
    else:
        print("🚫 取消执行")