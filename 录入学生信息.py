# 1. 导入系统相关库（用于程序入口）
import sys
# 2. 导入 PyQt5 相关库（用于做可视化界面）
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
# 3. 导入数据处理和 MySQL 相关库
import pandas as pd
import pymysql
from sqlalchemy import create_engine, text  # 新增 text 函数

# 4. MySQL 连接配置（必须改成你的真实信息！）
MYSQL_HOST = "localhost"       # 本地 MySQL 地址（默认都是 localhost，不用改）
MYSQL_USER = "root"            # 你的 MySQL 用户名（默认一般是 root，插件里能看到）
MYSQL_PASSWORD = "123456"  # 替换成你安装 MySQL 时的密码（比如 123456）
MYSQL_DB = "student"        # 咱们之前创建的数据库名（必须和这个一致）

# 5. 创建 MySQL 连接通道（engine）
engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}")

# 6. 定义主窗口类（所有功能都写在这个类里）
class StudentInfoApp(QMainWindow):
    def __init__(self):
        super().__init__()  # 继承 QMainWindow 的所有功能
        self.init_ui()  # 初始化界面（后面写这个方法）
        self.create_table()  # 创建学生表（后面写这个方法）
        self.load_data()  # 加载数据（后面写这个方法）
    
    # 把这段代码写在 StudentInfoApp 类里（紧跟在 __init__ 方法后面）
    def init_ui(self):
        # 1. 设置窗口标题和大小
        self.setWindowTitle("学生信息录入工具（MySQL版）")  # 窗口标题
        self.setGeometry(300, 300, 1200, 900)  # 窗口位置（100,100）和大小（800宽×600高）

        # 2. 创建中心部件和布局（PyQt5 必须用布局管理组件，否则界面会乱）
        central_widget = QWidget()  # 中心部件（所有内容都放在这个“容器”里）
        self.setCentralWidget(central_widget)  # 把中心部件设为主窗口的核心
        main_layout = QVBoxLayout(central_widget)  # 垂直布局：组件从上到下排列（上方录入区+下方表格区）

        # ---------------------- 上方：录入区域（标签+输入框+按钮）----------------------
        input_layout = QHBoxLayout()  # 水平布局：组件从左到右排列（标签和输入框并排）

        # （1）学号输入框
        self.id_label = QLabel("学号（4位数字）：")  # 标签（提示用户输入什么）
        self.id_input = QLineEdit()  # 输入框（用户输入学号）
        self.id_input.setPlaceholderText("例如：0001")  # 输入框提示文字
        input_layout.addWidget(self.id_label)  # 把标签加入水平布局
        input_layout.addWidget(self.id_input)  # 把输入框加入水平布局

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