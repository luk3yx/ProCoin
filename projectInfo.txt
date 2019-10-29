Coding style:

    All code must be Python 3.6 compliant.

    MyPy type checking will be used where applicable.

    Single quotes on string literals.
    Class names will be camel case and start with a capital letter. (ExampleClass)
    Variable names will be snake case. (example_variable)
    Indents will be 4 spaces.
    Builtin types should be initialized as literals where applicable. (example = {})
    Strings should be formatted with f-strings.
    80 characters per line maximum.
    Use \ to split string literals. ('this'\ \n 'and'\ \n 'this')


Items should have IDs, assigned by an automation script. A variable will track what the next ID is. IDs of removed items will not be re-used, because a user who has the IDs memorized could purchase an unexpected item by mistake.