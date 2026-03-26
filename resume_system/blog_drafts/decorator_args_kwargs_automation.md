# 자동화 코드가 갑자기 멈추는 진짜 이유 — 파이썬 데코레이터와 *args를 모르면 생기는 일

> 작성일: 2026-03-21
> 태그: Python, 자동화, 데코레이터, args, kwargs, 초보자

---

## 들어가며

노코드 자동화 툴로 시작했다가 어느 순간 막히는 경험, 해봤을 거다.
Make나 Zapier로 잘 되던 게 Claude API, GPT API를 붙이는 순간 이상하게 안 돌아간다.
에러 메시지를 보면 `TypeError: got an unexpected keyword argument` 같은 게 나온다.

이 글은 그 이유를 설명한다.
핵심은 **데코레이터**와 **`*args`, `**kwargs`** 두 개다.

---

## 1. 문제 제시 — 왜 자동화 코드는 갑자기 안 돌아갈까?

Claude API로 자동화 파이프라인을 만든다고 해보자.
여러 도구(tool)를 등록하고, API 응답이 오면 적절한 함수를 실행해야 한다.

### 문제 1: 함수를 실행하는 쪽에서 인자를 모른다

```python
def send_slack(message):
    print(f"Slack: {message}")

def save_to_notion(title, content):
    print(f"Notion: {title} - {content}")

# 어떤 함수가 올지 모르는 상태에서 실행하는 dispatcher
def run_tool(func):
    func()  # 인자를 어떻게 넘길지 모름 → TypeError 발생
```

`send_slack`은 인자가 1개, `save_to_notion`은 2개다.
`func()`로 그냥 호출하면? **바로 TypeError.**

해결은 간단하다 — `**kwargs`로 받아서 그대로 넘긴다:

```python
def run_tool(func, **kwargs):
    func(**kwargs)

run_tool(send_slack, message="배포 완료!")
run_tool(save_to_notion, title="회의록", content="내일 미팅 확인")
```

좋다. 근데 이제 새로운 요구가 생긴다.
모든 함수 실행마다 로그를 찍고 싶다. 함수가 10개면 10번 복붙해야 하나?

### 문제 2: 모든 함수에 같은 기능을 붙이고 싶다

```python
# 이 패턴을 10개 함수에 반복?
def send_slack(message):
    print("[LOG] 실행 시작")
    print(f"Slack: {message}")
    print("[LOG] 실행 완료")
```

여기서 **데코레이터** 아이디어가 나온다.
"함수를 받아서 기능을 붙인 새 함수로 교체하자."

```python
def add_log(func):
    def wrapper():              # ← 문제: 인자가 없음
        print("[LOG] 실행 시작")
        func()                  # ← TypeError 다시 발생
        print("[LOG] 실행 완료")
    return wrapper
```

`wrapper()`에 인자가 없어서 **또 같은 문제가 생긴다.**
`**kwargs`가 필요한 이유가 두 번째로 등장하는 순간이다.

---

## 2. 내가 직접 헷갈린 포인트

공부하면서 두 군데서 막혔다.

**첫 번째:** `**kwargs`와 `*kwargs`의 차이

```python
kwargs = {"a": 1, "b": 2}

func(*kwargs)   # ← 이거 쓴 적 있음
func(**kwargs)  # ← 이게 맞음
```

`*kwargs`(별 하나)를 쓰면 키 문자열만 들어간다. `"a"`, `"b"`가 위치 인자로 전달되는 것.
`**kwargs`(별 두 개)를 써야 `a=1, b=2`로 전달된다.

실제로 확인해보면:
```python
def test(a, b):
    print(a, b)

kwargs = {"a": 100, "b": 200}

test(*kwargs)   # → a b 출력 (키가 들어감)
test(**kwargs)  # → 100 200 출력 (값이 들어감)
```

**두 번째:** 호출 방식과 출력 결과를 헷갈림

`test(**kwargs)` 내부에서는 `test(a=100, b=200)`으로 변환된다.
근데 출력은 `a=100, b=200`이 아니라 `100 200`이다.

```
test(**kwargs)
→ test(a=100, b=200)   ← 호출 방식 (보이지 않음)
→ print(a, b)
→ 100 200              ← 실제 출력 (이게 결과)
```

---

## 3. 원리 설명 — 함수도 값처럼 다룰 수 있다

### 핵심 1: 함수는 변수에 담을 수 있다

```python
def hello():
    print("안녕")

a = hello   # 함수 자체를 담음 (실행 X)
a()         # 이때 실행됨
```

`hello`는 함수 그 자체, `hello()`는 실행.
이 차이를 이해하면 데코레이터는 자연스럽게 따라온다.

### 핵심 2: 함수를 다른 함수에 넘길 수 있다

```python
def run(func):
    func()

run(hello)  # hello를 인자로 넘김
```

함수도 인자가 된다.

### 핵심 3: 데코레이터 = 함수 바꿔치기 시스템

```python
def add_log(func):
    def wrapper(*args, **kwargs):   # ← *args, **kwargs로 어떤 인자든 받음
        print("[LOG] 실행 시작")
        result = func(*args, **kwargs)  # ← 그대로 전달
        print("[LOG] 실행 완료")
        return result               # ← 반드시 반환
    return wrapper                  # ← 원래 함수를 wrapper로 교체
```

`@add_log`를 쓰면 내부적으로 `hello = add_log(hello)`가 실행된다.
`hello`가 `wrapper`로 바뀌는 것.

### 핵심 4: `*args, **kwargs`가 두 곳에서 똑같이 필요한 이유

문제 1(dispatcher)과 문제 2(wrapper) 모두 같은 이유로 막혔다:
**함수를 받아서 실행하는 쪽이 인자를 미리 알 수 없기 때문이다.**

```python
# dispatcher에서
def run_tool(func, **kwargs):
    return func(**kwargs)       # API 응답의 JSON이 딕셔너리로 오니까

# decorator wrapper에서
def wrapper(*args, **kwargs):
    return func(*args, **kwargs)  # 어떤 함수가 올지 모르니까
```

- `*args` → 위치 인자를 튜플로 묶어서 받고 다시 풀어서 전달
- `**kwargs` → 키워드 인자를 딕셔너리로 묶어서 받고 다시 풀어서 전달
- `return` → 반드시 붙여야 함. 안 붙이면 결과가 `None`으로 사라짐

### 핵심 5: 데코레이터 2종류

| 종류 | 구조 | 용도 |
|------|------|------|
| wrapper형 | `func` → `wrapper` 반환 | 실행 전후 기능 추가 (로그, 타이머) |
| 등록형 | `func` 그대로 반환 | 함수 목록 관리 (AI 툴 등록) |

등록형은 이렇게 생겼다:
```python
tools = []

def register(func):
    tools.append(func)  # 등록만 하고
    return func         # 원래 함수 그대로 반환 — 실행 변화 없음

@register
def send_slack(message):
    print(f"Slack: {message}")
```

실행은 그대로고, 함수를 목록에만 추가한다.
Claude API 툴 등록할 때 이 패턴이 많이 나온다.

---

## 4. 실무 연결 — 그래서 자동화 코드에서 뭐가 달라지냐

**Claude API, GPT API 자동화에서 자주 쓰는 패턴:**

```python
tools = []

def tool(func):
    tools.append(func)
    return func

@tool
def send_slack(message: str):
    """Slack으로 메시지를 보낸다"""
    pass

@tool
def save_to_notion(title: str, content: str):
    """Notion에 페이지를 저장한다"""
    pass

# API 응답이 오면 이름으로 함수를 찾아서 실행
def run_tool(name, **kwargs):
    func = next(f for f in tools if f.__name__ == name)
    return func(**kwargs)
```

핵심은 `**kwargs`로 받아서 `**kwargs`로 전달하는 것.
API 응답의 JSON 인자가 딕셔너리 형태로 오기 때문이다.

**`return`을 빠뜨리면:**
```python
def wrapper(*args, **kwargs):
    func(*args, **kwargs)  # return 없음
```
함수 결과가 `None`으로 사라진다. 자동화 파이프라인에서 다음 단계로 전달이 안 된다.

---

## 5. 한 줄 정리

> 자동화 툴을 연결하는 것보다, 함수가 어떻게 전달되고 실행되는지를 이해할 때 비로소 내 것이 된다.

---

## 직접 확인해볼 코드

```python
# 이거 실행해보면 모든 개념이 정리된다

def decorator(func):
    def wrapper(*args, **kwargs):
        print(f"[실행 전] {func.__name__} 호출")
        result = func(*args, **kwargs)
        print(f"[실행 후] 결과: {result}")
        return result
    return wrapper

@decorator
def add(a, b):
    return a + b

@decorator
def greet(name, greeting="안녕"):
    return f"{greeting}, {name}!"

add(1, 2)
greet("철수")
greet("영희", greeting="반가워")
```

출력:
```
[실행 전] add 호출
[실행 후] 결과: 3
[실행 전] greet 호출
[실행 후] 결과: 안녕, 철수!
[실행 전] greet 호출
[실행 후] 결과: 반가워, 영희!
```
