def is_prime(n: int) -> bool:
    """주어진 정수 n이 소수인지 판별하는 함수"""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def find_primes(limit: int = 100) -> list[int]:
    """1부터 limit까지의 소수 목록을 반환하는 함수"""
    return [num for num in range(1, limit + 1) if is_prime(num)]


if __name__ == "__main__":
    primes = find_primes(100)
    print("=== 1부터 100 사이의 소수 ===")
    print(primes)
    print(f"\n총 개수: {len(primes)}개")

