# 

## 常用 SQL 基础语句（纯净版）



```sql
-- 1. 查指定列

SELECT client_id, 客户姓名, 国家, 日期 FROM client_db.new_quote;

-- 2. 带条件查询（参数化）

SELECT * FROM client_db.new_quote WHERE 国家 = :country;

-- 3. 去重查询

SELECT DISTINCT 国家 FROM client_db.new_quote;

-- 4. 新增列

ALTER TABLE client_db.new_quote ADD COLUMN IF NOT EXISTS 跟进状态 VARCHAR(20) AFTER 国家;

-- 5. 更新数据

UPDATE client_db.new_quote SET 国家 = :new_country WHERE client_id = :cid;

-- 6. 统计总数

SELECT COUNT(*) AS 客户总数 FROM client_db.new_quote;
```

> 
