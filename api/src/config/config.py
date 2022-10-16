
PAPERS_DATA_DIR_PATH = "/data/"
PAPERS_DATA_FILE = "papers-with-abstracts.json.gz" # https://paperswithcode.com/media/about/papers-with-abstracts.json.gz
LINKS_CODE_PAPERS_FILE = "links-between-papers-and-code.json.gz" # https://paperswithcode.com/media/about/links-between-papers-and-code.json.gz

MODEL_SERVING_SERVICE_CONFIG = {
    'ttl': 60*5, # lifetime period of live model
    'min_port': 5001, # min port in range
    'max_port': 5999, # max port in range
    'max_concurrent_models': 5, # max number of running models
    'max_retries': 6 # max number of retries on model prediction (using exponential algo.)
}

MODEL_UPLOAD_SERVICE_CONFIG = {
    'max_model_size': 1024, # max zip file size
    'max_concurrent_uploads_all': 1, #max number of concurrent model uplaods on the platform
    'max_concurrent_uploads_user': 1 #max number of concurrent model uplaods per user on the platform
}