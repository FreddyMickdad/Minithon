# Minithon Project

This project is a mini Python-like interpreter/compiler. Below is an explanation of every file and its purpose in the directory.

## Root Directory

- **pyrightconfig.json**
  - Configuration for Pyright, a static type checker for Python.
- **requirements.txt**
  - Lists Python dependencies required for the project.

## minithon/

- **__init__.py**
  - Makes `minithon` a Python package and imports everything from `main.py`.
- **__main__.py**
  - Entry point for running the package as a script (`python -m minithon`).
- **common.py**
  - Contains shared utilities and the `CommonException` class for error handling with source code context.
- **icg.py**
  - Implements the Intermediate Code Generator (`ICG` class) that generates intermediate code from the parsed AST.
- **lexer.py**
  - Contains the lexer/tokenizer logic. Defines token types, tokenization functions, and error handling for unrecognized tokens.
- **main.py**
  - Contains the main entry point function (`main`).
- **test_code.mipy**
  - Example source code file written in the Minithon language, used for testing the lexer, parser, and code generator. Example content:
    ```
    number = 7
    is_true = True
    if number <= 1:
        is_true = False
    elif number % 2 == 0 or number % 3 == 0:
        is_true = False
    else:
        i = 5
        while i * i <= number:
            j = i + 2
    ```
- **test.py**
  - Test runner script. Loads `test_code.mipy`, runs the lexer, parser, and ICG, and prints results and runtimes.
- **__pycache__/**
  - Directory for Python bytecode cache files (auto-generated).

### minithon/parser/

- **__init__.py**
  - Marks the directory as a Python package.
- **main.py**
  - Implements the parser (`Parser` class) that builds an AST from tokens.
- **types.py**
  - Defines AST node types, statement classes, and the `SyntaxError` exception for parsing errors.
- **__pycache__/**
  - Bytecode cache for parser subpackage.

---

## How to Run

1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
2. Run tests:
   ```powershell
   python minithon/test.py
   ```
3. Or run the package:
   ```powershell
   python -m minithon
   ```

---

## License

MIT (or specify your license here)
