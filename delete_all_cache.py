import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def clear_all_cache():
    """
    Delete all cache entries with the pattern 'query_hash:*'.
    """
    pattern = "conversation:*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
    print("All cache entries deleted.")

if __name__ == "__main__":
    clear_all_cache()