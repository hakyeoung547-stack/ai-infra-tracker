# 파이썬 async/await — "기다리는 시간을 낭비하지 않는다"는 게 무슨 뜻인가

> 작성일: 2026-03-22
> 태그: Python, asyncio, async, await, 비동기, 초보자

---

## 들어가며

처음 `async def`를 봤을 때 드는 생각:

> "이게 일반 함수랑 뭐가 다르지? 그냥 `def`로 하면 안 되나?"

그다음에 이런 에러가 뜬다.

```
RuntimeWarning: coroutine 'main' was never awaited
```

이 에러가 뜨는 이유를 이해하면 async 전체가 보인다.
이 글은 그 지점에서 시작한다.

---

## 1. 문제 제시 — 왜 async가 필요한가?

API 요청을 3개 보내야 한다고 해보자.

```python
import time

def fetch_data(name):
    print(f"{name} 요청 시작")
    time.sleep(2)  # API 응답 대기
    print(f"{name} 완료")

fetch_data("NVDA")
fetch_data("AMD")
fetch_data("TSM")
```

실행하면: 총 6초 걸린다.

근데 생각해보면 이상하다.
3개 요청은 서로 기다릴 필요가 없는데, 왜 하나씩 순서대로 기다리나?

이 낭비를 없애는 게 async의 핵심이다.

---

## 2. async def는 무엇인가

```python
async def work():
    print("작업")
```

이건 그냥 특별한 함수를 하나 만든 거다.
근데 일반 함수랑 결정적인 차이가 있다.

```python
def hello():
    print("안녕")

hello()   # → "안녕" 출력. 바로 실행됨.
```

```python
async def work():
    print("작업")

work()    # → 아무것도 출력 안 됨. 코루틴 객체만 생성됨.
```

`work()`를 호출해도 실행이 되지 않는다.
정확히는 **코루틴(coroutine) 객체**가 만들어진 것이다.

### 코루틴이 뭔가?

"나중에 실행할 비동기 작업표" 정도로 이해하면 된다.

```
일반 함수 호출  → 바로 실행
async 함수 호출 → 코루틴 객체 생성 (아직 실행 안 됨)
```

그래서 이 에러가 뜨는 거다.

```
RuntimeWarning: coroutine 'main' was never awaited
```

번역하면: "main이라는 코루틴 만들어놨는데, 실제로 실행은 안 했어."

---

## 3. await — 코루틴을 실제로 실행시키는 것

```python
await work()
```

이 뜻은:

> "이 비동기 작업을 실제로 진행시키고, 끝날 때까지 기다릴게"

`await`는 단순히 "기다린다"가 아니다. 더 정확하게는:

1. 코루틴을 실행 흐름에 올리고
2. 끝날 때까지 기다리는 것

---

## 4. 왜 어떤 때는 await가 안 되나

```python
async def main():
    print("실행")

await main()   # SyntaxError: 'await' outside function
```

`await`는 아무 데서나 쓸 수 없다.
**async 함수 안에서만** 쓸 수 있다.

파일 맨 아래(프로그램 시작점)에서 실행하려면:

```python
import asyncio
asyncio.run(main())   # ← 이게 맞다
```

요약:
```
async 함수 안 → await
프로그램 맨 바깥 → asyncio.run()
```

---

## 5. time.sleep vs asyncio.sleep

이 차이를 이해하면 async의 본질이 보인다.

```python
# 동기 방식
import time
time.sleep(1)
# → 프로그램 전체가 1초 동안 멈춤
# → 그동안 아무것도 못 함
```

```python
# 비동기 방식
import asyncio
await asyncio.sleep(1)
# → "나는 1초 쉬는 중"
# → 그동안 다른 비동기 작업은 진행 가능
```

`asyncio.sleep()`도 async 함수다.
그래서 반드시 `await`를 붙여야 한다.

```python
asyncio.sleep(1)        # 코루틴만 생성됨. 실제로 안 쉼.
await asyncio.sleep(1)  # 1초 비동기 대기. 이게 맞다.
```

---

## 6. gather — 여러 작업을 동시에

처음 문제로 돌아가보자.
API 요청 3개를 동시에 보내고 싶다.

```python
import asyncio

async def fetch_data(name):
    print(f"{name} 요청 시작")
    await asyncio.sleep(2)   # API 대기 (비동기)
    print(f"{name} 완료")

async def main():
    await asyncio.gather(
        fetch_data("NVDA"),
        fetch_data("AMD"),
        fetch_data("TSM"),
    )

asyncio.run(main())
```

실행하면: 총 2초 걸린다. (3개가 동시에 진행되므로)

`asyncio.gather()`의 뜻:

> "이 작업들을 같이 시작하고, 전부 끝날 때까지 기다릴게"

---

## 7. create_task — 먼저 시작해두고 나는 다른 일

```python
task = asyncio.create_task(work())
```

뜻: "이 작업, 지금 시작해 둬. 결과는 나중에 받을게."

`gather`와의 차이:

| | gather | create_task |
|---|---|---|
| **실행** | 여러 개 같이 시작 | 하나씩 먼저 시작 |
| **기다림** | 전부 끝날 때까지 | 내가 원할 때 await |
| **용도** | 결과 한 번에 받기 | 작업 시작 후 다른 일 가능 |

`create_task`의 장점이 보이는 예:

```python
async def main():
    task = asyncio.create_task(fetch_data("NVDA"))   # 시작해두고

    print("다른 처리 중...")                           # 다른 일
    await asyncio.sleep(0.5)
    print("아직 다른 일 하는 중")

    result = await task                              # 나중에 결과 받기
```

**중요**: `create_task`는 결과를 버리는 게 아니다.
"지금 당장 결과를 안 받을 뿐, 나중에 `await task`로 받을 수 있다."

---

## 8. async가 유리한 경우 vs 아닌 경우

async는 **무조건 빠른 기술이 아니다**.

| 유리한 경우 | 아닌 경우 |
|---|---|
| API 요청 | 복잡한 수치 계산 |
| 웹 크롤링 | 반복문으로 CPU 많이 쓰는 일 |
| 파일 I/O | 숫자 연산 집약적 작업 |
| DB 대기 | |
| 네트워크 통신 | |

async는 **기다리는 작업(I/O)**에 강하다.
CPU가 쉬는 시간(기다리는 시간)을 다른 작업으로 채우는 것이 핵심이다.

---

## 핵심 요약

| 개념 | 정확한 의미 |
|---|---|
| `async def work()` | 비동기 함수 정의 |
| `work()` | 코루틴 객체 생성 (실행 아님) |
| `await work()` | 코루틴 실제 실행 + 완료 대기 |
| `await`는 async 안에서만 | 바깥에서는 `asyncio.run()` |
| `asyncio.sleep()`도 async | 반드시 `await` 붙여야 함 |
| `gather` | 여러 작업 동시 실행 + 전체 대기 |
| `create_task` | 작업 먼저 시작, 결과는 나중에 |

> **한 줄 정리**
> async의 핵심은 "기다리는 시간을 낭비하지 않는 것"이다.
> `await`는 "지금 기다리는 동안 다른 작업이 진행될 수 있게 허용하는 신호"다.
