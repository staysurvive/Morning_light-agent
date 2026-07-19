# 文件 test_sample.py
def add(x, y):
    return x + y

def test_add():
    # assert 为断言机制，判断表达式是否为true true则为测试成功 false则为测试失败
    print("哈哈哈")
    assert add(2, 3) == 5

def test_add_same_values():
    assert add(2, 2) == 4
