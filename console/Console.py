from io import StringIO


def c_to_string():
    return MainConsoleOutput.output.getvalue()


def c_println(*output):
    for element in output:
        MainConsoleOutput.output.write(str(element))
        print(str(element), end="")
    print("")
    MainConsoleOutput.output.write('\n')


def c_print(*output):
    for element in output:
        MainConsoleOutput.output.write(element)
        print(str(element), end="")


def get_string():
    return MainConsoleOutput.output.getvalue()


def clear():
    MainConsoleOutput.output = StringIO()


class MainConsoleOutput:  # Variables estáticas en python solo existen dentro de clases?
    output = StringIO()
