import ast
import os

from democritus_ast import (
    python_functions_as_import_string,
    _python_ast_clean,
    python_ast_parse,
    python_ast_function_defs,
    python_function_arguments,
    python_function_argument_names,
    python_function_argument_defaults,
    python_function_argument_annotations,
    python_function_names,
    python_function_docstrings,
    python_variable_names,
    python_constants,
    python_exceptions_raised,
    python_ast_object_line_numbers,
    python_exceptions_handled,
    python_ast_objects_of_type,
    python_ast_objects_not_of_type,
)
from files import file_read
from lists import lists_have_same_items


TEST_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ast_data.py'))
PYTHON_FILE_TEXT = file_read(TEST_FILE)

TEST_CODE_1 = '''a = 1
b = 2
c = 3
myList = range(10)

def someMethod(x):
    something = x * 2
    return something

f = someMethod(b)

print(f)'''

TEST_CODE_WITH_PRIVATE_FUNCTION = '''def _test(a: str):
    """Docstring."""
    return a'''

TEST_FUNCTION_WITH_DEFAULT = '''def test(a: str = ''):
    """Docstring."""
    return a'''

TEST_EXCEPTION_DATA = [
    {  # test a simple raise
        'code': '''raise ValueError('I cannot divide by zero')''',
        'handled': [],
        'raised': ['ValueError'],
    },
    {  # test a simple raise (in a context)
        'code': '''if d == 0:
    raise ValueError('I cannot divide by zero')
else:
    return n / d''',
        'handled': [],
        'raised': ['ValueError'],
    },
    {  # test code where an error that is part of another module is raised
        'code': '''raise pint.UndefinedUnitError('"Foo" is not a valid unit')''',
        'handled': [],
        'raised': ['pint.UndefinedUnitError'],
    },
    {  # ('one', ('afore_mentioned', ('custom', 'explicit')))
        'code': '''try:\n\tpass\nexcept pint.UndefinedUnitError:\n\traise pint.UndefinedUnitError('"Foo" is not a valid unit')''',
        'handled': ['pint.UndefinedUnitError'],
        'raised': ['pint.UndefinedUnitError'],
    },
    {  # ('one', ('afore_mentioned', ('custom', 'named_before_except')))
        'code': '''e = pint.UndefinedUnitError('"Foo" is not a valid unit')\ntry:\n\tpass\nexcept e:\n\traise e''',
        'handled': ['e'],
        'raised': ['e'],
    },
    {  # ('one', ('afore_mentioned', ('custom', 'named_in_except')))
        'code': '''try:\n\tpass\nexcept pint.UndefinedUnitError as e:\n\traise e''',
        'handled': ['pint.UndefinedUnitError'],
        'raised': ['pint.UndefinedUnitError'],
    },
    {  # ('one', ('afore_mentioned', ('built_in', 'explicit')))
        'code': '''try:\n\tpass\nexcept RuntimeError:\n\traise RuntimeError('"Foo" is not a valid unit')''',
        'handled': ['RuntimeError'],
        'raised': ['RuntimeError'],
    },
    {  # ('one', ('afore_mentioned', ('built_in', 'named_before_except')))
        'code': '''e = ValueError('"Foo" is not a valid unit')\ntry:\n\tpass\nexcept e:\n\traise e''',
        'handled': ['e'],
        'raised': ['e'],
    },
    {  # ('one', ('afore_mentioned', ('built_in', 'named_in_except')))
        'code': '''try:\n\tpass\nexcept RuntimeError as e:\n\traise e''',
        'handled': ['RuntimeError'],
        'raised': ['RuntimeError'],
    },
    {  # ('one', ('different', ('custom', 'explicit')))
        'code': '''try:\n\tpass\nexcept RuntimeError:\n\traise pint.UndefinedUnitError('"Foo" is not a valid unit')''',
        'handled': ['RuntimeError'],
        'raised': ['pint.UndefinedUnitError'],
    },
    {  # ('one', ('different', ('custom', 'named_before_except')))
        'code': '''e = pint.UndefinedUnitError('"Foo" is not a valid unit')\ntry:\n\tpass\nexcept ValueError:\n\traise e''',
        'handled': ['ValueError'],
        'raised': ['e'],
    },
    {  # ('one', ('different', ('built_in', 'explicit')))
        'code': '''try:\n\tpass\nexcept ValueError:\n\traise RuntimeError''',
        'handled': ['ValueError'],
        'raised': ['RuntimeError'],
    },
    {  # ('one', ('different', ('built_in', 'named_before_except')))
        'code': '''e = ValueError\ntry:\n\tpass\nexcept RuntimeError:\n\traise e''',
        'handled': ['RuntimeError'],
        'raised': ['e'],
    },
    {  # ('one', '') - with built-in exception
        'code': '''try:\n\tpass\nexcept RuntimeError:\n\traise''',
        'handled': ['RuntimeError'],
        'raised': ['RuntimeError'],
    },
    {  # ('one', '') - with custom exception
        'code': '''try:\n\tpass\nexcept pint.UndefinedUnitError:\n\traise''',
        'handled': ['pint.UndefinedUnitError'],
        'raised': ['pint.UndefinedUnitError'],
    },
    {  # ('many', ('afore_mentioned', ('custom', 'explicit')))
        'code': '''try:\n\tpass\nexcept (pint.UndefinedUnitError, pint.FooBarError):\n\traise pint.UndefinedUnitError('"Foo" is not a valid unit')''',
        'handled': ['pint.UndefinedUnitError', 'pint.FooBarError'],
        'raised': ['pint.UndefinedUnitError'],
    },
    {  # ('many', ('afore_mentioned', ('custom', 'named_before_except')))
        'code': '''e = pint.UndefinedUnitError('"Foo" is not a valid unit')\ntry:\n\tpass\nexcept (e, pint.FooBarError):\n\traise e''',
        'handled': ['e', 'pint.FooBarError'],
        'raised': ['e'],
    },
    {  # ('many', ('afore_mentioned', ('custom', 'named_in_except')))
        'code': '''try:\n\tpass\nexcept (pint.UndefinedUnitError, pint.FooBarError) as e:\n\traise e''',
        'handled': ['pint.UndefinedUnitError', 'pint.FooBarError'],
        'raised': ['pint.UndefinedUnitError', 'pint.FooBarError'],
    },
    {  # ('many', ('afore_mentioned', ('built_in', 'explicit')))
        'code': '''try:\n\tpass\nexcept (RuntimeError, RuntimeWarning):\n\traise RuntimeError('"Foo" is not a valid unit')''',
        'handled': ['RuntimeError', 'RuntimeWarning'],
        'raised': ['RuntimeError'],
    },
    {  # ('many', ('afore_mentioned', ('built_in', 'named_before_except')))
        'code': '''e = ValueError('"Foo" is not a valid unit')\ntry:\n\tpass\nexcept (e, RuntimeError):\n\traise e''',
        'handled': ['e', 'RuntimeError'],
        'raised': ['e'],
    },
    {  # ('many', ('afore_mentioned', ('built_in', 'named_in_except')))
        'code': '''try:\n\tpass\nexcept (RuntimeError, RuntimeWarning) as e:\n\traise e''',
        'handled': ['RuntimeError', 'RuntimeWarning'],
        'raised': ['RuntimeError', 'RuntimeWarning'],
    },
    {  # ('many', ('different', ('custom', 'explicit')))
        'code': '''try:\n\tpass\nexcept (pint.AError, pint.BError):\n\traise pint.UndefinedUnitError('"Foo" is not a valid unit')''',
        'handled': ['pint.AError', 'pint.BError'],
        'raised': ['pint.UndefinedUnitError'],
    },
    {  # ('many', ('different', ('custom', 'named_before_except')))
        'code': '''e = pint.UndefinedUnitError('"Foo" is not a valid unit')\ntry:\n\tpass\nexcept (ValueError, RuntimeError):\n\traise e''',
        'handled': ['ValueError', 'RuntimeError'],
        'raised': ['e'],
    },
    {  # ('many', ('different', ('built_in', 'explicit')))
        'code': '''try:\n\tpass\nexcept (ValueError, AssertionError):\n\traise RuntimeError''',
        'handled': ['ValueError', 'AssertionError'],
        'raised': ['RuntimeError'],
    },
    {  # ('many', ('different', ('built_in', 'named_before_except')))
        'code': '''e = ValueError\ntry:\n\tpass\nexcept (RuntimeError, RuntimeWarning):\n\traise e''',
        'handled': ['RuntimeError', 'RuntimeWarning'],
        'raised': ['e'],
    },
    {  # ('many', '') - with built-in exception
        'code': '''try:\n\tpass\nexcept (RuntimeError, RuntimeWarning):\n\traise''',
        'handled': ['RuntimeError', 'RuntimeWarning'],
        'raised': ['RuntimeError', 'RuntimeWarning'],
    },
    {  # ('many', '') - with custom exception
        'code': '''try:\n\tpass\nexcept (pint.UndefinedUnitError, pint.AError):\n\traise''',
        'handled': ['pint.UndefinedUnitError', 'pint.AError'],
        'raised': ['pint.UndefinedUnitError', 'pint.AError'],
    },
]


def test_python_ast_objects_not_of_type_docs_1():
    # make sure that any ast.FunctionDef objects *and* their children are not returned
    result = python_ast_objects_not_of_type(TEST_CODE_1, ast.FunctionDef)
    assert len(result) == 35
    assert isinstance(result, list)


def test_python_ast_objects_of_type_1():
    result = list(python_ast_objects_of_type(TEST_CODE_1, ast.FunctionDef))
    assert len(result) == 1
    assert isinstance(result[0], ast.FunctionDef)


def test_python_exceptions_handled_docs_1():
    for test in TEST_EXCEPTION_DATA:
        try:
            assert lists_have_same_items(python_exceptions_handled(test['code']), test['handled'])
        except AssertionError as e:
            failure = (test, e)
            print(failure)
            raise e


def test_python_ast_object_line_numbers_docs_1():
    result = python_ast_object_line_numbers(python_ast_parse(TEST_CODE_WITH_PRIVATE_FUNCTION))
    assert result == (1, 3)

    result = python_ast_object_line_numbers(python_ast_parse(TEST_FUNCTION_WITH_DEFAULT))
    assert result == (1, 3)

    s = '''def democritus_directory_documentation_create(directory_path: str, *, track_changes: bool = True):
    """Create documentation files for all non-test python files in the given directory_path."""
    _directory_documentation_action(
        directory_path, democritus_functions_file_documentation_create, track_changes=track_changes
    )'''
    result = python_ast_object_line_numbers(python_ast_parse(s))
    assert result == (1, 4)


def test_python_exceptions_raised_docs_1():
    for test in TEST_EXCEPTION_DATA:
        try:
            assert lists_have_same_items(python_exceptions_raised(test['code']), test['raised'])
        except AssertionError as e:
            failure = (test, e)
            print(failure)
            raise e


def test_python_functions_as_import_string_1():
    assert (
        python_functions_as_import_string(PYTHON_FILE_TEXT, 'ast_data')
        == 'from democritus_ast import (\n    python_ast_raise_name,\n    python_exceptions,\n    python_functions_as_import_string,\n    python_ast_object_line_number,\n    python_ast_object_line_numbers,\n    _python_ast_clean,\n    python_ast_parse,\n    python_ast_function_defs,\n    python_function_arguments,\n    python_function_argument_names,\n    python_function_argument_defaults,\n    python_function_argument_annotations,\n    python_function_names,\n    python_function_docstrings,\n    python_variable_names,\n    python_constants,\n)'
    )


def test__python_ast_clean_1():
    assert _python_ast_clean('print("foo\nbar")') == 'print("foo\\nbar")'


def test_python_ast_parse_1():
    result = python_ast_parse(TEST_CODE_1)
    assert isinstance(result, ast.Module)


def test_python_ast_function_defs_1():
    result = tuple(python_ast_function_defs(TEST_FUNCTION_WITH_DEFAULT))
    assert len(result) == 1
    assert isinstance(result[0], ast.FunctionDef)

    result = tuple(python_ast_function_defs(TEST_CODE_WITH_PRIVATE_FUNCTION))
    assert len(result) == 1
    assert isinstance(result[0], ast.FunctionDef)


def test_python_function_arguments_1():
    result = python_function_arguments(TEST_FUNCTION_WITH_DEFAULT)
    assert len(result) == 1
    assert isinstance(result[0], ast.arg)


def test_python_function_argument_names_1():
    assert tuple(python_function_argument_names(TEST_FUNCTION_WITH_DEFAULT)) == ('a',)


def test_python_function_argument_defaults_1():
    result = python_function_argument_defaults(TEST_FUNCTION_WITH_DEFAULT)
    assert len(result) == 1
    assert isinstance(result[0], ast.Str)

    result = python_function_argument_defaults(TEST_CODE_WITH_PRIVATE_FUNCTION)
    assert len(result) == 0


def test_python_function_argument_annotations_1():
    assert (
        list(
            python_function_argument_annotations(
                '''def _test(a: str):
    """Docstring."""
    return a'''
            )
        )
        == ['str']
    )
    assert (
        list(
            python_function_argument_annotations(
                '''def _test(a):
    """Docstring."""
    return a'''
            )
        )
        == [None]
    )


def test_python_function_names_1():
    assert python_function_names(PYTHON_FILE_TEXT) == [
        'python_ast_raise_name',
        'python_exceptions',
        'python_functions_as_import_string',
        'python_ast_object_line_number',
        'python_ast_object_line_numbers',
        '_python_ast_clean',
        'python_ast_parse',
        'python_ast_function_defs',
        'python_function_arguments',
        'python_function_argument_names',
        'python_function_argument_defaults',
        'python_function_argument_annotations',
        'python_function_names',
        'python_function_docstrings',
        'python_variable_names',
        'python_constants',
    ]
    assert python_function_names(TEST_CODE_WITH_PRIVATE_FUNCTION) == ['_test']
    assert python_function_names(TEST_CODE_WITH_PRIVATE_FUNCTION, ignore_private_functions=True) == []


def test_python_function_docstrings_1():
    code_text = '''def _test(a: str):
    """Docstring."""
    return a'''
    assert python_function_docstrings(code_text) == ['Docstring.']
    assert python_function_docstrings(code_text, ignore_private_functions=True) == []


def test_python_variable_names_1():
    assert python_variable_names('x = 7') == ['x']
    assert python_variable_names('x = y + 7') == ['x']
    assert python_variable_names('PI = 3.14') == ['PI']
    assert python_variable_names('1 + 0') == []
    assert python_variable_names(TEST_CODE_1) == ['a', 'b', 'c', 'myList', 'f', 'something']


def test_python_constants_1():
    assert python_constants('x = 7') == []
    assert python_constants('PI = 3.14') == ['PI']
    assert python_constants('1 + 0') == []