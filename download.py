import asyncio
import pathlib
import tempfile
import time

import nodriver as uc


async def download_pdf(pdf_url, unique: pathlib.Path, browser: uc.Browser):
    # 设置下载路径
    await browser.main_tab.set_download_path(unique)

    # 打开pdf网页，自动下载
    print('准备下载', pdf_url)
    page = await browser.get(pdf_url, new_tab=True)

    try:
        # Check if the page has loaded successfully
        print('检查网页是否成功加载')
        start = time.time()
        flag = True
        while True:
            print(f'total_time: {time.time() - start} s')
            # pdf已存在
            pdf_file = list(unique.glob('*.pdf'))
            if len(pdf_file):
                return pdf_file[0]

            # pdf未存在，但有其他文件
            if any(unique.iterdir()):
                print('文件正在下载中', list(unique.iterdir()))
                if time.time() - start >= 120:
                    raise TimeoutError

                await asyncio.sleep(2)
                continue

            # 继续等待网页加载
            now = time.time()
            if now - start >= 90:
                raise TimeoutError

            if page not in browser.tabs:
                # 文件和网页都不存在？
                await asyncio.sleep(2)
            else:
                state = await page.evaluate("document.readyState")
                print(f'state={state}')
                # 检查网页是否需要重新加载
                if state == 'complete':
                    if flag:  # 保护成功加载情况
                        flag = False
                        await asyncio.sleep(3)
                    else:
                        await page.reload()
                        print('reloading')
                        flag = True
                        await asyncio.sleep(10)
                else:
                    await asyncio.sleep(2)

    finally:
        # 网页加载成功后
        if page in browser.tabs:
            print('页面未自动关闭，尝试关闭')
            await page.close()


async def main():
    # url = 'https://onlinelibrary.wiley.com/doi/pdf/10.1155/2016/6215085'
    # url = 'https://onlinelibrary.wiley.com/doi/pdfdirect/10.1155/2016/6215085'
    # url = 'https://e-space.mmu.ac.uk/626674/1/2020-%20IEEE%20JSAC-%20Pulmonary%20Nodule%20Classification%20Based%20on.pdf'
    # url = 'https://arxiv.org/pdf/1801.09555'
    # url = 'https://arxiv.org/pdf/1701.07274'
    url = 'https://discovery.ucl.ac.uk/id/eprint/10083557/1/1708.05866v2.pdf'

    # 当前文件路径拼接上 data\browser\userdata
    from data.path_config import user_data_dir, download
    # 用户设置chrome自动下载pdf
    browser = await uc.start(user_data_dir=user_data_dir)
    try:
        # 在子路径下再另建一个临时目录
        with tempfile.TemporaryDirectory(dir=download) as temp_dir:
            print('临时目录创建在:', temp_dir)
            pdf_file = await download_pdf(url, pathlib.Path(temp_dir), browser)
            print('文件已下载', pdf_file)

    finally:
        browser.stop()


uc.loop().run_until_complete(main())
