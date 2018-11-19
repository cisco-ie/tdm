import os
import logging

caches = {}

def get_cache(cache_id):
    if cache_id in caches.keys():
        return caches[cache_id]
    else:
        caches[cache_id] = get_cache_path(cache_id)
    return caches[cache_id]

def get_cache_path(cache_id, cache_env='CACHE_BASE_PATH', cache_base='/cache/'):
    cache_base_path = os.environ.get(cache_env)
    if not cache_base_path:
        cache_base_path = cache_base
    if os.path.exists(cache_base_path):
        if not os.path.isdir(cache_base_path):
            raise Exception('Cache base %s is not a folder!' % cache_base_path)
    else:
        os.mkdir(cache_base_path)
    cache_path = os.path.join(cache_base_path, cache_id)
    if os.path.exists(cache_path):
        if not os.path.isdir(cache_path):
            raise Exception('Cache %s is not a folder!' % cache_path)
    else:
        os.mkdir(cache_path)
    return cache_path
