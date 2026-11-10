def fizz(n):
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    if n % 15 == 0:
        return "FizzBuzz"
    return str(n)

if __name__ == "__main__":
    print(" ".join(fizz(i) for i in range(1, 16)))
