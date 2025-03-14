from semanticscholar import AsyncSemanticScholar
__debug = AsyncSemanticScholar.debug  # 是一个property对象


# 定义一个新的 setter 函数
def debug_setter(self, debug: bool) -> None:
    # print(f"hijack {self} {debug}")
    self._debug = debug


# 替换原有的 setter 方法
# 必需是<类>.debug 来设置
AsyncSemanticScholar.debug = property(AsyncSemanticScholar.debug.fget, debug_setter)
print(f'已修改 {__debug} 在文件 {__file__}')
