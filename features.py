import importlib
import logging as log
import os
import sys

import yaml

import config
import variables
from db.JamlEntities import Config
from utils.utils import assign
from variables import FEATURES, METHODS_META, METHODS_NAMES


def load_features():
    cfg = Config.objects(name=config.PROFILE).first()
    if 'version' in cfg.settings:
        config.VERSION = cfg.settings['version']
    else:
        cfg.settings['version'] = config.VERSION
        cfg.save()

    _methods = {}

    for version in ['basic', 'standard', 'enterprise']:
        _ml_methods, _methods_map = None, None
        features_yml = os.path.join(os.path.dirname(os.path.realpath(__file__)), version, 'features.yml')
        try:
            with open(features_yml, "r") as f:
                cfg = yaml.safe_load(f)
                FEATURES.update(cfg['features'])
                _methods_map = cfg['methods-map'] if 'methods-map' in cfg else None
                _ml_methods = cfg['features']['ml-methods']['value'] if 'ml-methods' in cfg['features'] else None
        except FileNotFoundError:
            continue

        if _methods_map:
            for tgt in _methods_map.keys():
                parts = tgt.split('.')
                if not parts[0]:
                    parts[0] = version
                tgt = '.'.join(parts)

                if tgt not in sys.modules:
                    print(f" [+] {tgt}")
                    tgt_module = importlib.import_module(tgt)
                else:
                    tgt_module = sys.modules[tgt]

                for t, s in _methods_map[tgt].items():
                    parts = s.split('.')
                    if not parts[0]:
                        parts[0] = version
                    sf = parts.pop()
                    sm = '.'.join(parts)
                    if sm not in sys.modules:
                        print(f" [+] {sm}")
                        src_module = importlib.import_module(sm)
                    else:
                        src_module = sys.modules[sm]

                    print(f"{tgt}.{t} := {sm}.{sf}")
                    tgt_module.__setattr__(t, src_module.__getattribute__(sf))

        if _ml_methods:
            for m in _ml_methods:
                try:
                    # Call dynamically as otherwise it'd be already bound to a wrong module's method
                    model = getattr(sys.modules['models'], 'create_model')(m)
                    if model:
                        _methods[model.name] = model
                except Exception as ex:
                    log.warning(f"Cannot load {version}.models.{m}: {ex}")

        if version != 'available' and version == config.VERSION:
            break

    variables.METHODS.clear()
    METHODS_NAMES.clear()
    METHODS_META.clear()

    variables.METHODS.extend(_methods.values())

    for m in variables.METHODS:
        METHODS_NAMES.append(m.name)
        METHODS_META[m.name] = m.title


def all_features():
    features, prev_values = {}, {}

    for version in ['basic', 'standard', 'enterprise']:
        features_yml = os.path.join(os.path.dirname(os.path.realpath(__file__)), version, 'features.yml')
        try:
            with open(features_yml, "r") as f:
                cfg = yaml.safe_load(f)
        except FileNotFoundError:
            continue

        for feature, cfg_value in cfg['features'].items():
            cfg_value['feature'] = feature
            if 'value' in cfg_value:
                cfg_value[version] = cfg_value['value']
                del cfg_value['value']
            else:
                cfg_value[version] = True

            prev_values[feature] = cfg_value[version]

            if feature in features:
                assign(features[feature], cfg_value)
            else:
                features[feature] = cfg_value

        for feature in features:
            if feature not in cfg['features']:
                features[feature][version] = prev_values[feature]

    return list(features.values())


def feature(name):
    return FEATURES[name]['value'] if name in FEATURES else None
