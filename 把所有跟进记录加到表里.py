from sqlalchemy import create_engine, text
from datetime import datetime, date
import warnings
warnings.filterwarnings("ignore")
from main import engine  # 从 main.py 导入引擎

def migrate_data_from_quote_to_follow():
    """从 new_quote 表迁移数据到 follow_up_record 表"""
    try:
        with engine.connect() as conn:
            # SQL 核心：INSERT INTO 目标表 (字段1, 字段2) SELECT 源表字段1, 源表字段2 FROM 源表
            # 示例：把 new_quote 中 Id=10 的客户的“跟进情况”迁移到 follow_up_record 表
            conn.execute(
                text("""
                    INSERT INTO follow_up_record (Id, 跟进时间, 跟进情况)
                    SELECT Id, 最近跟进日期, 跟进情况  -- 源表字段：Id 对应目标表 Id，跟进情况对应跟进情况
                    FROM new_quote
                     -- 条件：只迁移某个客户的数据（按需修改，比如去掉 WHERE 迁移所有）
                """)  # 要迁移的客户 ID（按需修改）
            )
            conn.commit()  # 提交事务
        print("数据迁移成功！")
    except Exception as e:
        print(f"迁移失败：{str(e)}")

if __name__ == "__main__":
    migrate_data_from_quote_to_follow() 
