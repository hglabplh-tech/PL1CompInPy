from __future__ import annotations

from dataclasses import replace

from ..core.ast import Call, DoGroup, IfStatement, LabelledStatement, Procedure, Program, SelectStatement, Statement
from .function_table import (
    RUNTIME_FUNCTION_TABLE,
    FunctionDescriptor,
    FunctionTable,
    FunctionTableError,
    build_dynamic_function_table,
    declare_program_builtins,
    validate_program_calls,
)


class RuntimeError(ValueError):
    pass


def normalize_calls(program: Program) -> Program:
    procedures = _procedure_table(program.statements)
    table = RUNTIME_FUNCTION_TABLE.merge(build_dynamic_function_table(program))
    declare_program_builtins(program, table)
    validate_program_calls(program, table)
    return Program([_normalize_statement(statement, procedures, table) for statement in program.statements])


def _procedure_table(statements: list[Statement]) -> dict[str, Procedure]:
    procedures: dict[str, Procedure] = {}
    for statement in statements:
        if isinstance(statement, Procedure) and statement.name:
            procedures[statement.name.upper()] = statement
        elif isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure):
            procedure = statement.statement
            procedures[(procedure.name or statement.label).upper()] = procedure
    return procedures


def _normalize_statement(statement: Statement, procedures: dict[str, Procedure], table: FunctionTable) -> Statement:
    if isinstance(statement, Call):
        return _normalize_call(statement, procedures, table)
    if isinstance(statement, Procedure):
        return replace(statement, body=[_normalize_statement(child, procedures, table) for child in statement.body])
    if isinstance(statement, LabelledStatement):
        return replace(statement, statement=_normalize_statement(statement.statement, procedures, table))
    if isinstance(statement, DoGroup):
        return replace(statement, body=[_normalize_statement(child, procedures, table) for child in statement.body])
    if isinstance(statement, IfStatement):
        return replace(
            statement,
            then_branch=_normalize_statement(statement.then_branch, procedures, table),
            else_branch=_normalize_statement(statement.else_branch, procedures, table) if statement.else_branch else None,
        )
    if isinstance(statement, SelectStatement):
        return replace(
            statement,
            when_branches=[
                replace(branch, statement=_normalize_statement(branch.statement, procedures, table))
                for branch in statement.when_branches
            ],
            otherwise=_normalize_statement(statement.otherwise, procedures, table) if statement.otherwise else None,
        )
    return statement


def _normalize_call(call: Call, procedures: dict[str, Procedure], table: FunctionTable) -> Call:
    try:
        descriptor = table.validate_call(call)
    except FunctionTableError as exc:
        raise RuntimeError(str(exc)) from exc
    if call.mode != "name":
        return call

    procedure = procedures.get(call.name.upper())
    parameters = _descriptor_parameter_names(descriptor) or (procedure.parameters if procedure else [])
    if not parameters:
        return replace(call, mode="reference")

    named_arguments = {getattr(argument, "name", "").upper(): argument for argument in call.arguments}
    if not all(parameter.upper() in named_arguments for parameter in parameters):
        raise RuntimeError(f"Cannot normalize CALL {call.name} BY NAME: argument names do not match parameters")

    return Call(call.name, [named_arguments[parameter.upper()] for parameter in parameters], "reference")


def _descriptor_parameter_names(descriptor: FunctionDescriptor) -> list[str]:
    return [parameter.name for parameter in descriptor.parameters]
