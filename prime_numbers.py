# prime_numbers.py - 제곱근을 이용한 속도 최적화 버전
import math

print("1부터 100 사이의 소수 (최적화 버전):")

for num in range(2, 101):
    is_prime = True

    # 제곱근까지만 나누어떨어지는지 확인
    for i in range(2, int(math.sqrt(num)) + 1):
        if num % i == 0:
            is_prime = False
            break

    if is_prime:
        print(num, end=" ")