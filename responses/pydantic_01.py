from collections import OrderedDict


class MetaModel(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return OrderedDict()

    def __new__(mcs, name, bases, namespace):
        # Inherit fields from parent models
        fields = OrderedDict()
        for base in reversed(bases):
            if hasattr(base, "fields"):
                fields.update(base.fields)

        # Add current model's annotated fields
        annotations = namespace.get("__annotations__", {})
        fields.update(annotations)

        namespace["fields"] = fields
        return super().__new__(mcs, name, bases, namespace)


class BaseModel(metaclass=MetaModel):
    def __init__(self, **data):
        # We only assign data that is defined in the 'fields' registry
        for name in self.fields:
            value = data.get(name)
            setattr(self, name, value)

    def dict(self, include=None, exclude=None, by_alias=False):
        """
        Recursively converts the model and nested models into a dictionary.
        """
        output = {}

        # Accessing optional Config for alias mapping
        config = getattr(self, "Config", None)
        alias_map = getattr(config, "fields", {}) if config else {}

        for name in self.fields:
            # 1. Apply Filtering Logic
            if include is not None and name not in include:
                continue
            if exclude is not None and name in exclude:
                continue

            value = getattr(self, name)

            # 2. Recursive Serialization for Nested Models
            if isinstance(value, BaseModel):
                value = value.dict(include=include, exclude=exclude, by_alias=by_alias)
            elif isinstance(value, list):
                # Handle lists of models
                value = [
                    v.dict(include=include, exclude=exclude, by_alias=by_alias) if isinstance(v, BaseModel) else v
                    for v in value
                ]

            # 3. Resolve Key Name (Actual name vs Alias)
            key = alias_map.get(name, name) if by_alias else name
            output[key] = value

        return output

    def __repr__(self):
        attrs = ", ".join(f"{k}={getattr(self, k)!r}" for k in self.fields)
        return f"<{self.__class__.__name__} {attrs}>"
