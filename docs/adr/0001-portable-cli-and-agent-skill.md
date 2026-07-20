# ADR-0001: Keep the conversion engine independent from Agent integrations

## Status

Accepted

## Context

Codex, Claude Code, and other agents use different installation directories, and not every agent supports Skills. The conversion process must also work in local terminals and CI.

## Decision

Implement the converter as a standalone Python CLI. Keep one vendor-neutral Agent Skill that invokes the CLI, and use small installers for supported Agents. Add MCP as a separate adapter after an asynchronous job interface is stable.

## Consequences

The conversion code has one implementation and remains usable without an Agent. Agent-specific metadata cannot contain conversion logic. Installation requires both the Python package and the Skill until packaged releases automate both steps.

## Alternatives Considered

- Separate implementations for every Agent: rejected because behavior and fixes would drift.
- Skill only: rejected because it excludes users and agents without Skill support.
- MCP only: deferred because synchronous MCP calls are a poor fit for conversions lasting many minutes.
