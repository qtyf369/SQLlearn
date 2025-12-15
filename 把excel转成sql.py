# 1. 处理 Excel 数据的核心库
import pandas as pd
# 2. 连接 MySQL 数据库的核心库
from sqlalchemy import create_engine, text
# 3. 处理 MySQL 连接可能出现的错误（可选，但建议加）
import pymysql
pymysql.install_as_MySQLdb() #伪装成MySQLdb模块，好像新版的sqlalchemy已经支持pymysql了
from sqlalchemy.types import DATE 

# ---------------------- 请修改成你的 MySQL 信息 ----------------------
MYSQL_USER = "root"        # 你的 MySQL 用户名（默认通常是 root）
MYSQL_PASSWORD = "123456"  # 你的 MySQL 密码（安装时设置的，比如 123456）
MYSQL_HOST = "localhost"   # MySQL 主机地址（本地运行默认是 localhost，不用改）
MYSQL_NEW_DB = "client_db"  # 要新建的数据库名（比如叫“新学生数据库”，自定义）
# ----------------------------------------------------------------------

# 其他固定配置（不用改）
EXCEL_FILE_PATH = "客户跟进表-新询盘更新12月5日 - 副本.xlsx"  # 你的 Excel 文件路径（比如放在桌面就写完整路径）
EXCEL_SHEET_NAME = "新询盘"  # 你 Excel 里改过名字的工作表名（比如“高三学生信息”）
SQL_TABLE_NAME = "new_quote"   # 要在 MySQL 里新建的表名（自定义，比如“学生信息表”）

def create_mysql_engine():
    try:
        # 1. 先创建一个“连接到 MySQL 服务器”的引擎（不是具体数据库，因为新数据库还没创建）
        engine_root = create_engine(
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/?charset=utf8mb4",
            echo=False  # echo=True 会打印执行的 SQL 语句，新手可以设为 True 看过程
        )
        
        # 2. 连接 MySQL 服务器，创建新数据库
        with engine_root.connect() as conn:
            # 执行 SQL：创建新数据库（如果不存在）
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_NEW_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            print(f"✅ 新数据库 {MYSQL_NEW_DB} 创建成功（如果已存在则跳过）")
        
        # 3. 再创建一个“连接到新数据库”的引擎（后续写入数据用这个）
        engine = create_engine(
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_NEW_DB}?charset=utf8mb4",
            echo=False
        )
        return engine  # 返回这个“连接新数据库”的引擎
    
    except Exception as e:
        print(f"❌ 数据库连接/创建失败：{str(e)}")
        return None

# 调用函数，创建引擎（这一步会实际执行数据库创建）
engine = create_mysql_engine()

# 检查引擎是否创建成功（失败则退出）
if engine is None:
    exit("数据库连接失败，程序退出")

def read_excel_data(file_path, sheet_name):
    try:
        # 1. 读取 Excel 数据（关键参数：指定工作表、第一行作为列名）
        df = pd.read_excel(
            io=file_path,          # Excel 文件路径（咱们第二步配置的 EXCEL_FILE_PATH）
            sheet_name=sheet_name, # 要读取的工作表名（第二步配置的 EXCEL_SHEET_NAME）
            header=0,              # 第 0 行（第一行）作为 DataFrame 的列名（对应后续 SQL 字段名）
            skiprows=0,            # 跳过前 0 行（如果 Excel 前几行是标题/注释，可改成 1 或 2）
            na_filter=False,       # 不自动把空单元格替换成 NaN（保留原始空值，后续写入 SQL 为 NULL）
            dtype=str              # 先统一按字符串读取（避免数字/日期自动转错类型，后续再调整）
        )
        
        # 2. 数据校验：确保读取到数据，且有列名
        if df.empty:
            raise ValueError("❌ Excel 工作表为空，没有可读取的数据")
        if len(df.columns) == 0:
            raise ValueError("❌ 未读取到列名，请检查 Excel 第一行是否为表头（字段名）")
        
        # 3. 打印读取结果（让你直观看到读了多少数据、列名是什么）
        print(f"✅ Excel 数据读取成功！")
        print(f"📊 数据概况：共 {len(df)} 行数据，{len(df.columns)} 列字段")
        print(f"🏷️  列名（对应后续 SQL 字段名）：{list(df.columns)}")
        print(f"👀 前 2 行数据预览：")
        print(df.head(2))  # 打印前 2 行，确认数据格式正确
        
        return df
    
    except FileNotFoundError:
        print(f"❌ 找不到 Excel 文件：{file_path}")
        return None
    except ValueError as ve:
        print(f"❌ 数据读取错误：{str(ve)}")
        return None
    except Exception as e:
        print(f"❌ Excel 读取失败：{str(e)}")
        return None

# 调用函数，读取 Excel 数据（用第二步配置的路径和工作表名）
df = read_excel_data(EXCEL_FILE_PATH, EXCEL_SHEET_NAME)
# 检查是否读取成功（失败则退出）
if df is None:
    exit("Excel 数据读取失败，程序退出")
#关键步骤：把 Excel 日期序列号（字符串）转成标准日期
def excel_serial_to_date(serial_str):
    """把 Excel 日期序列号字符串（如 '45913'）转成 datetime 类型"""
    try:
        # 空值/空白字符串直接返回 NaT（无效日期）
        if pd.isna(serial_str) or serial_str.strip() == '':
            return pd.NaT
        # 把字符串转成数字（序列号），再转成日期（origin='1900-01-01' 是 Excel 起始日期）
        serial_num = float(serial_str)
        # Excel 有个闰年 bug，需要减 2（否则会多算 2 天）
        return pd.to_datetime('1900-01-01') + pd.Timedelta(days=serial_num - 2)
    except:
        # 如果不是序列号（比如已经是 '2025-01-08' 格式），直接尝试转日期
        return pd.to_datetime(serial_str, errors='coerce')

# 应用到日期列（修改列名和你的 df 一致）
df['日期'] = df['日期'].apply(excel_serial_to_date)
df['最近跟进日期'] = df['最近跟进日期'].apply(excel_serial_to_date)




try:
    df.to_sql(
        name=SQL_TABLE_NAME,
        con=engine,
        if_exists="replace",
        index=False,
        dtype={
            '日期': DATE,
            '最近跟进日期': DATE
        }  # dtype 字典单独一行，闭合清晰
    )  # df.to_sql() 闭合括号单独一行
    print(f"✅ 数据写入 SQL 成功！表名：{SQL_TABLE_NAME}，共 {len(df)} 行数据")
except Exception as e:
    print(f"❌ 数据写入 SQL 失败：{str(e)}")

