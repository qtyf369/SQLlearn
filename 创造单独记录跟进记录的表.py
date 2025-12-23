import sqlite3
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")
# 这个脚本会把new_quote表中的所有跟进记录都加到follow_up_record表中
# 跟进记录的格式为：跟进时间+跟进情况+客户名称+国家



# ===================== SQLite 配置（直接指定数据库路径）=====================
SQLITE_DB_PATH = "crm.db"  # 你的 CRM 数据库文件路径（与 new_quote 表所在数据库一致）
SOURCE_TABLE = "new_quote"  # 源表名
TARGET_TABLE = "follow_up_record"  # 目标表名

def migrate_data_from_quote_to_follow():
    """从 new_quote 表迁移数据到 follow_up_record 表（纯 SQLite 实现，无 engine）"""
    conn = None
    try:
        # 1. 连接 SQLite 数据库（内置模块，无需额外依赖）
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        print(f"✅ 成功连接 SQLite 数据库：{SQLITE_DB_PATH}")

        # 2. 可选：如果目标表 follow_up_record 未创建，先自动创建（取消注释即可启用）
        # 按需调整字段和类型（SQLite 字段类型可灵活设置）
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TARGET_TABLE} (
                Id TEXT NOT NULL,  -- 与源表 new_quote 的 Id 关联（外键）
                跟进时间 TEXT,     -- 存储日期字符串（YYYY-MM-DD 或 YYYYMMDD）
                跟进情况 TEXT,     -- 跟进内容
                -- 外键约束：确保 Id 对应源表的有效记录（需源表 new_quote.Id 是主键）
                FOREIGN KEY (Id) REFERENCES {SOURCE_TABLE}(Id)
            );
        """)
        print(f"ℹ️ 确保目标表 {TARGET_TABLE} 已存在（无则自动创建）")

        # 3. 核心迁移逻辑（SQLite 原生语法，无兼容性问题）
        migrate_sql = f"""
            INSERT INTO {TARGET_TABLE} (Id, 跟进时间, 跟进情况)
            SELECT 
                Id,                -- 源表：客户唯一标识（关联字段）
                最近跟进日期,      -- 源表：跟进日期字段（按需替换为你的实际字段名）
                跟进情况         -- 源表：跟进内容字段（按需替换）
            FROM {SOURCE_TABLE}
            -- 筛选条件：只迁移有价值的数据（按需调整或删除 WHERE 迁移所有）
            WHERE 
               
                最近跟进日期 IS NOT NULL AND 最近跟进日期 != ''  -- 排除空跟进日期
            -- 去重：避免重复迁移（支持脚本多次运行）
            AND Id NOT IN (SELECT Id FROM {TARGET_TABLE});
        """

        # 执行迁移并获取影响行数
        cursor.execute(migrate_sql)
        migrated_count = cursor.rowcount  # 迁移的记录数

        # 4. 提交事务（SQLite 必须提交，否则数据不生效）
        conn.commit()

        # 输出结果
        print(f"\n🎉 数据迁移成功！")
        print(f"📊 源表：{SOURCE_TABLE} → 目标表：{TARGET_TABLE}")
        print(f"📈 共迁移 {migrated_count} 条记录")
        if migrated_count == 0:
            print("ℹ️ 无新数据可迁移（可能已迁移过，或无符合条件的记录）")

    except Exception as e:
        print(f"\n❌ 迁移失败：{str(e)}")
        # 打印详细错误栈（便于排查字段名、表名错误）
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()  # 错误时回滚事务
    finally:
        # 关闭数据库连接（必须执行）
        if conn:
            conn.close()
            print("\n🔌 数据库连接已关闭")

if __name__ == "__main__":
    # 确认执行（避免误操作）
    confirm = input(f"⚠️ 即将执行数据迁移：\n源表：{SOURCE_TABLE}\n目标表：{TARGET_TABLE}\n数据库：{SQLITE_DB_PATH}\n是否继续？(y/n)：").lower()
    if confirm == "y":
        migrate_data_from_quote_to_follow()
    else:
        print("🚫 取消执行")