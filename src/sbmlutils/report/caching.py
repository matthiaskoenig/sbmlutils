import binascii
import uuid
from datetime import datetime
from functools import lru_cache
from hashlib import md5, sha256


JSON_REPORT_CACHE = {}


def create_job_id(file_contents):
    if isinstance(file_contents, str):
        file_contents = file_contents.encode()
    hex_content = binascii.hexlify(file_contents)
    hex_hash = (md5(hex_content).hexdigest())[:16]
    return uuid.UUID(bytes=hex_hash.encode(), is_safe=True)


def get_report_from_cache(uuid: str):
    try:
        report = JSON_REPORT_CACHE[uuid]
        print("data in cache!")
        return report
    except:
        raise KeyError("Report with specified UUID does not exist in cache")


def cache_report(uuid: str, report: dict):
    JSON_REPORT_CACHE[uuid] = report


def generate_job_id(file_contents):
    encoded_file_contents = str(file_contents).encode("utf-8")
    timestamp = str(datetime.now())

    job_id = sha256((encoded_file_contents + timestamp).encode("utf-8"))

    return job_id


def generate_file_hash(file_contents):
    encoded_file_contents = str(file_contents).encode("utf-8")
    file_hash = sha256(encoded_file_contents)

    return file_hash


"""
WORK IN PROGRESS
@lru_cache()
def _write_to_file_and_generate_report(
    filename: str, file_content: str, mode: str
) -> Dict:
    content = {}
    with open(path, mode) as sbml_file:
        sbml_file.write(file_content)
        content = _content_for_source(source=path)
    return content
"""
