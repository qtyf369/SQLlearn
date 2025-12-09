# 1. 处理 Excel 数据的核心库
import pandas as pd
# 2. 连接 MySQL 数据库的核心库
from sqlalchemy import create_engine, text
# 3. 处理 MySQL 连接可能出现的错误（可选，但建议加）
import pymysql
pymysql.install_as_MySQLdb() #伪装成MySQLdb模块，好像新版的sqlalchemy已经支持pymysql了
from sqlalchemy.types import DATE 
import sys
from datetime import datetime
#可视化界面

# 优化后的导入（合并成一行，新增组件直接加在后面）
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox,
    QComboBox, QDateEdit, QTextEdit,QSpinBox  # 新增的高频组件
)
from PyQt5.QtCore import Qt,QDate


MYSQL_HOST = "localhost"       # 本地 MySQL 地址（默认都是 localhost，不用改）
MYSQL_USER = "root"            # 你的 MySQL 用户名（默认一般是 root，插件里能看到）
MYSQL_PASSWORD = "123456"  # 替换成你安装 MySQL 时的密码（比如 123456）
MYSQL_DB = "client_db"        # 咱们之前创建的数据库名（必须和这个一致）

# 5. 创建 MySQL 连接通道（engine）
engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}")

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
        input_layout2 = QHBoxLayout()  # 水平布局：组件从左到右排列（标签和输入框并排）

        # （1）询盘日期输入框
        self.date_label = QLabel("询盘日期：")  # 标签（提示用户输入什么）
        self.date_input = QDateEdit()  # 输入框（用户输入学号）
        self.date_input.setCalendarPopup(True)  # 点击输入框弹出日期选择器
        self.date_input.setDisplayFormat("yyyy-MM-dd")  # 显示格式为 "年-月-日"
        self.date_input.setDate(QDate.currentDate())  # 获取系统当前日期并设置为默认值
        input_layout.addWidget(self.date_label)  # 把标签加入水平布局
        input_layout.addWidget(self.date_input)  # 把输入框加入水平布局

        # （2）姓名输入框
        self.name_label = QLabel("客户姓名：")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入客户姓名")
        input_layout.addWidget(self.name_label)
        input_layout.addWidget(self.name_input)

        # （3）等级输入框（改为下拉框）
        self.grade_label = QLabel("客户等级：")
        self.grade_input = QComboBox()  # 替换 QLineEdit 为 QComboBox（下拉框）
        self.grade_input.addItems(["L0", "L1", "L2", "L3", "L4"])  # 添加下拉选项 L0-L4
        self.grade_input.setCurrentText("L0")  # 默认选中 L0
        input_layout.addWidget(self.grade_label)
        input_layout.addWidget(self.grade_input)

        # （4）国家输入框
        self.country_label = QLabel("国家：")
        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("例如：中国")
        input_layout.addWidget(self.country_label)
        input_layout.addWidget(self.country_input)

       # （7）产品输入框
        self.product_label = QLabel("产品：")
        self.product_input = QLineEdit()
        default_product = "光伏系统"
        self.product_input.setText(default_product)
        self.product_input.setPlaceholderText("光伏系统")
        input_layout.addWidget(self.product_label)
        input_layout.addWidget(self.product_input)

        # （5）提交按钮
        self.submit_btn = QPushButton("提交信息")  # 按钮
        self.submit_btn.clicked.connect(self.submit_client)  # 按钮绑定点击事件（点按钮就执行 submit_client 方法）
        input_layout.addWidget(self.submit_btn)
        # （6）手动刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_data)  # 按钮绑定点击事件（点按钮就执行 load_data 方法）
        input_layout.addWidget(self.refresh_btn)
       #时间输入框，第几周
        self.week_label = QLabel("第几周：")
        self.week_input = QSpinBox()
        self.week_input.setRange(1, 52)  # 假设最多52周
        self.week_input.setSingleStep(1)
        input_layout2.addWidget(self.week_label)
        input_layout2.addWidget(self.week_input)
        #询盘信息
        self.quote_label = QLabel("询盘信息：")
        self.quote_input = QTextEdit()
        self.quote_input.setMaximumHeight(150)  # 仅限制最大高度=150px（高度不放大）
        self.quote_input.setPlaceholderText("请输入询盘信息") 
        input_layout2.addWidget(self.quote_label)
        input_layout2.addWidget(self.quote_input,1)
        # （8）客户评价输入框
        self.eval_label = QLabel("客户评价：")
        self.eval_input = QTextEdit()
        self.eval_input.setMaximumHeight(150)  # 仅限制最大高度=150px（高度不放大）
        self.eval_input.setPlaceholderText("客户情况")
        input_layout2.addWidget(self.eval_label)
        input_layout2.addWidget(self.eval_input,1)
        # 把录入区域加入主布局（垂直布局的上方）
        main_layout.addLayout(input_layout)
        main_layout.addLayout(input_layout2)

        # ---------------------- 下方：表格区域（显示学生信息）----------------------
        self.table = QTableWidget()  # 创建表格
        self.table.setColumnCount(10)  # 表格有10列（时间、日期、等级、客户姓名、国家、产品、询盘信息、客户评价、最近跟进日期、跟进情况）
        self.table.setHorizontalHeaderLabels(["时间","日期", "等级", "客户姓名", "国家","产品","询盘信息","客户评价","最近跟进日期","跟进情况"])  # 表格列标题

        # 表格自适应列宽（让列宽跟着窗口大小变，更美观）
        self.table.horizontalHeader().setStretchLastSection(True)
        for i in range(10):
            self.table.horizontalHeader().setSectionResizeMode(i, 1)

        # 把表格加入主布局（垂直布局的下方）
        main_layout.addWidget(self.table)        

    # 把这段代码写在 ClientInfoApp 类里（紧跟在 init_ui 方法后面）
    def create_table(self):
        try:
            with engine.connect() as conn:
                check_sql = text("""
                SELECT TABLE_NAME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = :db_name  -- 数据库名（client_db）
                  AND TABLE_NAME = :table_name  -- 表名（client_info）
            """)
            # 传递参数（避免 SQL 注入，更规范）
                result = conn.execute(
                    check_sql,
                    {"db_name": MYSQL_DB, "table_name": "new_quote"}
            ).fetchone()  # fetchone()：有结果返回表名，无结果返回 None

                # 1. 定义SQL语句（确保格式正确，无多余符号）
            if result is None:   
                create_sql = """
    CREATE TABLE IF NOT EXISTS new_quote (
    询盘日期 DATE NOT NULL,
    客户姓名 VARCHAR(20) NOT NULL,
    客户等级 VARCHAR(20) NOT NULL,
    国家 VARCHAR(20) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
                # 2. 用 text() 包装SQL，转为可执行对象
                conn.execute(text(create_sql.strip()))
                conn.commit()
                QMessageBox.information(self, "建表成功", "new_quote表创建成功！")
        except Exception as e:
            QMessageBox.critical(self, "建表失败", f"建表失败原因：{str(e)}")
    # 写在 create_table 方法后面，ClientInfoApp 类里
    def load_data(self):
        try:
            # 用 text() 包装查询SQL
            self.df = pd.read_sql(text("SELECT * FROM new_quote"), engine)
            self.update_table()
        except Exception as e:
            self.df = pd.DataFrame(columns=["询盘日期", "客户姓名", "客户等级", "国家"])
            QMessageBox.warning(self, "加载提示", f"暂无询盘数据：{str(e)}")
            # 写在 load_data 方法后面，ClientInfoApp 类里 
    def update_table(self):
        # 1. 清空表格里已有的数据（避免重复显示）
        self.table.setRowCount(0)
        
        # 2. 遍历 self.df（从 MySQL 读到的数据），逐行添加到表格
        for row_idx, row in self.df.iterrows():
            # 插入一行（行号是 row_idx）
            self.table.insertRow(row_idx)
            
            # 给每一列赋值（4列：询盘日期、客户姓名、客户等级、国家）
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["时间"])) 
            #日期不能直接显示，需要转换为字符串，先判断是否为空
            if pd.notna(row["日期"]):
                self.table.setItem(row_idx, 1, QTableWidgetItem(row["日期"].strftime("%Y-%m-%d"))) 
            else:
                self.table.setItem(row_idx, 1, QTableWidgetItem(""))  

            self.table.setItem(row_idx, 2, QTableWidgetItem(row["等级"])) 
            self.table.setItem(row_idx, 3, QTableWidgetItem(row["名字"]))
            # 国家是 VARCHAR 类型，直接显示即可
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["国家"]))
            self.table.setItem(row_idx, 5, QTableWidgetItem(row["产品"]))
            #客户评价和跟进情况有点长，增加悬停提示
            follow_item = QTableWidgetItem(row["客户评价"])
            follow_item.setToolTip(row["客户评价"])  # 悬停仍显示完整内容
            self.table.setItem(row_idx, 7, follow_item)
            #跟进情况也增加悬停提示
            follow_item = QTableWidgetItem(row["跟进情况"])
            follow_item.setToolTip(row["跟进情况"])  # 悬停仍显示完整内容
            self.table.setItem(row_idx, 9, follow_item)
            #询盘信息也增加悬停提示
            quote_item = QTableWidgetItem(row["询盘信息"])
            quote_item.setToolTip(row["询盘信息"])  # 悬停仍显示完整内容
            self.table.setItem(row_idx, 6, quote_item)
            #最近跟进日期不能直接显示，需要转换为字符串，先判断是否为空
            if pd.notna(row["最近跟进日期"]):
                self.table.setItem(row_idx, 8, QTableWidgetItem(row["最近跟进日期"].strftime("%Y-%m-%d")))
            else:
                self.table.setItem(row_idx, 8, QTableWidgetItem(""))  
            
            
            
            # 3. 让表格内容居中对齐（更美观）
            for col in range(10):
                self.table.item(row_idx, col).setTextAlignment(Qt.AlignCenter)
# 写在 update_table 方法后面，ClientInfoApp 类里
    def submit_client(self):
        # 1. 获取输入框里的内容（strip() 去掉前后空格，避免输入空字符）
        week = self.week_input.value()#周数
        quote_date = self.date_input.text().strip()
        client_name = self.name_input.text().strip()
        client_level = self.grade_input.currentText()
        country = self.country_input.text().strip()
        product = self.product_input.text().strip()
        eval = self.eval_input.toPlainText().strip()
        quote_info = self.quote_input.toPlainText().strip()
        # 2. 数据校验（避免无效数据存入 MySQL）
        # 校验1：所有字段不能为空,客户评价可以为空
        if not all([quote_date, client_name, client_level, country,product,week]):
            QMessageBox.warning(self, "输入错误", "所有字段不能为空！")
            return  # 直接返回，不执行后续操作
        

        
 
            
        
        # 3. 把输入的信息整理成 DataFrame（方便 pandas 写入 MySQL）
        new_data = pd.DataFrame({
            "时间": [f"第{week}周"],
            "日期": [quote_date],
            "名字": [client_name],
            "等级": [client_level],
            "国家": [country],
            "产品": [product],
            "客户评价": [eval],
            "跟进情况": [""],
            "最近跟进日期": [datetime.now()],
            "询盘信息": [quote_info],

        })
        #判断是否重复数据，用国家+客户姓名判断是否重复
        current_data = self.df[(self.df["国家"] == country) & (self.df["名字"] == client_name)]
        if not current_data.empty:
            QMessageBox.warning(self, "重复录入", f"国家{country}客户{client_name}已存在，请勿重复提交！")
            return
        # 4. 把数据写入 MySQL
        try:
            # df.to_sql() 本质是执行 SQL：INSERT INTO student_info (...) VALUES (...)
            new_data.to_sql(
                name="new_quote",  # 要写入的表名   
                con=engine,           # 连接通道
                if_exists="append",   # 追加数据（不覆盖已有数据）
                index=False           # 不把 DataFrame 的索引写入 MySQL（避免多一列）
            )
            
            # 5. 写入成功后，提示用户
            QMessageBox.information(self, "成功", "客户信息录入成功！")
            
            # 6. 重新加载数据，更新表格（让新数据显示在表格里）
            self.load_data()
            
            # 7. 清空输入框，方便下次录入
            self.name_input.clear()
            self.grade_input.setCurrentIndex(0)
            self.country_input.clear()
            self.product_input.clear()
            self.eval_input.clear()
            self.quote_input.clear()
            
        
        except pymysql.IntegrityError:
            # 捕获主键冲突（学号重复，因为 MySQL 表的学号是 PRIMARY KEY）
            QMessageBox.warning(self, "重复录入", f"学号{client_id}已存在，请勿重复提交！")
        except Exception as e:
            # 其他错误（比如连接失败）
            QMessageBox.error(self, "提交失败", f"录入失败：{str(e)}")

                 


# 7. 程序入口（固定写法，让程序能运行起来）
if __name__ == "__main__":
    app = QApplication(sys.argv)  # 创建应用实例
    window = ClientInfoApp()     # 创建主窗口
    window.show()                 # 显示窗口
    sys.exit(app.exec_())         # 让程序持续运行
# 最后，关闭数据库连接（好习惯，释放资源）
engine.dispose()
