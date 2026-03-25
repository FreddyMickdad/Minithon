from typing import NoReturn
from minithon.lexer import Token, TokenType
from minithon.parser.types import (
    Node,
    Expression,
    ControlFlowStmtBlock,
    IfStatementBlock,
    GenericStatement,
    AssignmentStatement,
    StatementType,
    Block,
    Program,
    SyntaxError,
)


class Parser:
    def __init__(self, tokens: list[Token], source_code: str) -> None:
        self.tokens = tokens
        self.current_token: Token
        self.token_index = -1
        self.current_node: Node
        self.source_code = source_code
        self.block_id = 0

    def raise_syntax_error(self, msg: str) -> NoReturn:
        raise SyntaxError(msg, self.source_code, self.current_token.position)

    def parse(self) -> Program:
        return self.program()

    def program(self) -> Program:
        block = self.block(-1)
        program_ = Program(block)
        return program_

    def get_indent(self) -> int:
        indent = 0
        # Monkey patch to prevent get_indent() from modifying indents such that other blocks can't see the changes
        token_index = self.token_index
        while self.match(TokenType.NEWLINE, False, False):
            pass
        while self.match(TokenType.WHITESPACE, False, False):
            indent += 1
            while self.match(TokenType.NEWLINE, False, False):
                indent = 0
        self.token_index = token_index
        if 0 <= token_index < len(self.tokens):
            self.current_token = self.tokens[token_index]
        return indent

    def block(self, prev_indent: int) -> Block | None:
        indent = self.get_indent()
        # Nested blocks must increase indentation compared to parent.
        if prev_indent >= 0 and indent <= prev_indent:
            return None
        self.block_id += 1
        block_id_buffer = self.block_id
        statements: list[StatementType] = []
        while self.get_indent() == indent:
            statement = self.statement(indent)
            if statement is None:
                break
            statements.append(statement)
        if not statements:
            self.block_id -= 1
            return None

        block_ = Block(statements, block_id_buffer, indent)
        return block_

    def match(
        self, token_type: TokenType, ignore_newline=True, ignore_whitespace=True
    ) -> bool:
        if self.token_index + 1 >= len(self.tokens):
            return False
        self.token_index += 1
        self.current_token = self.tokens[self.token_index]
        matched = False
        if (
            self.current_token.type == TokenType.COMMENT
            or (ignore_newline and self.current_token.type == TokenType.NEWLINE)
            or (ignore_whitespace and self.current_token.type == TokenType.WHITESPACE)
        ):
            matched = self.match(token_type)

        else:
            matched = self.current_token.type == token_type
        if matched:
            return True
        self.token_index -= 1
        if 0 <= self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]
        return False

    def generic_statement(
        self, token_type: TokenType, string_repr: str
    ) -> GenericStatement | None:
        if not self.match(token_type):
            return None
        stmt = GenericStatement(self.current_token, string_repr)
        return stmt

    def statement(self, indent: int) -> StatementType | None:
        statement = (
            self.generic_statement(TokenType.BREAK, "BREAK")
            or self.generic_statement(TokenType.CONTINUE, "CONTINUE")
            or self.generic_statement(TokenType.PASS, "PASS")
            or self.generic_statement(TokenType.COMMENT, "COMMENT")
            or self.assignment_statement()
            or self.while_statement_block(indent)
            or self.if_statement_block(indent)
        )
        return statement

    def assignment_statement(self) -> AssignmentStatement | None:
        if not self.match(TokenType.IDENTIFIER):
            return None
        identifier = self.current_token
        if not self.match(TokenType.ASSIGN):
            self.raise_syntax_error("Expected assignment operator")

        expression = self.expression()
        if expression is None:
            self.raise_syntax_error("Expected expression")
        stmt = AssignmentStatement(identifier, expression)
        return stmt

    def control_flow_stmt_block(
        self, token_type: TokenType, indent: int, has_expression=True
    ) -> ControlFlowStmtBlock | None:
        if not self.match(token_type):
            return None
        token = self.current_token
        expression: Expression | None = None
        if has_expression:
            expression = self.expression()
            if expression is None:
                self.raise_syntax_error("Expected expression")
        if not self.match(TokenType.COLON):
            self.raise_syntax_error("Expected colon")
        if not self.match(TokenType.NEWLINE, False):
            self.raise_syntax_error("Expected newline")
        block = self.block(indent)
        if block is None:
            self.raise_syntax_error("Expected code block")
        stmt_block = ControlFlowStmtBlock(token, expression, block)
        return stmt_block

    def if_statement_block(self, indent: int) -> IfStatementBlock | None:
        if_stmt_block = self.control_flow_stmt_block(TokenType.IF, indent)
        if if_stmt_block is None:
            return None
        elifs: list[ControlFlowStmtBlock] = []
        elif_stmt_block = self.control_flow_stmt_block(TokenType.ELIF, indent)
        while elif_stmt_block is not None:
            elifs.append(elif_stmt_block)
            elif_stmt_block = self.control_flow_stmt_block(TokenType.ELIF, indent)
        else_stmt_block = self.control_flow_stmt_block(TokenType.ELSE, indent, False)
        statement_block = IfStatementBlock(if_stmt_block, elifs, else_stmt_block)
        return statement_block

    def while_statement_block(self, indent: int) -> ControlFlowStmtBlock | None:
        stmt_block = self.control_flow_stmt_block(TokenType.WHILE, indent)
        return stmt_block

    def factor(self) -> bool:
        return (
            self.match(TokenType.BOOL_TRUE)
            or self.match(TokenType.BOOL_FALSE)
            or self.match(TokenType.IDENTIFIER)
            or self.match(TokenType.STRING)
            or self.match(TokenType.INTEGER)
            or self.match(TokenType.FLOAT)
        )

    def match_any(self, token_types: list[TokenType]) -> bool:
        for token_type in token_types:
            if self.match(token_type):
                return True
        return False

    def primary(self) -> Expression | Token | None:
        if self.match(TokenType.LPAREN):
            inner_expression = self.expression()
            if inner_expression is None:
                self.raise_syntax_error("Expected expression")
            if not self.match(TokenType.RPAREN):
                self.raise_syntax_error("Expected closing paranthesis")
            return inner_expression
        if self.factor():
            return self.current_token
        return None

    def unary(self) -> Expression | Token | None:
        if self.match(TokenType.NOT):
            operator = self.current_token
            operand = self.unary()
            if operand is None:
                self.raise_syntax_error("Expected expression")
            return Expression(operand, operator, None)
        return self.primary()

    def parse_binary(self, parse_operand, operators: list[TokenType]) -> Expression | None:
        left = parse_operand()
        if left is None:
            return None
        while self.match_any(operators):
            operator = self.current_token
            right = parse_operand()
            if right is None:
                self.raise_syntax_error("Expected expression")
            left = Expression(left, operator, right)
        return left if isinstance(left, Expression) else Expression(left)

    def term(self) -> Expression | None:
        return self.parse_binary(
            self.unary,
            [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULUS],
        )

    def arithmetic_expression(self) -> Expression | None:
        return self.parse_binary(self.term, [TokenType.ADD, TokenType.SUBTRACT])

    def comparison_expression(self) -> Expression | None:
        return self.parse_binary(
            self.arithmetic_expression,
            [
                TokenType.EQUAL,
                TokenType.NOT_EQUAL,
                TokenType.GREATER_THAN,
                TokenType.LESS_THAN,
                TokenType.GREATER_THAN_OR_EQUAL,
                TokenType.LESS_THAN_OR_EQUAL,
            ],
        )

    def and_expression(self) -> Expression | None:
        return self.parse_binary(self.comparison_expression, [TokenType.AND])

    def expression(self) -> Expression | None:
        return self.parse_binary(self.and_expression, [TokenType.OR])
