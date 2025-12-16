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
from PyQt5.QtGui import QFont, QColor
# 优化后的导入（合并成一行，新增组件直接加在后面）
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox,
    QComboBox, QDateEdit, QTextEdit,QSpinBox,QDialog,QListWidget,QListWidgetItem,QDateTimeEdit  # 新增的高频组件
)
from PyQt5.QtCore import Qt,QDate,QSize,QDateTime,QTimer  


MYSQL_HOST = "localhost"       # 本地 MySQL 地址（默认都是 localhost，不用改）
MYSQL_USER = "root"            # 你的 MySQL 用户名（默认一般是 root，插件里能看到）
MYSQL_PASSWORD = "123456"  # 替换成你安装 MySQL 时的密码（比如 123456）
MYSQL_DB = "client_db"        # 咱们之前创建的数据库名（必须和这个一致）

# 5. 创建 MySQL 连接通道（engine）
engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}")


# ---------------------- 1. 定义新窗口类（修改客户） ----------------------
class ModifyClientWindow(QWidget): #这个用来修改客户信息，包括ID 名字、国家、产品，等级，客户评价
    """修改客户的新窗口"""
    def __init__(self, parent=None, current_user=None,selected_id=None):
        super().__init__(parent)  # parent指定主窗口为父窗口（可选，便于窗口管理）,QWidget类里是会操作parent的，把父亲和儿子绑定。
        self.current_user = current_user  # 接收当前登录用户
        self.name_text=None
        self.country_text=None
        self.product_text=None
        self.grade_text=None
        self.feedback_text=None
        self.selected_id = selected_id
        self.init_ui()

    def init_ui(self):
        """新窗口的界面初始化"""
        # 设置窗口属性
        self.setWindowTitle("修改客户")
        self.setFixedSize(800, 400)  # 固定大小，避免缩放
        self.setWindowModality(Qt.ApplicationModal)  # 模态窗口（阻塞主窗口操作）
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)  



        # 创建布局和控件
        main_layout = QVBoxLayout(self)
        #需要回显数据库里的数据
        df = pd.read_sql_query(f"SELECT * FROM new_quote WHERE Id = '{self.selected_id}'", engine)
        if not df.empty:
            row = df.iloc[0]
            self.name_text=row["名字"]
            self.country_text=row["国家"]
            self.product_text=row["产品"]
            self.grade_text=row["等级"]
            self.feedback_text=row["客户评价"]
        else:
            QMessageBox.warning(self, "提示", "客户不存在！")
            self.close()


        #ID显示
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("客户ID："))
        self.id_text = QLineEdit()
        self.id_text.setText(self.selected_id)
        self.id_text.setReadOnly(True)  # 设置为只读模式
        id_layout.addWidget(self.id_text)
        main_layout.addLayout(id_layout)

        # 姓名输入
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名字："))
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.name_text)
        name_layout.addWidget(self.name_edit)
        main_layout.addLayout(name_layout)

        # 国家输入
        country_layout = QHBoxLayout()
        country_layout.addWidget(QLabel("客户国家："))
        self.country_edit = QLineEdit()
        self.country_edit.setText(self.country_text)     
        country_layout.addWidget(self.country_edit)
        main_layout.addLayout(country_layout)

        # 产品输入
        product_layout = QHBoxLayout()
        product_layout.addWidget(QLabel("客户产品："))
        self.product_edit = QLineEdit()
        self.product_edit.setText(self.product_text)
        product_layout.addWidget(self.product_edit)
        main_layout.addLayout(product_layout)

        # 等级输入
        grade_layout = QHBoxLayout()
        grade_layout.addWidget(QLabel("客户等级："))
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["L0", "L1", "L2", "L3","L4"])
        self.grade_combo.setCurrentText(self.grade_text)
        grade_layout.addWidget(self.grade_combo)
        main_layout.addLayout(grade_layout)
        # 客户评价输入
        feedback_layout = QHBoxLayout()
        feedback_layout.addWidget(QLabel("客户评价："))
        self.feedback_edit = QTextEdit()
        self.feedback_edit.setText(self.feedback_text)
        feedback_layout.addWidget(self.feedback_edit)
        main_layout.addLayout(feedback_layout)

        #保存按钮
        submit_button = QPushButton("保存修改")
        submit_button.clicked.connect(self.submit_client)
        main_layout.addWidget(submit_button)

    def submit_client(self):
        """提交新客户数据"""
        name = self.name_edit.text().strip()
        country = self.country_edit.text().strip()
        product = self.product_edit.text().strip()
        grade = self.grade_combo.currentText()
        feedback = self.feedback_edit.toPlainText().strip()
        # 空值校验
        if not name or not country or not product or not grade: # 客户评价可以为空
            QMessageBox.warning(self, "提示", "所有字段不能为空！")
            return




        try:
            with engine.connect() as conn:
               
                # 插入数据（依赖Id）
                sql = text("""
                    UPDATE new_quote
                    SET `名字` = :name, `国家` = :country, `产品` = :product, `等级` = :grade, `客户评价` = :feedback
                    WHERE Id = :cid;
                """)
                conn.execute(sql, {
                    "cid": self.selected_id,
                    "name": name,
                    "country": country,
                    "product": product,
                    "grade": grade,
                    "feedback": feedback,
                    
                })
                conn.commit()
                QMessageBox.information(self, "成功", "客户修改成功！")
                self.close()  # 关闭新窗口
                self.parent().load_data()  # 刷新父窗口的表格数据
        except Exception as e:
            
             QMessageBox.critical(self, "失败", f"添加失败：{str(e)}")

#跟进客户窗口
class FollowUpClientWindow(QDialog):
    def __init__(self, parent=None, selected_id=None):
        super().__init__(parent)
        self.setWindowTitle("跟进客户")
        self.selected_id = selected_id
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()
    def closeEvent(self, event):
        # 检查儿子是否存在（避免属性不存在报错）
        if hasattr(self, 'client_timeline'):
            self.client_timeline.stop_timer()  # 父亲调用儿子的停止方法
        event.accept()  # 允许父亲关闭
    def init_ui(self):
        """跟进客户窗口的界面初始化"""
        # 设置窗口属性
        self.setWindowTitle("跟进客户")
        self.setFixedSize(1000, 800)  # 固定大小，避免缩放
        #从数据库获取客户信息
        with engine.connect() as conn:
            cursor = conn.connection.cursor(pymysql.cursors.DictCursor) # 使用字典游标，返回结果为字典格式
            cursor.execute("SELECT 名字, 等级, 国家,最近跟进日期,跟进情况 FROM new_quote WHERE Id=%s", (self.selected_id,))
            result = cursor.fetchone()
            if result:
                self.name_sqltext, self.grade_sqltext, self.country_sqltext, self.last_followup_sqltext, self.follow_up_record_sqltext = result.values()
            else:
                QMessageBox.warning(self, "提示", "客户不存在！")
                self.close()
                return
        #创建布局
        main_layout = QVBoxLayout(self)  # 垂直布局：组件从上到下排列（上方录入区+下方表格区）
        #回显客户信息，包括ID,名字，国家，等级，上一次跟进时间和记录
        info_layout = QHBoxLayout()  # 水平布局：组件从左到右排列（标签和输入框并排）
        info_layout.addWidget(QLabel("客户ID："))
        self.id_text = QLineEdit()
        self.id_text.setText(self.selected_id)
        self.id_text.setReadOnly(True)  # 设置为只读模式
        info_layout.addWidget(self.id_text)
        main_layout.addLayout(info_layout)
        info_layout2 = QHBoxLayout()  # 水平布局：组件从左到右排列（标签和输入框并排）
        info_layout.addWidget(QLabel("客户名字："))
        self.name_text = QLineEdit()
        self.name_text.setText(self.name_sqltext)
        self.name_text.setReadOnly(True)  # 设置为只读模式
        info_layout.addWidget(self.name_text)
        info_layout3 = QHBoxLayout()  # 水平布局：组件从左到右排列（标签和输入框并排）
        info_layout2.addWidget(QLabel("客户国家："))
        self.country_text = QLineEdit()
        self.country_text.setText(self.country_sqltext)
        self.country_text.setReadOnly(True)  # 设置为只读模式
        info_layout2.addWidget(self.country_text)
        main_layout.addLayout(info_layout3)

        info_layout2.addWidget(QLabel("客户等级："))
        self.grade_text = QLineEdit()
        self.grade_text.setText(self.grade_sqltext)
        self.grade_text.setReadOnly(True)  # 设置为只读模式
        info_layout2.addWidget(self.grade_text)
        main_layout.addLayout(info_layout2)
        
        # 跟进时间轴，加到自己的属性中
        self.client_timeline = TimeLineWidget(self, self.selected_id)
        main_layout.addWidget(self.client_timeline) #把时间轴添加到布局中

      
        
        # #保存按钮
        # info_layout8 = QHBoxLayout()  # 水平布局：组件从左到右排列（标签和输入框并排）
        # self.save_button = QPushButton("保存")
        # self.save_button.clicked.connect(self.save_follow_up)
        # info_layout8.addWidget(self.save_button)
        # main_layout.addLayout(info_layout8)

    # def save_follow_up(self):
    #     """保存跟进记录"""
    #     follow_up_record = self.follow_up_record_text.toPlainText()
    #     if not follow_up_record:
    #         QMessageBox.warning(self, "提示", "请输入跟进记录！")
    #         return
    #     with engine.connect() as conn:
    # # 占位符改成 :follow_up 和 :id（命名格式）
    #         conn.execute(
    #             text("UPDATE new_quote SET `跟进情况`=:follow_up WHERE `Id`=:id"),
    #     # 传参用字典，key 对应占位符的变量名
    #             {"follow_up": follow_up_record, "id": self.selected_id}
    # )
    #         conn.commit()
    #     QMessageBox.information(self, "提示", "跟进记录已保存！")
    #     print(follow_up_record)
    #     self.close()
    #     self.parent().load_data()  # 刷新父窗口的表格数据

#时间轴类
class TimeLineWidget(QWidget):
    def __init__(self, parent=None, selected_id=None):
        super().__init__(parent)
        self.selected_id = selected_id
        self.init_ui()
        # 关键：提供给父亲调用的“停止定时器”方法
    def stop_timer(self):
        if hasattr(self, 'time_timer') and self.time_timer.isActive():
            self.time_timer.stop()
    def closeEvent(self, event):
        print("closeEvent 触发了！") 
    # 检查定时器是否存在且在运行，是就停止
        if hasattr(self, 'time_timer') and self.time_timer.isActive():
            self.time_timer.stop()
        event.accept()  # 允许窗口关闭
    def init_ui(self):
        # 创建跟进时间轴
        # 1. 布局：垂直布局（标题 + 时间轴列表）
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # 2. 时间轴标题
        self.title_label = QLabel("客户跟进时间轴")
        self.title_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        self.title_label.setStyleSheet("color: #2C3E50;")
        self.layout.addWidget(self.title_label)

        # 3. 时间轴核心组件：QListWidget（关键修复：加 position: relative）
        self.time_line_list = QListWidget()
        self.time_line_list.setStyleSheet("""
                  QListWidget {
                border: none;
                background-color: transparent;
                padding: 0;
                
            }
            QListWidget::item {
                border-left: 2px solid #3498DB;
                padding-left: 20px;
                position: relative;  /* 圆点定位必须 */
            }
            QListWidget::item:hover {
                background-color: #F8F9FA;
            }
            QListWidget::item::before {
                position: absolute;
                left: -10px;
                top: 10px;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                background-color: #3498DB;
            }
        """)
        self.layout.addWidget(self.time_line_list)

        #下方加输入区
        # 输入区容器（单独的Widget，和QListWidget平级）

        self.follow_input_widget = QWidget()
        self.follow_input_widget.setStyleSheet("""
            background-color: #f8f9fa; 
            border: 1px dashed #2196F3; 
            border-radius: 8px; 
            padding: 15px;
            margin-top: 10px;  # 和历史记录区隔开一点，不挤
        """)
        self.follow_input_widget.setVisible(False)  # 默认隐藏，点击按钮再显示

        # 给输入区装内部控件（时间+输入框+按钮）
        input_layout = QVBoxLayout(self.follow_input_widget)

        # ① 跟进时间（可手动修改）
        time_layout = QHBoxLayout()
        time_label = QLabel("跟进时间：")
            # 1. 创建控件时初始化当前时间
        self.follow_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.follow_time_edit.setCalendarPopup(True)
        self.follow_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        #  2.创建定时器（每隔1秒刷新时间）
        self.time_timer = QTimer(self)
        self.time_timer.setInterval(1000)  # 1000毫秒=1秒
        self.time_timer.timeout.connect(self.update_time)  # 定时器触发时调用更新方法
        
       
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.follow_time_edit)
        input_layout.addLayout(time_layout)

        # ② 跟进内容输入框
        self.follow_content_edit = QTextEdit()
        self.follow_content_edit.setPlaceholderText("请输入本次跟进情况（比如客户需求、报价反馈等）...")
        self.follow_content_edit.setMinimumHeight(80)  # 输入框高度
        input_layout.addWidget(self.follow_content_edit)

        # ③ 保存/取消按钮
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存记录")
        self.cancel_btn = QPushButton("取消")
        # 按钮样式（可选，看着舒服）
        self.save_btn.setStyleSheet("background-color: #2196F3; color: white; border: none; padding: 6px 12px; border-radius: 4px;")
        self.cancel_btn.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; padding: 6px 12px; border-radius: 4px;")
        # 按钮居右
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        self.cancel_btn.clicked.connect(self.hide_follow_input)
        self.save_btn.clicked.connect(self.save_follow_up)
        input_layout.addLayout(btn_layout)
        #点击保存按钮，调用save_follow_up方法
        # self.save_btn.clicked.connect(self.save_follow_up)
        # 把输入区添加到主布局（和时间轴平级）
        self.layout.addWidget(self.follow_input_widget)
        self.load_time_line(self.selected_id)

        
       
       
       
       #创建按钮布局，按钮区
        btn_layout = QHBoxLayout()
        
        # （2）创建按钮1：添加跟进记录
        self.add_btn = QPushButton("添加跟进记录")
        self.add_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 15px;
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        btn_layout.addWidget(self.add_btn)
        # （3）创建按钮2：编辑跟进记录
        self.edit_btn = QPushButton("编辑跟进记录")
        self.edit_btn.setStyleSheet(""" 
            QPushButton {
                padding: 6px 15px;
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        btn_layout.addWidget(self.edit_btn)
        self.add_btn.clicked.connect(self.show_follow_input)
        # self.edit_btn.clicked.connect(self.edit_follow_up)
        self.layout.addLayout(btn_layout)
    # 显示输入区时启动定时器，隐藏时停止（节省资源）
    def show_follow_input(self):
        self.follow_input_widget.setVisible(True)
        # 先清空输入框内容（防止上次编辑内容残留在输入区）
        self.follow_time_edit.setDateTime(QDateTime.currentDateTime())
        self.follow_content_edit.clear()
        self.time_timer.start()  # 启动定时器，实时更新

    def hide_follow_input(self):
        self.follow_input_widget.setVisible(False)
        self.time_timer.stop()  # 停止定时器
    def save_follow_up(self):
        """保存跟进记录"""
        follow_content = self.follow_content_edit.toPlainText().strip()

        # 可选：输入校验（避免空内容）
        if not follow_content:
            QMessageBox.warning(self, "输入错误", "请输入跟进内容！")
            return  # 内容为空，直接返回，不执行后续保存逻辑
        qdatetime = self.follow_time_edit.dateTime()
        follow_time = qdatetime.toPyDateTime()# 转换为Python datetime对象，适配SQL存储
        # 数据库操作
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO follow_up_record (Id, 跟进时间, 跟进情况)
                        VALUES (:customer_id, :follow_time, :follow_content)
                    """),
                    {"customer_id": self.selected_id,
                     "follow_time": follow_time,
                     "follow_content": follow_content}
                )
                conn.execute(
            text("""
                UPDATE new_quote 
                SET 最近跟进日期 = :follow_time, 跟进情况 = :follow_content
                WHERE Id = :customer_id
            """),
            {"customer_id": self.selected_id, "follow_time": follow_time, "follow_content": follow_content}
        )

                conn.commit()
                QMessageBox.information(self, "成功", "跟进记录已保存！")
                self.hide_follow_input()
                self.load_time_line(self.selected_id)
                #主窗口也要刷新
                self.parent().parent().load_data()
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"数据库操作失败：{str(e)}")
            conn.rollback()
    # 4. 时间更新方法（把控件时间设为当前系统时间）
    def update_time(self):
        self.follow_time_edit.setDateTime(QDateTime.currentDateTime())

    def load_time_line(self, customer_id):
        """加载指定客户的跟进记录，生成时间轴"""
        follow_records = self.query_follow_records(customer_id) # 查询客户的所有跟进记录,这个方法是返回df的
        if follow_records.empty:
            self.add_empty_item()
            return

        self.time_line_list.clear()
        # 修复：用 _ 忽略无用的 idx（不影响功能，但规范）
        for _, row in follow_records.iterrows():
            self.add_time_line_item(row["跟进时间"], row["跟进情况"])

    def query_follow_records(self, customer_id):
        """查询客户的所有跟进记录（按时间倒序）"""
        try:
            with engine.connect() as conn:
                df = pd.read_sql(
                    text("""
                        SELECT 跟进时间, 跟进情况 
                        FROM follow_up_record 
                        WHERE Id = :customer_id 
                        ORDER BY 跟进时间 DESC
                    """),
                    conn,
                    params={"customer_id": customer_id}
                )
            return df
        except Exception as e:
            print(f"查询跟进记录失败：{str(e)}")
            return pd.DataFrame()

    def add_time_line_item(self, follow_time, follow_content):
        """添加单个时间轴节点（解决右侧留白+垂直居中）"""
        item = QListWidgetItem(self.time_line_list)

        # 1. 先创建 widget 和布局，添加所有组件
        widget = QWidget()
        widget.setStyleSheet("background-color: white;")
        h_layout = QHBoxLayout(widget)
        
        h_layout.setContentsMargins(0, 3, 0, 3)  # 上下内边距不变
        h_layout.setSpacing(15)  # 时间和内容的横向间距不变
        h_layout.setAlignment(Qt.AlignVCenter)  # 垂直居中

        # 时间标签（不变，固定宽度180px）
        time_label = QLabel(follow_time.strftime("%Y-%m-%d %H:%M:%S"))
        time_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        time_label.setStyleSheet("color: #E74C3C; background-color: transparent;")
        time_label.setFixedWidth(180)
        time_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        h_layout.addWidget(time_label)

        # 跟进内容标签（关键修改：解决右侧留白）
        content_label = QLabel(follow_content)
        content_label.setFont(QFont("微软雅黑", 10))
        content_label.setStyleSheet("color: #34495E; background-color: transparent;")
        content_label.setWordWrap(True)  # 自动换行保留
        content_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)  # 垂直居中+左对齐
        content_label.setMinimumWidth(400)
        # 关键1：去掉固定 maximumWidth，改用拉伸因子让内容占满剩余空间
        # content_label.setMaximumWidth(self.time_line_list.width() - 200)  # 删掉这行！
        h_layout.addWidget(content_label)
        # 关键2：给 content_label 加拉伸因子（1=占满所有剩余空间）
        h_layout.setStretchFactor(content_label, 1)

        # 2. 计算 widget 高度
        widget.adjustSize()
        # 关键3：让 item 宽度自适应 QListWidget（不限制宽度）
        item.setSizeHint(QSize(self.time_line_list.width() - 20, widget.height()))  # 减20px避免贴边

        # 3. 把 widget 嵌入 item
        self.time_line_list.setItemWidget(item, widget)
    #添加跟进记录逻辑
    # def add_follow_up(self):
    #     """添加跟进记录"""
    #     follow_time = QDateTime.currentDateTime()
    #     follow_content = self.follow_content_input.text()
    #     if not follow_content.strip():
    #         QMessageBox.warning(self, "输入错误", "请输入跟进内容")
    #         return
    #     with engine.connect() as conn:
    #         conn.execute(
    #             text("""
    #                 INSERT INTO follow_up_record (Id, 跟进时间, 跟进情况)
    #                 VALUES (:customer_id, :follow_time, :follow_content)
    #             """),
    #             {"customer_id": self.current_customer_id,
    #              "follow_time": follow_time.toPyDateTime(),
    #              "follow_content": follow_content}
    #         )
    #     self.load_time_line(self.current_customer_id)
    #     self.follow_content_input.clear()

    def add_empty_item(self):
        """无跟进记录时显示提示（修复3：不覆盖全局样式）"""
        item = QListWidgetItem("暂无跟进记录")
        # 修复3：直接给 Item 设样式（不用 QListWidget::item 选择器，避免冲突）
        item.setStyleSheet("""
            color: #95A5A6;
            font-size: 12px;
            text-align: center;
            border: none;  /* 取消竖线 */
        """)
        # 让提示居中显示（设置 Item 高度，避免太矮）
        item.setSizeHint(QSize(0, 60))
        self.time_line_list.addItem(item)

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
        self.name_label = QLabel("名字：")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入名字")
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
        self.week_input.setRange(1, 99)  # 假设最多52周
        self.week_input.setSingleStep(1)
       
         #先弄个小垂直布局放边上的按钮，可能要多个按钮，用来放跟进客户，和修改客户
        small_btn_layout = QVBoxLayout()
        small_week_layout=QHBoxLayout()
        small_week_layout.addWidget(self.week_label)
        small_week_layout.addWidget(self.week_input)
        small_btn_layout.addLayout(small_week_layout)
        # （8）跟进客户按钮，默认禁用
        self.follow_btn = QPushButton("跟进客户")  # 按钮
        small_btn_layout.addWidget(self.follow_btn)
        self.follow_btn.setEnabled(False)
        self.follow_btn.clicked.connect(self.open_follow_up_window)
        # （9）修改客户按钮
        self.modify_btn = QPushButton("修改客户")  # 按钮
        small_btn_layout.addWidget(self.modify_btn)
        input_layout2.addLayout(small_btn_layout) 
        self.modify_btn.setEnabled(False)
            #绑定监听事件
        self.modify_btn.clicked.connect(self.open_modify_window)


        #询盘信息
        self.quote_label = QLabel("询盘信息：")
        self.quote_input = QTextEdit()
        self.quote_input.setMaximumHeight(135)  # 仅限制最大高度=100px（高度不放大）
        self.quote_input.setPlaceholderText("请输入询盘信息") 
       
        # （7）提交按钮
        self.quote_submit_btn = QPushButton("提交询盘信息")  # 按钮
        self.quote_submit_btn.clicked.connect(self.submit_client)  # 按钮绑定点击事件（点按钮就执行 submit_quote 方法）
        input_layout2.addWidget(self.quote_label)
        input_layout2.addWidget(self.quote_input,1)
        # （8）客户评价输入框
        self.eval_label = QLabel("客户评价：")
        self.eval_input = QTextEdit()
        self.eval_input.setMaximumHeight(135)  
        self.eval_input.setPlaceholderText("客户情况")
        input_layout2.addWidget(self.eval_label)
        input_layout2.addWidget(self.eval_input,1)
        # 把录入区域加入主布局（垂直布局的上方）
        main_layout.addLayout(input_layout)
        main_layout.addLayout(input_layout2)

        # ---------------------- 下方：表格区域（显示学生信息）----------------------
        self.table = QTableWidget()  # 创建表格
        self.table.setColumnCount(11)  # 表格有10列（时间、日期、等级、名字、国家、产品、询盘信息、客户评价、最近跟进日期、跟进情况）
        self.table.setHorizontalHeaderLabels(['Id',"时间","日期", "等级", "名字", "国家","产品","询盘信息","客户评价","最近跟进日期","跟进情况"])  # 表格列标题
         # 1. 设置选择行为：点击单元格自动选中整行（核心！）
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        # 表格自适应列宽（让列宽跟着窗口大小变，更美观）
        self.table.horizontalHeader().setStretchLastSection(True)
        for i in range(11):
            self.table.horizontalHeader().setSectionResizeMode(i, 1)

        # 把表格加入主布局（垂直布局的下方）
        main_layout.addWidget(self.table)        
        self.table.setStyleSheet("""
        /* 表格整体样式（可选，优化基础外观） */
        QTableWidget {
            border: 1px solid #eee;
            gridline-color: #eee;  /* 表格网格线颜色 */
            font-size: 14px;
        }
        /* 表头样式（可选） */
        QTableWidget::horizontalHeader {
            background-color: #f8f9fa;
            border: none;
            padding: 5px;
        }
         QTableWidget::item:!selected:hover {
        background-color: #e8f4f8;
        color: #2196F3;
    }
        /* 选中行样式（可选，和 hover 区分） */
        QTableWidget::item:selected {
            background-color: #1d83c0;  /* 选中行背景色（比 hover 深一点） */
            color: #ffffff;              /* 选中行文字色 */
        }
        /* 行交替颜色（可选，配合 hover 更易读） */
        QTableWidget {
            alternate-background-color: #fafafa;
        }
    """)

        #新增监听，检查是否有选中行，有则启用按钮
        self.table.selectionModel().selectionChanged.connect(self.check_selection)
    # 检查是否有选中行，有则启用按钮
    def check_selection(self)->list:
        selected_rows = self.table.selectionModel().selectedRows()
        has_selected = len(selected_rows) > 0
        self.follow_btn.setEnabled(has_selected)
        self.modify_btn.setEnabled(has_selected)
         # 3. 提取选中行的 ID（核心新增逻辑）
        selected_ids = []  # 用列表存储选中行的 ID（支持多选）
        for index in selected_rows:
            # index.row() → 获取选中行在表格中的「行号」（和 self.df 的行索引一致）
            row_num = index.row()
            # 从 self.df 中取出当前行的 ID（列名替换成你的实际 ID 列名，比如 'id'/'Id'）
            row_id = self.df.iloc[row_num]["Id"]  # 关键：df.iloc[行号][列名]
            selected_ids.append(row_id)
        
        # 4. 按需使用选中的 ID（比如返回、存储或传递给其他函数）
            self.selected_ids = selected_ids  # 存储到实例变量，供其他按钮（如修改/跟进）使用
        return selected_ids  # 返回选中的 ID 列表（单选返回 [id]，多选返回 [id1, id2...]）



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
    名字 VARCHAR(20) NOT NULL,
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
            self.df = pd.DataFrame(columns=["询盘日期", "名字", "客户等级", "国家"])
            QMessageBox.warning(self, "加载提示", f"暂无询盘数据：{str(e)}")
            # 写在 load_data 方法后面，ClientInfoApp 类里 
    def update_table(self):
        # 1. 清空表格里已有的数据（避免重复显示）
        self.table.setRowCount(0)
        
        # 2. 遍历 self.df（从 MySQL 读到的数据），逐行添加到表格
        for row_idx, row in self.df.iterrows():
            # 插入一行（行号是 row_idx）
            self.table.insertRow(row_idx)
            
            # 给每一列赋值（11列：Id、时间、日期、等级、名字、国家、产品、询盘信息、客户评价、最近跟进日期、跟进情况）
            


            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["Id"]))) 
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["时间"])) 
            #日期不能直接显示，需要转换为字符串，先判断是否为空
            if pd.notna(row["日期"]):
                self.table.setItem(row_idx, 2, QTableWidgetItem(row["日期"].strftime("%Y-%m-%d"))) 
            else:
                self.table.setItem(row_idx, 2, QTableWidgetItem(""))  

            self.table.setItem(row_idx, 3, QTableWidgetItem(row["等级"])) 
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["名字"]))   
            # 国家是 VARCHAR 类型，直接显示即可
            self.table.setItem(row_idx, 5, QTableWidgetItem(row["国家"]))
            self.table.setItem(row_idx, 6, QTableWidgetItem(row["产品"]))           
            #客户评价和跟进情况有点长，增加悬停提示
            follow_item = QTableWidgetItem(row["客户评价"])
            follow_item.setToolTip(row["客户评价"])  # 悬停仍显示完整内容
            self.table.setItem(row_idx, 8, follow_item)
            #跟进情况也增加悬停提示
            follow_item = QTableWidgetItem(row["跟进情况"])
            follow_item.setToolTip(row["跟进情况"])  # 悬停仍显示完整内容
            self.table.setItem(row_idx, 10, follow_item)
            #询盘信息也增加悬停提示
            quote_item = QTableWidgetItem(row["询盘信息"])
            quote_item.setToolTip(row["询盘信息"])  # 悬停仍显示完整内容
            self.table.setItem(row_idx, 7, quote_item)
            #最近跟进日期不能直接显示，需要转换为字符串，先判断是否为空
            if pd.notna(row["最近跟进日期"]):
                self.table.setItem(row_idx, 9, QTableWidgetItem(row["最近跟进日期"].strftime("%Y-%m-%d")))
            else:
                self.table.setItem(row_idx, 9, QTableWidgetItem(""))  
            
            
            
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
        #判断是否重复数据，用国家+名字判断是否重复
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


    #打开修改客户窗口
    def open_modify_window(self): #小窗口直接从数据库中读取客户信息，这里就只把ID传过去
        """打开修改客户窗口"""
        selected_id=self.check_selection()
        if not selected_id:
            QMessageBox.warning(self, "选择错误", "请先选择要修改的客户！")
            return
       
        # 打开修改客户窗口
        self.modify_window = ModifyClientWindow(parent=self,selected_id=selected_id[0]) #同时只能修改一个客户，多选时只修改第一个
        self.modify_window.show()
        # 绑定监听事件
    #打开跟进客户窗口
    def open_follow_up_window(self): #小窗口直接从数据库中读取客户信息，这里就只把ID传过去
        """打开跟进客户窗口"""
        selected_id=self.check_selection()
        if not selected_id:
            QMessageBox.warning(self, "选择错误", "请先选择要跟进的客户！")
            return
       
        # 打开跟进客户窗口
        self.follow_up_window = FollowUpClientWindow(parent=self,selected_id=selected_id[0]) #同时只能跟进一个客户，多选时只跟进第一个
        self.follow_up_window.exec_() # exec_() 方法会阻塞主窗口，直到子窗口关闭

# 7. 程序入口（固定写法，让程序能运行起来）
if __name__ == "__main__":
    app = QApplication(sys.argv)  # 创建应用实例
    window = ClientInfoApp()     # 创建主窗口
    window.show()                 # 显示窗口
    sys.exit(app.exec_())         # 让程序持续运行
# 最后，关闭数据库连接（好习惯，释放资源）
engine.dispose()
