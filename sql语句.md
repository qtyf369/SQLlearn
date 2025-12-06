### 第一步：巩固 DML（数据操纵语言）—— 日常用得最多

```sql
-- 1. 多条件：查 性别女 + 总学分≥85 + 年龄≤22 的学生
SELECT sname, totalcredit, age FROM student 
WHERE sex = '女' AND totalcredit ≥ 85 AND age ≤ 22;

-- 2. 范围：查 学号在 001001-001005 之间的学生
SELECT * FROM student WHERE sno BETWEEN '001001' AND '001005';

-- 3. 模糊查询：查 姓名含“小”字的学生（%匹配任意字符，_匹配单个字符）
SELECT * FROM student WHERE sname LIKE '%小%';

-- 4. 排序+限制：查 总学分前3的学生（降序）
SELECT sname, totalcredit FROM student 
ORDER BY totalcredit DESC LIMIT 3; 

-- 批量插入（比单条插入高效）
INSERT INTO student (sno, sname, sex) 
VALUES ('001008', '郑十', '男'), ('001009', '王十一', '女');

-- 安全更新（用主键/唯一键限制，避免误改全表）
UPDATE student SET age = 21 WHERE sno = '001008'; -- 用 sno 定位，绝对安全

-- 删重复数据（保留一条）
DELETE FROM student 
WHERE sno NOT IN (SELECT MIN(sno) FROM student GROUP BY sname);
```

### 第二步，学 DQL 进阶 + 聚合查询 —— 能做 “数据统计”





#### 常用聚合函数

#### `COUNT()`：统计数量；`SUM()`：求和；`AVG()`：求平均；`MAX()`/`MIN()`：求最大 / 最小；

```sql
-- 1. 统计学生总数（排除 NULL）
SELECT COUNT(*) AS total_student FROM student;

-- 2. 统计女生的平均总学分
SELECT AVG(totalcredit) AS girl_avg_credit 
FROM student WHERE sex = '女';

-- 3. 统计各性别的学生数和总学分总和
SELECT 
  sex, -- 分组字段
  COUNT(*) AS num, -- 每组人数
  SUM(totalcredit) AS total_credit -- 每组总学分
FROM student 
GROUP BY sex; -- 按性别分组
```

#### 用 `HAVING` 筛选分组后的结果（比如 “统计平均学分≥85 的性别”）：

```sql
SELECT sex, AVG(totalcredit) AS avg_credit 
FROM student 
GROUP BY sex 
HAVING avg_credit ≥ 85; -- 筛选分组后的结果（不能用 WHERE）
```

### 第三步：学约束与索引 —— 让表更 “规范”+ 查询更快

#### 1. 约束（Constraint）—— 保证数据正确性

之前只学了 `PRIMARY KEY`（主键）、`NOT NULL`（非空）、`DEFAULT`（默认值），还要学：

* `UNIQUE`：唯一约束（比如手机号不能重复）；

* `FOREIGN KEY`：外键约束（关联两个表，比如 “学生表” 关联 “班级表”）；
  示例：

```sql
-- 1. 给手机号加唯一约束（不能重复）
ALTER TABLE student ADD UNIQUE (phone);

-- 2. 建班级表（主表）
CREATE TABLE class (
  class_id CHAR(4) PRIMARY KEY COMMENT '班级编号',
  class_name VARCHAR(20) NOT NULL COMMENT '班级名称'
);

-- 3. 学生表加外键（关联班级表）
ALTER TABLE student 
ADD COLUMN class_id CHAR(4) COMMENT '班级编号',
ADD FOREIGN KEY (class_id) REFERENCES class(class_id); -- 关联班级表的主键
```

#### 2. 索引（Index）—— 让查询更快

索引是 “数据的目录”，比如给 `sno`（学号）加索引，查询 `WHERE sno='001002'` 会瞬间定位，不用全表扫描；

```sql
-- 给学号加普通索引（查询快）
CREATE INDEX idx_student_sno ON student(sno);

-- 给姓名加全文索引（支持模糊查询加速）
CREATE FULLTEXT INDEX idx_student_sname ON student(sname);
```

### 第四步：学 多表关联查询 —— 解决 “跨表取数据”

实际工作中数据不会存在一张表（比如 “学生表”“班级表”“成绩表”），需要跨表查询：

#### 1. 核心语法：JOIN（内连接、左连接、右连接）

示例（学生表 + 班级表）：

```sql
-- 内连接：查“有班级的学生”及其班级名称（只显示两边都有的数据）
SELECT s.sname, s.sno, c.class_name 
FROM student s -- 表别名 s（简化写法）
JOIN class c -- 表别名 c
ON s.class_id = c.class_id; -- 连接条件（学生表的班级编号 = 班级表的班级编号）

-- 左连接：查“所有学生”及其班级名称（没有班级的学生也显示，class_name 为 NULL）
SELECT s.sname, c.class_name 
FROM student s
LEFT JOIN class c ON s.class_id = c.class_id;
```

* 目标：能从多个关联表中取需要的数据，比如 “查 2 班学生的成绩排名”。

### 第五步：学 事务与存储过程 —— 处理 “复杂业务”

#### 1. 事务（Transaction）—— 保证多步操作的原子性

比如 “转账”（扣钱 + 加钱），要么都成功，要么都失败，不会出现 “扣了钱没加钱” 的情况：

```sql
-- 开启事务
START TRANSACTION;

-- 步骤1：A学生扣10学分
UPDATE student SET totalcredit = totalcredit - 10 WHERE sno = '001001';

-- 步骤2：B学生加10学分
UPDATE student SET totalcredit = totalcredit + 10 WHERE sno = '001002';

-- 确认无误，提交事务（数据生效）
COMMIT;

-- 如果出错，回滚事务（恢复到操作前状态）
-- ROLLBACK;
```

* 核心：ACID 特性（原子性、一致性、隔离性、持久性），记住 “要么全成，要么全败”。

#### 2. 存储过程（Stored Procedure）—— 封装重复的复杂逻辑

比如 “批量添加学生并自动分配班级”，把逻辑写成存储过程，调用一次就行：

```sql
-- 创建存储过程
DELIMITER // -- 临时修改结束符（默认 ; 会冲突）
CREATE PROCEDURE add_students(IN num INT) -- 入参：添加学生数量
BEGIN
  DECLARE i INT DEFAULT 1;
  WHILE i <= num DO
    INSERT INTO student (sno, sname) 
    VALUES (CONCAT('001', LPAD(i, 3, '0')), CONCAT('学生', i));
    SET i = i + 1;
  END WHILE;
END //
DELIMITER ; -- 恢复默认结束符

-- 调用存储过程（添加5个学生）
CALL add_students(5);
```

* 目标：减少重复写 SQL，提高开发效率。

### 六、学习方法：边练边用，避免 “只看不学”

1. **用真实场景练手**：
   * 自己建 3 张关联表（比如 “学生表 + 班级表 + 成绩表”），模拟需求：
     * 查 “数学成绩≥90 分的学生姓名 + 班级”；
     * 统计 “每个班级的平均分排名”；
     * 批量修改 “某班级所有学生的入学日期”。
2. **用工具辅助**：
   * DBeaver 中可以用「可视化设计表」验证 DDL（右键表→编辑表）；
   * 执行 SQL 后看「执行计划」（DBeaver 中选中 SQL→右键→执行计划），理解索引是否生效。
3. **踩坑记录**：
   * 比如 “分组查询后不能用 WHERE 筛选”“外键关联时主表数据不能随便删”，把错误和解决方案记下来。
4. **推荐资源**：
   * 入门：W3School MySQL 教程（边看边练，简单易懂）；
   * 进阶：《MySQL 必知必会》（薄书，全是实用技巧，适合新手）；
   * 实操：LeetCode 数据库题库（100+ 题，从简单到复杂，练完能应对工作）。

### 总结学习路径

`巩固 DML 增删改查 → 聚合查询与分组 → 约束与索引 → 多表关联查询 → 事务与存储过程`

按这个顺序学，每一步都能解决 “实际问题”，不会觉得枯燥。每学一个知识点，就用你的 `student` 表或新建表练手，2-3 周就能掌握工作中 80% 的 MySQL 技能～ 如果学到某一步卡壳（比如多表连接搞不懂），可以随时问，我给你针对性讲例子！


