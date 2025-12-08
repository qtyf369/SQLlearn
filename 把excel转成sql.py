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

#可视化界面
# 优化后的导入（合并成一行，新增组件直接加在后面）
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox,
    QComboBox, QDateEdit  # 新增的高频组件
)
from PyQt5.QtCore import Qt

class ClientInfoApp(QMainWindow):
    def __init__(self):
        super().__init__()  # 继承 QMainWindow 的所有功能
        self.init_ui()  # 初始化界面（后面写这个方法）
        self.create_table()  # 创建学生表（后面写这个方法）
        self.load_data()  # 加载数据（后面写这个方法）
    
    # 把这段代码写在 ClientInfoApp 类里（紧跟在 __init__ 方法后面）
    def init_ui(self):
        # 1. 设置窗口标题和大小
        self.setWindowTitle("客户信息录入工具（MySQL版）")  # 窗口标题  
        self.setGeometry(300, 300, 1200, 900)  # 窗口位置（100,100）和大小（800宽×600高）

        # 2. 创建中心部件和布局（PyQt5 必须用布局管理组件，否则界面会乱）
        central_widget = QWidget()  # 中心部件（所有内容都放在这个“容器”里）
        self.setCentralWidget(central_widget)  # 把中心部件设为主窗口的核心
        main_layout = QVBoxLayout(central_widget)  # 垂直布局：组件从上到下排列（上方录入区+下方表格区）

        # ---------------------- 上方：录入区域（标签+输入框+按钮）----------------------
        input_layout = QHBoxLayout()  # 水平布局：组件从左到右排列（标签和输入框并排）

        # （1）询盘日期输入框
        self.date_label = QLabel("询盘日期：")  # 标签（提示用户输入什么）
        self.date_input = QDateEdit()  # 输入框（用户输入学号）
        self.date_input.setCalendarPopup(True)  # 点击输入框弹出日期选择器
        self.date_input.setDisplayFormat("yyyy-MM-dd")  # 显示格式为 "年-月-日"
        input_layout.addWidget(self.date_label)  # 把标签加入水平布局
        input_layout.addWidget(self.date_input)  # 把输入框加入水平布局

        # （2）姓名输入框
        self.name_label = QLabel("姓名：")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入学生姓名")
        input_layout.addWidget(self.name_label)
        input_layout.addWidget(self.name_input)

        # （3）年龄输入框
        self.age_label = QLabel("年龄：")
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("例如：18")
        input_layout.addWidget(self.age_label)
        input_layout.addWidget(self.age_input)

        # （4）班级输入框
        self.class_label = QLabel("班级：")
        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("例如：高三(1)班")
        input_layout.addWidget(self.class_label)
        input_layout.addWidget(self.class_input)

        # （5）提交按钮
        self.submit_btn = QPushButton("提交信息")  # 按钮
        self.submit_btn.clicked.connect(self.submit_student)  # 按钮绑定点击事件（点按钮就执行 submit_student 方法）
        input_layout.addWidget(self.submit_btn)
        # （6）手动刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_data)  # 按钮绑定点击事件（点按钮就执行 load_data 方法）
        input_layout.addWidget(self.refresh_btn)
        
        # 把录入区域加入主布局（垂直布局的上方）
        main_layout.addLayout(input_layout)

        # ---------------------- 下方：表格区域（显示学生信息）----------------------
        self.table = QTableWidget()  # 创建表格
        self.table.setColumnCount(4)  # 表格有4列（学号、姓名、年龄、班级）
        self.table.setHorizontalHeaderLabels(["学号", "姓名", "年龄", "班级"])  # 表格列标题

        # 表格自适应列宽（让列宽跟着窗口大小变，更美观）
        self.table.horizontalHeader().setStretchLastSection(True)
        for i in range(4):
            self.table.horizontalHeader().setSectionResizeMode(i, 1)

        # 把表格加入主布局（垂直布局的下方）
        main_layout.addWidget(self.table)        

    # 把这段代码写在 StudentInfoApp 类里（紧跟在 init_ui 方法后面）
    def create_table(self):
        try:
            with engine.connect() as conn:
                check_sql = text("""
                SELECT TABLE_NAME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = :db_name  -- 数据库名（student_db）
                  AND TABLE_NAME = :table_name  -- 表名（student_info）
            """)
            # 传递参数（避免 SQL 注入，更规范）
                result = conn.execute(
                    check_sql,
                    {"db_name": MYSQL_DB, "table_name": "student_info"}
            ).fetchone()  # fetchone()：有结果返回表名，无结果返回 None

                # 1. 定义SQL语句（确保格式正确，无多余符号）
            if result is None:   
                create_sql = """
    CREATE TABLE IF NOT EXISTS student_info (
    学号 CHAR(4) PRIMARY KEY,
    姓名 VARCHAR(20) NOT NULL,
    年龄 INT NOT NULL,
    班级 VARCHAR(20) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
                # 2. 用 text() 包装SQL，转为可执行对象
                conn.execute(text(create_sql.strip()))
                conn.commit()
                QMessageBox.information(self, "建表成功", "student_info表创建成功！")
        except Exception as e:
            QMessageBox.critical(self, "建表失败", f"建表失败原因：{str(e)}")
    # 写在 create_table 方法后面，StudentInfoApp 类里
    def load_data(self):
        try:
            # 用 text() 包装查询SQL
            self.df = pd.read_sql(text("SELECT * FROM student_info"), engine)
            self.update_table()
        except Exception as e:
            self.df = pd.DataFrame(columns=["学号", "姓名", "年龄", "班级"])
            QMessageBox.warning(self, "加载提示", f"暂无学生数据：{str(e)}")
            # 写在 load_data 方法后面，StudentInfoApp 类里
    def update_table(self):
        # 1. 清空表格里已有的数据（避免重复显示）
        self.table.setRowCount(0)
        
        # 2. 遍历 self.df（从 MySQL 读到的数据），逐行添加到表格
        for row_idx, row in self.df.iterrows():
            # 插入一行（行号是 row_idx）
            self.table.insertRow(row_idx)
            
            # 给每一列赋值（4列：学号、姓名、年龄、班级）
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["学号"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["姓名"]))
            # 年龄是 INT 类型，转成字符串才能显示
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row["年龄"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row["班级"]))
            
            # 3. 让表格内容居中对齐（更美观）
            for col in range(4):
                self.table.item(row_idx, col).setTextAlignment(Qt.AlignCenter)
# 写在 update_table 方法后面，StudentInfoApp 类里
    def submit_student(self):
        # 1. 获取输入框里的内容（strip() 去掉前后空格，避免输入空字符）
        student_id = self.id_input.text().strip()
        name = self.name_input.text().strip()
        age = self.age_input.text().strip()
        class_name = self.class_input.text().strip()
        
        # 2. 数据校验（避免无效数据存入 MySQL）
        # 校验1：所有字段不能为空
        if not all([student_id, name, age, class_name]):
            QMessageBox.warning(self, "输入错误", "所有字段不能为空！")
            return  # 直接返回，不执行后续操作
        
        # 校验2：学号必须是4位数字（和 MySQL 表的 CHAR(4) 对应）
        if not student_id.isdigit() or len(student_id) != 4:
            QMessageBox.warning(self, "格式错误", "学号必须是4位数字（例如：0001）！")
            return
        
        # 校验3：年龄必须是6-30之间的整数（合理范围）
        if not age.isdigit():
            QMessageBox.warning(self, "格式错误", "年龄必须是整数！")
            return
        age_int = int(age)
        if age_int < 6 or age_int > 30:
            QMessageBox.warning(self, "范围错误", "年龄必须在6-30之间！")
            return
        
        # 3. 把输入的信息整理成 DataFrame（方便 pandas 写入 MySQL）
        new_data = pd.DataFrame({
            "学号": [student_id],
            "姓名": [name],
            "年龄": [age_int],  # 转成整数，匹配 MySQL 的 INT 类型
            "班级": [class_name]
        })
        
        # 4. 把数据写入 MySQL
        try:
            # df.to_sql() 本质是执行 SQL：INSERT INTO student_info (...) VALUES (...)
            new_data.to_sql(
                name="student_info",  # 要写入的表名
                con=engine,           # 连接通道
                if_exists="append",   # 追加数据（不覆盖已有数据）
                index=False           # 不把 DataFrame 的索引写入 MySQL（避免多一列）
            )
            
            # 5. 写入成功后，提示用户
            QMessageBox.information(self, "成功", "学生信息录入成功！")
            
            # 6. 重新加载数据，更新表格（让新数据显示在表格里）
            self.load_data()
            
            # 7. 清空输入框，方便下次录入
            self.id_input.clear()
            self.name_input.clear()
            self.age_input.clear()
            self.class_input.clear()
        
        except pymysql.IntegrityError:
            # 捕获主键冲突（学号重复，因为 MySQL 表的学号是 PRIMARY KEY）
            QMessageBox.warning(self, "重复录入", f"学号{student_id}已存在，请勿重复提交！")
        except Exception as e:
            # 其他错误（比如连接失败）
            QMessageBox.error(self, "提交失败", f"录入失败：{str(e)}")

                 


# 7. 程序入口（固定写法，让程序能运行起来）
if __name__ == "__main__":
    app = QApplication(sys.argv)  # 创建应用实例
    window = StudentInfoApp()     # 创建主窗口
    window.show()                 # 显示窗口
    sys.exit(app.exec_())         # 让程序持续运行
# 最后，关闭数据库连接（好习惯，释放资源）
engine.dispose()
