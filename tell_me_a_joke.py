#!/usr/bin/env python3

def get_joke_topic() -> str:
    return input("Enter a joke topic: ")


def main() -> None:
    joke_topic = get_joke_topic()
    print(f"i got the topic, i will tell a joke about this: {joke_topic}")


if __name__ == "__main__":
    main()
