# 数据库配置
db_url = 'mysql+mysqlconnector://root:root@127.0.0.1:3306/test?charset=utf8mb4'  # 数据库连接串
db_echo = False  # 是否回显SQL
db_echo_pool = False  # 数据库连接池是否记录 checkouts/checkins 操作
db_pool_size = 100  # 数据库连接池中保持打开的连接数量
db_pool_recycle = 3600  # 数据库连接池在连接被创建多久（单位秒）以后回收连接
db_create = False  # 是否自动创建数据库表
db_commit = True  # 是否事务自动提交
