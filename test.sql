CREATE DATABASE if not exists student;

insert into test (id, name, age) values ('0005', '张九', 18);

insert into test (name, age) values ('李四', 19);

select * from test;

delete from test where id = 2;

alter table test MODIFY column id INT;

ALTER TABLE test MODIFY COLUMN id CHAR(4);