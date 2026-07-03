from __future__ import annotations

from dataclasses import replace

from ..ast import Call, DoGroup, IfStatement, LabelledStatement, Procedure, Program, Statement


class RuntimeError(ValueError):
    pass


def normalize_calls(program: Program) -> Program:
    procedures = _procedure_table(program.statements)
    return Program([_normalize_statement(statement, procedures) for statement in program.statements])


def _procedure_table(statements: list[Statement]) -> dict[str, Procedure]:
    procedures: dict[str, Procedure] = {}
    for statement in statements:
        if isinstance(statement, Procedure) and statement.name:
            procedures[statement.name.upper()] = statement
        elif isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure):
            procedure = statement.statement
            procedures[(procedure.name or statement.label).upper()] = procedure
    return procedures


def _normalize_statement(statement: Statement, procedures: dict[str, Procedure]) -> Statement:
    if isinstance(statement, Call):
        return _normalize_call(statement, procedures)
    if isinstance(statement, Procedure):
        return replace(statement, body=[_normalize_statement(child, procedures) for child in statement.body])
    if isinstance(statement, LabelledStatement):
        return replace(statement, statement=_normalize_statement(statement.statement, procedures))
    if isinstance(statement, DoGroup):
        return replace(statement, body=[_normalize_statement(child, procedures) for child in statement.body])
    if isinstance(statement, IfStatement):
        return replace(
            statement,
            then_branch=_normalize_statement(statement.then_branch, procedures),
            else_branch=_normalize_statement(statement.else_branch, procedures) if statement.else_branch else None,
        )
    return statement


def _normalize_call(call: Call, procedures: dict[str, Procedure]) -> Call:
    if call.mode != "name":
        return call

    procedure = procedures.get(call.name.upper())
    if procedure is None:
        return replace(call, mode="reference")

    named_arguments = {getattr(argument, "name", "").upper(): argument for argument in call.arguments}
    if not all(parameter.upper() in named_arguments for parameter in procedure.parameters):
        raise RuntimeError(f"Cannot normalize CALL {call.name} BY NAME: argument names do not match parameters")

    return Call(call.name, [named_arguments[parameter.upper()] for parameter in procedure.parameters], "reference")
