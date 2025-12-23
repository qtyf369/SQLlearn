# 1. 处理 Excel 数据的核心库
import pandas as pd
# 2. SQLite 原生数据库连接库（无需额外安装）
import sqlite3
# 3. 其他工具库
import sys
from datetime import datetime
# 可视化界面
from PyQt5.QtGui import QFont, QColor
# 优化后的导入
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox,
    QComboBox, QDateEdit, QTextEdit, QSpinBox, QDialog, QListWidget, QListWidgetItem, QDateTimeEdit
)
from PyQt5.QtCore import Qt, QDate, QSize, QDateTime, QTimer, QEvent

# 全局配置（数据库路径）
DB_PATH = "crm.db"  # SQLite 数据库文件（自动创建）

# ---------------------- 1. 数据库工具函数（简化操作） ----------------------
def get_db_connection():
    """获取 SQLite 数据库连接（原生连接，自动创建文件）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果支持字典式访问（row["字段名"]）
    return conn

# ---------------------- 2. 修改客户窗口 ----------------------
class ModifyClientWindow(QWidget):
    """修改客户的新窗口"""
    def __init__(self, parent=None, selected_id=None):
        super().__init__(parent)
        self.current_user = None
        self.name_text = None
        self.country_text = None
        self.product_text = None
        self.grade_text = None
        self.feedback_text = None
        self.selected_id = selected_id
        self.init_ui()

    def init_ui(self):
        """新窗口的界面初始化"""
        self.setWindowTitle("修改客户")
        self.setFixedSize(800, 400)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        main_layout = QVBoxLayout(self)
        # 回显数据库数据（用原生 sqlite3 查询）
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM new_quote WHERE Id = ?", (self.selected_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                self.name_text = row["名字"]
                self.country_text = row["国家"]
                self.product_text = row["产品"]
                self.grade_text = row["等级"]
                self.feedback_text = row["客户评价"]
            else:
                QMessageBox.warning(self, "提示", "客户不存在！")
                self.close()
                return
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取客户信息失败：{str(e)}")
            self.close()
            return

        # ID 显示
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("客户ID："))
        self.id_text = QLineEdit()
        self.id_text.setText(str(self.selected_id))
        self.id_text.setReadOnly(True)
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
        self.grade_combo.addItems(["L0", "L1", "L2", "L3", "L4"])
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

        # 保存按钮
        submit_button = QPushButton("保存修改")
        submit_button.clicked.connect(self.submit_client)
        main_layout.addWidget(submit_button)

    def submit_client(self):
        """提交修改数据"""
        name = self.name_edit.text().strip()
        country = self.country_edit.text().strip()
        product = self.product_edit.text().strip()
        grade = self.grade_combo.currentText()
        feedback = self.feedback_edit.toPlainText().strip()

        # 空值校验
        if not name or not country or not product or not grade:
            QMessageBox.warning(self, "提示", "所有字段不能为空！")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # 原生 SQL 更新（用 ? 占位符，避免注入）
            cursor.execute("""
                UPDATE new_quote
                SET `名字` = ?, `国家` = ?, `产品` = ?, `等级` = ?, `客户评价` = ?
                WHERE Id = ?
            """, (name, country, product, grade, feedback, self.selected_id))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "成功", "客户修改成功！")
            self.close()
            self.parent().load_data()  # 刷新父窗口
        except Exception as e:
            QMessageBox.critical(self, "失败", f"修改失败：{str(e)}")

# ---------------------- 3. 跟进客户窗口 ----------------------
class FollowUpClientWindow(QDialog):
    def __init__(self, parent=None, selected_id=None):
        super().__init__(parent)
        self.setWindowTitle("跟进客户")
        self.selected_id = selected_id
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def closeEvent(self, event):
        if hasattr(self, 'client_timeline'):
            self.client_timeline.stop_timer()
        event.accept()

    def init_ui(self):
        self.setFixedSize(1000, 800)
        # 从 SQLite 获取客户信息（原生查询）
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 名字, 等级, 国家, 最近跟进日期, 跟进情况 
                FROM new_quote 
                WHERE Id = ?
            """, (self.selected_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                QMessageBox.warning(self, "提示", "客户不存在！")
                self.close()
                return

            self.name_sqltext = row["名字"]
            self.grade_sqltext = row["等级"]
            self.country_sqltext = row["国家"]
            self.last_followup_sqltext = row["最近跟进日期"] or ""
            self.follow_up_record_sqltext = row["跟进情况"] or ""
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取客户信息失败：{str(e)}")
            self.close()
            return

        main_layout = QVBoxLayout(self)
        # 客户信息回显
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("客户ID："))
        self.id_text = QLineEdit()
        self.id_text.setText(str(self.selected_id))
        self.id_text.setReadOnly(True)
        info_layout.addWidget(self.id_text)
        main_layout.addLayout(info_layout)

        info_layout2 = QHBoxLayout()
        info_layout2.addWidget(QLabel("客户名字："))
        self.name_text = QLineEdit()
        self.name_text.setText(self.name_sqltext)
        self.name_text.setReadOnly(True)
        info_layout2.addWidget(self.name_text)

        info_layout2.addWidget(QLabel("客户国家："))
        self.country_text = QLineEdit()
        self.country_text.setText(self.country_sqltext)
        self.country_text.setReadOnly(True)
        info_layout2.addWidget(self.country_text)

        info_layout2.addWidget(QLabel("客户等级："))
        self.grade_text = QLineEdit()
        self.grade_text.setText(self.grade_sqltext)
        self.grade_text.setReadOnly(True)
        info_layout2.addWidget(self.grade_text)
        main_layout.addLayout(info_layout2)

        # 时间轴组件
        self.client_timeline = TimeLineWidget(self, self.selected_id)
        main_layout.addWidget(self.client_timeline)

# ---------------------- 4. 时间轴类 ----------------------
class TimeLineWidget(QWidget):
    def __init__(self, parent=None, selected_id=None):
        super().__init__(parent)
        self.selected_id = selected_id
        self.is_edit_mode = False
        self.current_edit_key = ""
        self.init_ui()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            QApplication.sendEvent(self.time_line_list, event)
        return False

    def stop_timer(self):
        if hasattr(self, 'time_timer') and self.time_timer.isActive():
            self.time_timer.stop()

    def closeEvent(self, event):
        self.stop_timer()
        event.accept()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        self.title_label = QLabel("客户跟进时间轴")
        self.title_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        self.title_label.setStyleSheet("color: #2C3E50;")
        self.layout.addWidget(self.title_label)

        # 时间轴列表
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
                position: relative;
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
        self.time_line_list.itemSelectionChanged.connect(self.highlight_selected_item)
        self.layout.addWidget(self.time_line_list)

        # 跟进输入区
        self.follow_input_widget = QWidget()
        # self.follow_input_widget.setStyleSheet("""
            
        #     border: 1px solid #2196F3;
        #     border-radius: 8px;
        #     padding: 15px;
        #     margin-top: 10px;
        # """)
        self.follow_input_widget.setVisible(False)

        input_layout = QVBoxLayout(self.follow_input_widget) # 跟进输入布局
        # 跟进时间
        time_layout = QHBoxLayout()
        time_label = QLabel("跟进时间：")
        self.follow_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.follow_time_edit.setCalendarPopup(True)
        self.follow_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self.time_timer = QTimer(self)
        self.time_timer.setInterval(1000)
        self.time_timer.timeout.connect(self.update_time) # 定时器更新时间

        # 1. 先创建 QDateTimeEdit，不急于添加到布局
        self.follow_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.follow_time_edit.setCalendarPopup(True)
        self.follow_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
     

        # 5. 最后将 QDateTimeEdit 添加到布局（确保样式已生效）
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.follow_time_edit)
        input_layout.addLayout(time_layout)

        # 跟进内容
        self.follow_content_edit = QTextEdit()
        self.follow_content_edit.setPlaceholderText("请输入本次跟进情况（比如客户需求、报价反馈等）...")
        self.follow_content_edit.setMinimumHeight(80)
        input_layout.addWidget(self.follow_content_edit)

        # 按钮布局
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存记录")
        self.cancel_btn = QPushButton("取消")
        self.save_btn.setStyleSheet("background-color: #2196F3; color: white; border: none; padding: 6px 12px; border-radius: 4px;")
        self.cancel_btn.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; padding: 6px 12px; border-radius: 4px;")
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        self.cancel_btn.clicked.connect(self.hide_follow_input)
        self.save_btn.clicked.connect(self.save_follow_up)
        input_layout.addLayout(btn_layout)

        self.layout.addWidget(self.follow_input_widget)

        # 操作按钮
        btn_layout = QHBoxLayout()
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
        self.edit_btn.clicked.connect(self.edit_follow_up)
        self.layout.addLayout(btn_layout)

        # 加载时间轴数据
        self.load_time_line(self.selected_id)

    def show_follow_input(self):
        self.follow_input_widget.setVisible(True)
        self.add_btn.setVisible(False)
        self.edit_btn.setVisible(False)
        if not self.is_edit_mode:
            self.follow_time_edit.setDateTime(QDateTime.currentDateTime())
            self.follow_content_edit.clear()
            self.time_timer.start()

    def hide_follow_input(self):
        self.follow_input_widget.setVisible(False)
        self.time_timer.stop()
        self.is_edit_mode = False
        self.add_btn.setVisible(True)
        self.edit_btn.setVisible(True)

    def save_follow_up(self):
        follow_content = self.follow_content_edit.toPlainText().strip()
        if not follow_content:
            QMessageBox.warning(self, "输入错误", "请输入跟进内容！")
            return

        qdatetime = self.follow_time_edit.dateTime()
        follow_time_str = qdatetime.toString("yyyy-MM-dd HH:mm:ss")  # 直接转字符串，适配 SQLite

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if self.is_edit_mode:
                # 编辑模式：更新记录
                original_time_str = self.current_edit_key.split("_")[1]
                # 更新跟进记录表
                cursor.execute("""
                    UPDATE follow_up_record
                    SET 跟进时间 = ?, 跟进情况 = ?
                    WHERE Id = ? AND 跟进时间 = ?
                """, (follow_time_str, follow_content, self.selected_id, original_time_str))
                # 更新主表的最近跟进信息
                cursor.execute("""
                    UPDATE new_quote
                    SET 最近跟进日期 = ?, 跟进情况 = ?
                    WHERE Id = ?
                """, (follow_time_str, follow_content, self.selected_id))
                QMessageBox.information(self, "成功", "跟进记录已更新！")
            else:
                # 新增模式：插入记录
                cursor.execute("""
                    INSERT INTO follow_up_record (Id, 跟进时间, 跟进情况)
                    VALUES (?, ?, ?)
                """, (self.selected_id, follow_time_str, follow_content))
                # 更新主表的最近跟进信息
                cursor.execute("""
                    UPDATE new_quote
                    SET 最近跟进日期 = ?, 跟进情况 = ?
                    WHERE Id = ?
                """, (follow_time_str, follow_content, self.selected_id))
                QMessageBox.information(self, "成功", "跟进记录已保存！")

            conn.commit()
            conn.close()
            self.hide_follow_input()
            self.load_time_line(self.selected_id)
            self.parent().parent().load_data()
            self.is_edit_mode = False
        except Exception as e:
            QMessageBox.warning(self, "失败", f"数据库操作失败：{str(e)}")

    def update_time(self):
        self.follow_time_edit.setDateTime(QDateTime.currentDateTime())

    def load_time_line(self, customer_id):
        follow_records = self.query_follow_records(customer_id)
        if not follow_records:
            self.add_empty_item()
            return

        self.time_line_list.clear()
        for record in follow_records:
            follow_time = pd.to_datetime(record["跟进时间"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
            if pd.notna(follow_time):
                self.add_time_line_item(follow_time, record["跟进情况"])

    def query_follow_records(self, customer_id):
        """查询客户的所有跟进记录（原生 SQL 查询）"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 跟进时间, 跟进情况
                FROM follow_up_record
                WHERE Id = ?
                ORDER BY 跟进时间 DESC
            """, (customer_id,))
            records = cursor.fetchall()  # 返回列表，每个元素是 sqlite3.Row 对象
            conn.close()
            return records
        except Exception as e:
            print(f"查询跟进记录失败：{str(e)}")
            return []

    def add_time_line_item(self, follow_time, follow_content):
        item = QListWidgetItem(self.time_line_list)
        widget = QWidget()
        widget.setStyleSheet("background-color: white;")
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(0, 3, 0, 3)
        h_layout.setSpacing(15)
        h_layout.setAlignment(Qt.AlignVCenter)

        # 时间标签
        time_label = QLabel(follow_time.strftime("%Y-%m-%d %H:%M:%S"))
        time_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        time_label.setStyleSheet("color: #E74C3C; background-color: transparent;")
        time_label.setFixedWidth(180)
        time_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        time_label.setCursor(Qt.IBeamCursor)
        time_label.installEventFilter(self)
        h_layout.addWidget(time_label)

        # 内容标签
        content_label = QLabel(follow_content)
        content_label.setFont(QFont("微软雅黑", 10))
        content_label.setStyleSheet("color: #34495E; background-color: transparent;")
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        content_label.setMinimumWidth(400)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setCursor(Qt.IBeamCursor)
        content_label.installEventFilter(self)
        h_layout.addWidget(content_label)
        h_layout.setStretchFactor(content_label, 1)

        widget.adjustSize()
        item.setSizeHint(QSize(self.time_line_list.width() - 20, widget.height()))
        self.time_line_list.setItemWidget(item, widget)

    def edit_follow_up(self):
        selected_items = self.time_line_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "操作提示", "请先选择一条跟进记录")
            return

        self.is_edit_mode = True
        self.show_follow_input()

        selected_widget = self.time_line_list.itemWidget(selected_items[0])
        h_layout = selected_widget.layout()
        time_label = h_layout.itemAt(0).widget()
        content_label = h_layout.itemAt(1).widget()

        follow_time_str = time_label.text().strip()
        follow_content = content_label.text().strip()

        follow_datetime = QDateTime.fromString(follow_time_str, "yyyy-MM-dd HH:mm:ss")
        self.follow_time_edit.setDateTime(follow_datetime)
        self.follow_content_edit.setPlainText(follow_content)
        self.current_edit_key = f"{self.selected_id}_{follow_time_str}"

    def add_empty_item(self):
        item = QListWidgetItem("暂无跟进记录")
        # item.setStyleSheet("""
        #     color: #95A5A6;
        #     font-size: 12px;
        #     text-align: center;
        #     border: none;
        # """)
        item.setSizeHint(QSize(0, 60))
        self.time_line_list.addItem(item)

    def highlight_selected_item(self):
        # 清除所有高亮
        for i in range(self.time_line_list.count()):
            item = self.time_line_list.item(i)
            widget = self.time_line_list.itemWidget(item)
            if widget:
                widget.setStyleSheet("background-color: white;")
                for label in widget.findChildren(QLabel):
                    if ":" in label.text():
                        label.setStyleSheet("color: #E74C3C; background-color: transparent;")
                    else:
                        label.setStyleSheet("color: #34495E; background-color: transparent;")

        # 高亮选中项
        selected_items = self.time_line_list.selectedItems()
        if selected_items:
            selected_widget = self.time_line_list.itemWidget(selected_items[0])
            if selected_widget:
                selected_widget.setStyleSheet("background-color: #1a85ff; border-radius: 8px;")
                for label in selected_widget.findChildren(QLabel):
                    label.setStyleSheet("color: #e7f2ff; background-color: transparent;")

# ---------------------- 5. 主窗口类 ----------------------
class ClientInfoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = pd.DataFrame()  # 存储表格数据
        self.init_ui()
        self.create_tables()  # 启动时自动创建表
        self.load_data()

    def init_ui(self):
        self.setWindowTitle("客户信息录入工具")
        self.setGeometry(300, 300, 1200, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 上方录入区域
        input_layout = QHBoxLayout()
        input_layout2 = QHBoxLayout()

        # 询盘日期
        self.date_label = QLabel("询盘日期：")
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())
        input_layout.addWidget(self.date_label)
        input_layout.addWidget(self.date_input)

        # 名字
        self.name_label = QLabel("名字：")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入名字")
        input_layout.addWidget(self.name_label)
        input_layout.addWidget(self.name_input)

        # 客户等级
        self.grade_label = QLabel("客户等级：")
        self.grade_input = QComboBox()
        self.grade_input.addItems(["L0", "L1", "L2", "L3", "L4"])
        self.grade_input.setCurrentText("L0")
        input_layout.addWidget(self.grade_label)
        input_layout.addWidget(self.grade_input)

        # 国家
        self.country_label = QLabel("国家：")
        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("例如：中国")
        input_layout.addWidget(self.country_label)
        input_layout.addWidget(self.country_input)

        # 产品
        self.product_label = QLabel("产品：")
        self.product_input = QLineEdit()
        default_product = "光伏系统"
        self.product_input.setText(default_product)
        input_layout.addWidget(self.product_label)
        input_layout.addWidget(self.product_input)

        # 提交按钮
        self.submit_btn = QPushButton("提交信息")
        self.submit_btn.clicked.connect(self.submit_client)
        input_layout.addWidget(self.submit_btn)

        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_data)
        input_layout.addWidget(self.refresh_btn)

        # 右侧小布局（周数+按钮）
        small_btn_layout = QVBoxLayout()
        small_week_layout = QHBoxLayout()
        self.week_label = QLabel("第几周：")
        self.week_input = QSpinBox()
        self.week_input.setRange(1, 99)
        small_week_layout.addWidget(self.week_label)
        small_week_layout.addWidget(self.week_input)
        small_btn_layout.addLayout(small_week_layout)

        # 跟进客户按钮
        self.follow_btn = QPushButton("跟进客户")
        self.follow_btn.setEnabled(False)
        self.follow_btn.clicked.connect(self.open_follow_up_window)
        small_btn_layout.addWidget(self.follow_btn)

        # 修改客户按钮
        self.modify_btn = QPushButton("修改客户")
        self.modify_btn.setEnabled(False)
        self.modify_btn.clicked.connect(self.open_modify_window)
        small_btn_layout.addWidget(self.modify_btn)
        input_layout2.addLayout(small_btn_layout)

        # 询盘信息
        self.quote_label = QLabel("询盘信息：")
        self.quote_input = QTextEdit()
        self.quote_input.setMaximumHeight(135)
        self.quote_input.setPlaceholderText("请输入询盘信息")
        input_layout2.addWidget(self.quote_label)
        input_layout2.addWidget(self.quote_input, 1)

        # 客户评价
        self.eval_label = QLabel("客户评价：")
        self.eval_input = QTextEdit()
        self.eval_input.setMaximumHeight(135)
        self.eval_input.setPlaceholderText("客户情况")
        input_layout2.addWidget(self.eval_label)
        input_layout2.addWidget(self.eval_input, 1)

        main_layout.addLayout(input_layout)
        main_layout.addLayout(input_layout2)

        # 下方表格区域
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels(['Id', "时间", "日期", "等级", "名字", "国家", "产品", "询盘信息", "客户评价", "最近跟进日期", "跟进情况"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        for i in range(11):
            self.table.horizontalHeader().setSectionResizeMode(i, 1)

        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #eee;
                gridline-color: #eee;
                font-size: 14px;
            }
            QTableWidget::horizontalHeader {
                background-color: #f8f9fa;
                border: none;
                padding: 5px;
            }
            QTableWidget::item:!selected:hover {
                background-color: #e8f4f8;
                color: #2196F3;
            }
            QTableWidget::item:selected {
                background-color: #1d83c0;
                color: #ffffff;
            }
            QTableWidget {
                alternate-background-color: #fafafa;
            }
        """)
        main_layout.addWidget(self.table)

        # 监听表格选择事件
        self.table.selectionModel().selectionChanged.connect(self.check_selection)

    def check_selection(self) -> list:
        selected_rows = self.table.selectionModel().selectedRows()
        has_selected = len(selected_rows) > 0
        self.follow_btn.setEnabled(has_selected)
        self.modify_btn.setEnabled(has_selected)

        selected_ids = []
        for index in selected_rows:
            row_num = index.row()
            if row_num < len(self.df):
                row_id = self.df.iloc[row_num]["Id"]
                selected_ids.append(row_id)
        self.selected_ids = selected_ids
        return selected_ids

    def create_tables(self):
        """创建 new_quote 和 follow_up_record 表（SQLite 原生语法，确保执行成功）"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. 创建客户主表 new_quote（Id 自增主键）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS new_quote (
                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
                    时间 TEXT NOT NULL,
                    日期 TEXT NOT NULL,
                    名字 TEXT NOT NULL,
                    等级 TEXT NOT NULL,
                    国家 TEXT NOT NULL,
                    产品 TEXT NOT NULL,
                    询盘信息 TEXT,
                    客户评价 TEXT,
                    最近跟进日期 TEXT,
                    跟进情况 TEXT
                );
            """)

            # 2. 创建跟进记录表 follow_up_record（外键关联主表 Id）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follow_up_record (
                    Id INTEGER NOT NULL,
                    跟进时间 TEXT NOT NULL,
                    跟进情况 TEXT NOT NULL,
                    FOREIGN KEY (Id) REFERENCES new_quote (Id) ON DELETE CASCADE
                );
            """)

            conn.commit()
            conn.close()
            print("表格创建成功（或已存在）")
        except Exception as e:
            QMessageBox.critical(self, "建表失败", f"建表失败原因：{str(e)}")

    def load_data(self):
        """加载数据（原生 SQL 查询 + 转 DataFrame）"""
        try:
            conn = get_db_connection()
            # 用 pandas 读取原生查询结果（简化数据处理）
            self.df = pd.read_sql_query("SELECT * FROM new_quote", conn)
            conn.close()
            self.update_table()
        except Exception as e:
            self.df = pd.DataFrame(columns=["Id", "时间", "日期", "等级", "名字", "国家", "产品", "询盘信息", "客户评价", "最近跟进日期", "跟进情况"])
            QMessageBox.warning(self, "加载提示", f"暂无数据：{str(e)}")

    def update_table(self):
        """更新表格显示"""
        self.table.setRowCount(0)
        for row_idx, row in self.df.iterrows():
            self.table.insertRow(row_idx)

            # 填充各列数据
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["Id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["时间"]))

            # 日期列（处理空值）
            date_val = row["日期"]
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(date_val)) if pd.notna(date_val) else QTableWidgetItem(""))

            self.table.setItem(row_idx, 3, QTableWidgetItem(row["等级"]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["名字"]))
            self.table.setItem(row_idx, 5, QTableWidgetItem(row["国家"]))
            self.table.setItem(row_idx, 6, QTableWidgetItem(row["产品"]))

            # 询盘信息（带悬停提示）
            quote_val = row["询盘信息"] if pd.notna(row["询盘信息"]) else ""
            quote_item = QTableWidgetItem(quote_val)
            quote_item.setToolTip(quote_val)
            self.table.setItem(row_idx, 7, quote_item)

            # 客户评价（带悬停提示）
            eval_val = row["客户评价"] if pd.notna(row["客户评价"]) else ""
            eval_item = QTableWidgetItem(eval_val)
            eval_item.setToolTip(eval_val)
            self.table.setItem(row_idx, 8, eval_item)

            # 最近跟进日期（处理空值）
            follow_date_val = row["最近跟进日期"]
            self.table.setItem(row_idx, 9, QTableWidgetItem(str(follow_date_val)) if pd.notna(follow_date_val) else QTableWidgetItem(""))

            # 跟进情况（带悬停提示）
            follow_val = row["跟进情况"] if pd.notna(row["跟进情况"]) else ""
            follow_item = QTableWidgetItem(follow_val)
            follow_item.setToolTip(follow_val)
            self.table.setItem(row_idx, 10, follow_item)

            # 居中对齐
            for col in range(11):
                self.table.item(row_idx, col).setTextAlignment(Qt.AlignCenter)

    def submit_client(self):
        """提交客户信息（原生 SQL 插入）"""
        # 获取输入数据
        week = self.week_input.value()
        quote_date = self.date_input.text().strip()
        client_name = self.name_input.text().strip()
        client_level = self.grade_input.currentText()
        country = self.country_input.text().strip()
        product = self.product_input.text().strip()
        eval_text = self.eval_input.toPlainText().strip()
        quote_info = self.quote_input.toPlainText().strip()

        # 空值校验
        if not all([quote_date, client_name, client_level, country, product, week]):
            QMessageBox.warning(self, "输入错误", "所有字段不能为空！")
            return

        # 重复校验（国家+名字）
        if not self.df.empty:
            current_data = self.df[(self.df["国家"] == country) & (self.df["名字"] == client_name)]
            if not current_data.empty:
                QMessageBox.warning(self, "重复录入", f"国家{country}客户{client_name}已存在，请勿重复提交！")
                return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # 原生 SQL 插入
            cursor.execute("""
                INSERT INTO new_quote (时间, 日期, 名字, 等级, 国家, 产品, 客户评价, 跟进情况, 最近跟进日期, 询盘信息)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"第{week}周", quote_date, client_name, client_level, country, product, eval_text, "", "", quote_info))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "成功", "客户信息录入成功！")
            self.load_data()

            # 清空输入框
            self.name_input.clear()
            self.grade_input.setCurrentIndex(0)
            self.country_input.clear()
            self.product_input.clear()
            self.eval_input.clear()
            self.quote_input.clear()
        except Exception as e:
            QMessageBox.error(self, "提交失败", f"录入失败：{str(e)}")

    def open_modify_window(self):
        """打开修改客户窗口"""
        selected_ids = self.check_selection()
        if not selected_ids:
            QMessageBox.warning(self, "选择错误", "请先选择要修改的客户！")
            return
        self.modify_window = ModifyClientWindow(parent=self, selected_id=selected_ids[0])
        self.modify_window.show()

    def open_follow_up_window(self):
        """打开跟进客户窗口"""
        selected_ids = self.check_selection()
        if not selected_ids:
            QMessageBox.warning(self, "选择错误", "请先选择要跟进的客户！")
            return
        self.follow_up_window = FollowUpClientWindow(parent=self, selected_id=selected_ids[0])
        self.follow_up_window.exec_()

# ---------------------- 程序入口 ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClientInfoApp()
    window.show()
    sys.exit(app.exec_())