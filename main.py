import json
import yaml

# Force populate combiner registry:
import ludwig.combiners.combiners  # noqa: F401
from ludwig.schema.combiners.utils import get_combiner_registry
from ludwig.schema.features.preprocessing.utils import preprocessing_registry
from ludwig.schema.trainer import trainer_schema_registry
from ludwig.schema.optimizers import optimizer_registry


def flatten(d, prefix=""):
    o_dict = {}
    for k, v in d.items():
        key = k
        if prefix:
            key = f"{prefix}.{key}"
        o_dict[key] = v

        if v is not None and hasattr(v, "load_default"):
            default = v.load_default
            if callable(default):
                default = default()
            
            cls = type(default)
            if hasattr(cls, "get_class_schema"):
                schema = cls.get_class_schema()()
                if "type" not in schema.fields:
                    o_dict.update(flatten(schema.fields, key))

    return o_dict


def dump_value(v):
    return json.dumps(v).lstrip('\"').rstrip('\"')


def is_internal(field):
    param_meta = field.metadata.get("parameter_metadata", {})
    if param_meta and param_meta.get("internal_only"):
        return True
    return False


def expected_impact(field):
    param_meta = field.metadata.get("parameter_metadata", {})
    if not param_meta:
        return 0
    return param_meta.get("expected_impact", 0)


def field_sort_order(name, field):
    if name == "type":
        # Type param always comes first in the sort order
        return -100
    return -expected_impact(field)


def sort_fields(fields_dict):
    return {
        k: v for k, v in
        sorted(fields_dict.items(), key=lambda x: field_sort_order(*x))
    } 


def define_env(env):
    @env.macro
    def get_feature_preprocessing_schema(type: str):
        return preprocessing_registry[type]

    @env.macro
    def get_combiner_schema(type: str):
        return get_combiner_registry()[type].get_schema_cls()
    
    @env.macro
    def get_trainer_schema(model_tyoe: str):
        return trainer_schema_registry[model_tyoe]
    
    @env.macro
    def get_optimizer_schemas():
        return [v[1] for v in optimizer_registry.values()]
    
    @env.macro
    def schema_class_to_yaml(cls, sort_by_impact=True):
        schema = cls.get_class_schema()()
        internal_fields = {n for n, f in schema.fields.items() if is_internal(f)}
        d = {k: v for k, v in cls().to_dict().items() if k not in internal_fields}

        if sort_by_impact:
            sorted_fields = flatten(sort_fields(schema.fields))
            d = {k: d[k] for k in sorted_fields.keys() if k in d}

        return yaml.safe_dump(d, indent=4, sort_keys=False)
    
    @env.macro
    def schema_class_to_fields(cls, exclude=None):
        exclude = exclude or []
        schema = cls.get_class_schema()()
        d = flatten(sort_fields(schema.fields))
        return {
            k: v for k, v in d.items() if k not in exclude
        }
    
    @env.macro
    def render_field(name, field, details):
        if is_internal(field):
            return ""

        has_default = True
        default_value = field.dump_default
        if isinstance(default_value, dict):
            if "type" in default_value:
                default_value = {"type": default_value["type"]}
            else:
                has_default = False

        default_str = ""
        if has_default:
            default_str = f"(default: `{dump_value(default_value)}`)"
        
        s = f"- **`{ name }`** {default_str}: { field.metadata['description'] }"
        if field.validate is not None and hasattr(field.validate, "choices"):
            options = ", ".join([f"`{dump_value(opt)}`" for opt in field.validate.choices])
            s += f" Options: {options}."

        if details is not None and name in details:
            s += f" {details[name]}"

        return s
    
    @env.macro
    def merge_dicts(d1, d2):
        return {**d1, **d2}