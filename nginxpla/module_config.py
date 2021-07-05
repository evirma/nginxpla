from nginxpla.storage import LogStorage
import sys
from nginxpla import CUSTOM_MODULES_DIR

try:
    # Python 3
    from collections.abc import MutableSequence
except ImportError:
    # Python 2.7
    from collections import MutableSequence


class ModuleConfig(object):
    def __init__(self, name, module_config, config):
        self.name = name
        self.module_config = module_config
        self.config = config
        self.storage = False
        self.arguments = config.arguments
        self.sql = '' if 'sql' not in module_config else module_config['sql']
        self.reports = [] if 'reports' not in module_config else module_config['reports']

        self.fields = set([])
        if 'fields' in module_config:
            self.fields = set(module_config['fields'])

        self.indexes = set([])
        if 'indexes' in module_config:
            self.indexes = set(module_config['indexes'])

        self.label = '' if 'label' not in module_config else module_config['label']
        self.package = '' if 'package' not in module_config else module_config['package']
        self.class_name = '' if 'class' not in module_config else module_config['class']
        self.options = False if 'options' not in module_config else module_config['options']
        self.instance = False

    def factory(self):
        if self.instance is False:
            sys.path.append(CUSTOM_MODULES_DIR)
            mod = __import__(self.package, fromlist=[self.class_name])
            self.instance = getattr(mod, self.class_name)(self)
        return self.instance

    def get_fields(self):
        return self.fields

    def set_storage(self, storage: LogStorage):
        self.storage = storage

    def is_required(self, search) -> bool:
        fields = set(self.config.fields)
        if not fields:
            return False

        if isinstance(search, set):
            return bool(fields.intersection(search))
        else:
            for field in fields:
                if field == search:
                    return True

        return False


class ModuleList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    def set_storage(self, storage: LogStorage):
        for module in self:
            module.set_storage(storage)

    def fields(self):
        fields = set([])
        for module in self:
            if module.fields:
                fields = fields.union(set(module.fields))

        return fields

    def indexes(self):
        indexes = set([])
        for module in self:
            if module.indexes:
                indexes = indexes.union(set(module.indexes))

        return indexes
