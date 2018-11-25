from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

PERFECT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
Base = declarative_base()


class ModelBase:

    def to_dict(self, placeholder_column=None, need_params=None):
        if need_params:
            keys = need_params
        elif hasattr(self, "__mapper__"):
            keys = [prop.key for prop in self.__mapper__.iterate_properties]
        else:
            keys = list(vars(self).keys())
        if placeholder_column:
            keys.remove(placeholder_column)
        format_data = {}
        for key in keys:
            format_data[key] = getattr(self, key)
            if isinstance(format_data[key], datetime):
                format_data[key] = format_data[key].strftime(PERFECT_TIME_FORMAT)
            format_data[key] = format_data[key] if format_data[key] else ""
        return format_data
