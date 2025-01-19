import os.path

from scidownl import scihub_download

from download.common_tool import make_uname_for_file


def download_pdf(paper, paper_type, save_dir, logger):
    name = make_uname_for_file()
    out = os.path.join(save_dir, name)
    scihub_download(paper, paper_type=paper_type, out=out)
    if os.path.exists(out):
        logger.debug(f'scidownl 下载完成 {paper}')
        return name
    else:
        raise DownloadFailed(f'scidownl下载失败')


class DownloadFailed(Exception):
    pass



