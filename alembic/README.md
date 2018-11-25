
# sqlalchemy和alembic的使用

1. 安装环境所依赖的库
   pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

1. 在 shell 里面 cd 到项目根目录执行
   
   alembic init alembic 

### 配置文件 ###

2. 修改 alembic.ini 设置数据库连接
   sqlalchemy.url = driver://user:pass@localhost/dbname
   改为
   sqlalchemy.url = mysql+mysqlconnector://root:root@127.0.0.1:3306/test?charset=utf8mb4

   env.py，其中配置models
   target_metadata = None
   改为
   import os
   import sys
   sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
   from app.models import models
   target_metadata = models.Base.metadata


### 生成增量脚本 ###

    alembic revision --autogenerate -m "1.0.0"

### 增量升级 ###

    # 升级到最新版本
    alembic upgrade head

    # 升级到 下一个 版本
    alembic upgrade +1

    # 打印升级到最新版本的 SQL 脚本
    alembic upgrade head --sql

### 增量降级 ###

    # 降级到 前一个 版本
    alembic downgrade -1

#### 脚本的封装 ###
#!/bin/sh
PYENV_PATH="/opt/pyenv/alembic_env"
${PYENV_PATH}/bin/python -m alembic.config $@

#### Create db sql statements ####

create database test;

GRANT ALL PRIVILEGES ON test.* TO 'root'@'localhost' \
  IDENTIFIED BY 'root';
GRANT ALL PRIVILEGES ON test.* TO 'root'@'%' \
  IDENTIFIED BY 'root';
