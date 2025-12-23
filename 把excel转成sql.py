# 1. 处理 Excel 数据的核心库
import pandas as pd
# 2. 连接 SQLite 数据库的核心库（轻量化，无需额外安装服务）
import sqlite3
# 3. 其他工具库
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QComboBox,
    QTextEdit, QFileDialog
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

# 全局变量（存储Excel路径）
EXCEL_FILE_PATH = ""

class ExcelToSQLiteWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel 转 SQLite 导入工具")
        self.setGeometry(100, 100, 700, 550)
        self.setStyleSheet("background-color: #f5f7fa;")  # 整体背景色
        self.initUI()

    def initUI(self):
        # 主窗口中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(15)  # 控件间距
        self.main_layout.setContentsMargins(30, 30, 30, 30)  # 内边距

        # 标题样式
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label = QLabel("Excel 数据 → SQLite 导入工具")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2d3748; margin-bottom: 10px;")
        self.main_layout.addWidget(title_label)

        # 1. 选择文件区域
        file_layout = QHBoxLayout()
        self.select_file_btn = QPushButton("📂 选择 Excel 文件")
        self.select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #4299e1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
            QPushButton:pressed {
                background-color: #2b6cb0;
            }
        """)
        self.select_file_btn.clicked.connect(self.on_select_file)
        file_layout.addWidget(self.select_file_btn)

        # Excel路径显示框
        self.excel_path_input = QLineEdit()
        self.excel_path_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4299e1;
                outline: none;
                box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
            }
        """)
        self.excel_path_input.setPlaceholderText("Excel 文件绝对路径（自动填充）")
        file_layout.addWidget(self.excel_path_input)
        self.main_layout.addLayout(file_layout)

        # 2. 工作表选择区域（下拉框，自动加载）
        sheet_layout = QHBoxLayout()
        sheet_label = QLabel("工作表：")
        sheet_label.setStyleSheet("font-size: 14px; color: #4a5568; width: 80px;")
        sheet_layout.addWidget(sheet_label)

        self.sheet_combo = QComboBox()
        self.sheet_combo.setStyleSheet("""
             QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                background-color: white;
                color: #2d3748;
            }
            QComboBox:focus {
                border-color: #4299e1;
                outline: none;
                box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
            }
        """)
        self.sheet_combo.setPlaceholderText("请选择工作表（自动加载）")
        sheet_layout.addWidget(self.sheet_combo)
        self.main_layout.addLayout(sheet_layout)

        # 3. 数据库配置区域（网格布局，更紧凑）
        db_layout = QVBoxLayout()
        db_layout.setSpacing(12)

        # 数据库名输入
        db_name_layout = QHBoxLayout()
        db_name_label = QLabel("SQLite 数据库名：")
        db_name_label.setStyleSheet("font-size: 14px; color: #4a5568; width: 120px;")
        self.db_name_input = QLineEdit("crm.db")  # 默认数据库名
        self.db_name_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4299e1;
                outline: none;
                box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
            }
        """)
        self.db_name_input.setPlaceholderText("例如：student.db（自动创建）")
        db_name_layout.addWidget(db_name_label)
        db_name_layout.addWidget(self.db_name_input)
        db_layout.addLayout(db_name_layout)

        # 表名输入，数据库里的表名
        table_name_layout = QHBoxLayout()
        table_name_label = QLabel("数据库表名：")
        table_name_label.setStyleSheet("font-size: 14px; color: #4a5568; width: 120px;")
        self.table_name_input = QLineEdit("excel_data")  # 默认表名
        self.table_name_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4299e1;
                outline: none;
                box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
            }
        """)
        self.table_name_input.setPlaceholderText("例如：student_info（自动创建）")
        table_name_layout.addWidget(table_name_label)
        table_name_layout.addWidget(self.table_name_input)
        db_layout.addLayout(table_name_layout)

        self.main_layout.addLayout(db_layout)

        # 4. 导入按钮（突出显示）
        self.import_btn = QPushButton("🚀 开始导入 SQLite")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #48bb78;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 14px;
                font-size: 15px;
                font-weight: 600;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #38a169;
            }
            QPushButton:pressed {
                background-color: #2f855a;
            }
            QPushButton:disabled {
                background-color: #a0aec0;
                cursor: not-allowed;
            }
        """)
        self.import_btn.clicked.connect(self.import_to_sqlite)
        self.import_btn.setDisabled(True)  # 初始禁用（未选文件）
        self.main_layout.addWidget(self.import_btn)

        # 5. 日志输出区域
        log_label = QLabel("导入日志：")
        log_label.setStyleSheet("font-size: 14px; color: #4a5568; margin-top: 15px;")
        self.main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 12px;
                background-color: white;
                color: #2d3748;
                font-family: Consolas, monospace;
            }
        """)
        self.log_text.setReadOnly(True)  # 只读
        self.log_text.setMaximumHeight(120)
        self.main_layout.addWidget(self.log_text)

    def on_select_file(self):
        """选择Excel文件，自动加载工作表名"""
        global EXCEL_FILE_PATH
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Excel 文件", "", "Excel 文件 (*.xlsx *.xls)"
        )
        if file_path:
            EXCEL_FILE_PATH = file_path
            self.excel_path_input.setText(file_path)
            self.log(f"已选择Excel文件：{file_path}")

            # 尝试读取工作表名
            try:
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names  # 自动获取所有工作表名
                self.sheet_combo.clear()
                self.sheet_combo.addItems(sheet_names)  # 填充下拉框
                if sheet_names:  # 确保有工作表
                    self.sheet_combo.setCurrentIndex(0)  # 选择第一个工作表
                self.log(f"成功读取工作表：{', '.join(sheet_names)}")
                self.import_btn.setDisabled(False)  # 启用导入按钮
            except Exception as e:
                QMessageBox.warning(self, "读取失败", f"无法读取Excel文件：{str(e)}")
                self.log(f"读取工作表失败：{str(e)}")
        else:
            self.log("用户取消了文件选择")

    def import_to_sqlite(self):
        """核心逻辑：专门处理Excel五位数日期序列号，修复闰年差异，转标准日期"""
        # 获取用户输入
        db_name = self.db_name_input.text().strip()
        table_name = self.table_name_input.text().strip()
        sheet_name = self.sheet_combo.currentText()

        # 输入校验
        if not db_name:
            QMessageBox.warning(self, "输入错误", "请输入数据库名！")
            return
        if not table_name:
            QMessageBox.warning(self, "输入错误", "请输入表名！")
            return
        if not EXCEL_FILE_PATH:
            QMessageBox.warning(self, "路径错误", "请先选择Excel文件！")
            return

        self.log("开始导入数据...")
        self.import_btn.setDisabled(True)  # 防止重复点击

        try:
            # 1. 读取Excel数据（按字符串读取，避免pandas自动转换序列号）
            self.log(f"正在读取工作表：{sheet_name}")
            df = pd.read_excel(
                EXCEL_FILE_PATH,
                sheet_name=sheet_name,
                parse_dates=False,  # 禁用自动日期解析（我们手动处理序列号）
                na_filter=False,    # 保留原始空值
                dtype=str           # 所有列先按字符串读取，避免数值丢失
            )
            self.log(f"成功读取数据：{df.shape[0]} 行 × {df.shape[1]} 列")

            # 2. 核心：手动指定日期列（替换成你的Excel日期列名！！！）
            # 重点：把下面的 "日期" 改成你Excel中实际的日期列名（比如 "创建日期"、"跟进日期"）
            DATE_COL_NAMES = ["日期","最近跟进日期"]  # 可以多个日期列，比如 ["日期", "最近跟进日期"]
            
            # 处理每个日期列的五位数序列号
            date_columns = []
            for col in DATE_COL_NAMES:
                if col not in df.columns:
                    self.log(f"⚠️  未找到日期列「{col}」，跳过处理")
                    continue

                self.log(f"正在处理日期列「{col}」（五位数序列号转日期）")
                # 步骤1：将字符串格式的序列号转为数值
                df[col] = pd.to_numeric(df[col], errors="coerce")  # 非数字转NaN

                # 步骤2：修复Excel闰年bug，转换为标准日期
                # Excel bug：错误认为1900年是闰年，比实际多算2天，所以减2
                df[col] = pd.to_datetime('1900-01-01') + pd.to_timedelta(df[col] - 2, unit='D')

                # 步骤3：过滤无效日期（只保留2000年之后的合理日期）
                valid_mask = df[col].dt.year >= 2000
                df.loc[~valid_mask, col] = pd.NaT  # 无效日期设为NaT

                # 步骤4：统一格式为 "YYYY-MM-DD 00:00:00"，空值填空字符串
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

                date_columns.append(col)
                # 打印前3行结果，验证转换效果
                self.log(f"  列「{col}」前3行转换结果：{df[col].head(3).tolist()}")

            if not date_columns:
                self.log("⚠️  未成功处理任何日期列，请检查日期列名是否正确")
            else:
                self.log(f"✅ 成功处理日期列：{date_columns}（格式：YYYY-MM-DD 00:00:00）")

            # 3. 连接SQLite数据库
            conn = sqlite3.connect(db_name)
            self.log(f"成功连接/创建SQLite数据库：{db_name}")

            # 4. 构建字段类型映射（日期列存为TEXT，确保格式稳定）
            dtype_map = {col: "TEXT" for col in date_columns}

            # 5. 写入数据库
            df.to_sql(
                name=table_name,
                con=conn,
                if_exists='replace',
                index=False,
                chunksize=1000,
                dtype=dtype_map,
                method="multi"
            )
            self.log(f"成功导入数据到表：{table_name}")

            # 6. 验证结果
            cursor = conn.cursor()
            # 查表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            table_struct = cursor.fetchall()
            self.log("表结构（字段名+类型）：")
            for col_id, col_name, col_type, notnull, dflt_value, pk in table_struct:
                self.log(f"  {col_name}: {col_type}")
            # 查前3行数据
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            self.log("表中前3行数据：")
            for row in rows:
                self.log(str(row))

            conn.close()
            QMessageBox.information(
                self,
                "导入成功",
                f"数据已成功导入SQLite！\n数据库：{db_name}\n表名：{table_name}\n日期列已从五位数序列号转为标准格式"
            )
            self.log("✅ 数据导入完成！")

        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"导入过程出错：{str(e)}")
            self.log(f"❌ 导入失败：{str(e)}")
        finally:
            self.import_btn.setDisabled(False)  # 恢复按钮状态

    def log(self, message):
        """日志输出到文本框"""
        self.log_text.append(f"[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        # 自动滚动到最新日志
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExcelToSQLiteWindow()
    window.show()
    sys.exit(app.exec_())