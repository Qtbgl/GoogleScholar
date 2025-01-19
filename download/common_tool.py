import uuid


def make_uname_for_file():
    # 生成一个 UUID, 取前 8 个字符
    uname = str(uuid.uuid4())[:8]
    return uname


class GoodbyeBecauseOfError(Exception):
    pass


def get_errs_info(errs):
    return '; '.join(map(str, errs)) if len(errs) else None
