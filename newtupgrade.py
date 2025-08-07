import command


def main():
    success, output = command.run_cmd("newt upgrade")
    print(output)


if __name__ == '__main__':
    main()
