#!/usr/bin/env python3

def get_joke_context() -> str:
    return input("Enter a joke context: ")


def main() -> None:
    joke_context = get_joke_context()
    print(f"i got the context, i will tell a joke about this: {joke_context}")


if __name__ == "__main__":
    main()
