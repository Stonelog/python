from app.models.models import User
from json import loads as json_loads
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from app.config import *

SQL_ALCHEMY_ENGINE_CONTAINER = dict()


def json_deserializer(src_str, **kwargs):
    json_str = src_str.decode('utf-8') if isinstance(src_str, bytes) else src_str
    return json_loads(json_str, **kwargs)


def get_sql_alchemy_engine(_db_url):
    if _db_url not in SQL_ALCHEMY_ENGINE_CONTAINER:
        engine = create_engine(_db_url,
                               echo=db_echo,
                               echo_pool=db_echo_pool,
                               pool_size=db_pool_size,
                               pool_recycle=db_pool_recycle,
                               json_deserializer=json_deserializer)
        SQL_ALCHEMY_ENGINE_CONTAINER[_db_url] = engine
    return SQL_ALCHEMY_ENGINE_CONTAINER[_db_url]


class DB(object):

    session = None

    def __init__(self, _db_url):
        """
        提供数据库访问能力
        :param _db_url: 数据库连接串
        """
        engine = get_sql_alchemy_engine(_db_url)
        self.session = sessionmaker(bind=engine)()


def add_user(db_session):
    # Add one user
    user_entries = {
        "name": "test1",
        "email": "test1@qq.com"
    }
    user = User(**user_entries)
    db_session.add(user)
    # Add multiple user
    db_session.add_all([
        User(name="test2", email='test2@qq.com'),
        User(name="test3", email='test3@qq.com'),
    ])


def update_user(update_entry, user):
    """
    :param update_entry: The type is dictionary and the key is the column name
    :param user: app.models.models.User
    :return:
    """
    for key, value in update_entry.items():
        setattr(user, key, value)


def first_query(db_session):
    # #####################first parameter#########################
    # first, returns None when the query does not result
    user_id_100 = db_session.query(User).filter_by(id=100).first()
    print(type(user_id_100))
    # first, returns the first result when querying multiple results
    user_idg_gt_1 = db_session.query(User).filter(User.id > 1).first()
    print(user_idg_gt_1.to_dict())


def one_query(db_session):
    # #####################one parameter#########################
    # Only one record is retrieved,
    # and if no record is found or multiple records are found, an error is reported
    # 1. Failure to find a record throws the following error
    #    sqlalchemy.orm.exc.NoResultFound: No row was found for one()
    try:
        db_session.query(User).filter_by(id=100).one()
    except NoResultFound:
        print("NoResultFound error!")
    # 2. Finding multiple records throws the following error
    #    sqlalchemy.orm.exc.MultipleResultsFound: Multiple rows were found for one()
    try:
        db_session.query(User).filter(User.id > 1).one()
    except MultipleResultsFound:
        print("MultipleResultsFound error!")


def specify_fields_query(db_session):
    # Specify the returned field
    # 1. Filter the results of the query
    query_fields = ["id", "name"]
    users = db_session.query(User).all()
    print([user.to_dict(need_params=query_fields) for user in users])
    # 2. Use Sql statements to query
    users = db_session.query(User.id, User.name).all()
    # The element type is <sqlalchemy.util._collections.result>
    print([dict(zip(user.keys(), user)) for user in users])


if __name__ == '__main__':
    db = DB(_db_url=db_url)
    session = db.session
    # Test add users
    add_user(session)
    # Test Update user info
    update_user_entries = {
        "name": "test4",
    }
    _update_user = session.query(User).filter_by(name="test1").first()
    update_user(update_user_entries, _update_user)
    # Test query user
    first_query(session)
    one_query(session)
    specify_fields_query(session)
    # Use the unwrapped list to pass arguments to filter()
    params = {'name': "test3", "email": "test3@qq.com"}
    conditions = []
    if params.get('name'):
        conditions.append(User.name == params['name'])
    if params.get('email'):
        conditions.append(User.email == params['email'])
    condition_users = session.query(User).filter(*conditions).all()
    print([user.to_dict() for user in condition_users])
    # Use the unwrapped dictionary to pass arguments to filter_by()
    params = {'name': "test3", "email": "test3@qq.com"}
    conditions = {k: v for k, v in params.items()}
    condition_users = session.query(User).filter_by(**conditions).all()
    print([user.to_dict() for user in condition_users])
    # Test delete users
    session.query(User).delete()
    session.commit()
