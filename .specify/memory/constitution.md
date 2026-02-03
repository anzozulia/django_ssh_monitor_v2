<!--
  ============================================================================
  SYNC IMPACT REPORT
  ============================================================================
  Version Change: 1.1.0 → 1.2.0 (Testing requirements strengthened)
  
  Current Principles:
  - I. Clean Code
  - II. Monolith with Clear Boundaries
  - III. Separation of Concerns
  - IV. Comprehensive Unit Testing (was: Reasonable Testing)
  - V. Pragmatic Documentation
  
  Modified in v1.2.0:
  - Principle IV: Significantly expanded from "reasonable" to comprehensive
    - Added coverage tracking requirement
    - Added stage-based testing workflow
    - Added test pipeline requirements
    - Added regression testing mandate
  
  Templates Requiring Updates:
  - .specify/templates/plan-template.md: ✅ No changes needed (generic)
  - .specify/templates/spec-template.md: ✅ No changes needed (generic)
  - .specify/templates/tasks-template.md: ✅ No changes needed (generic)
  
  Deferred Items: None
  ============================================================================
-->

# Pet Web App Constitution

## Core Principles

### I. Clean Code

Code MUST be readable and maintainable. This pet project should remain approachable even after breaks from development.

- Use meaningful variable, function, and class names that describe intent
- Keep functions focused on a single responsibility (aim for <30 lines)
- Avoid deep nesting (max 3 levels preferred)
- Remove dead code rather than commenting it out
- Format consistently using automated tools (linter/formatter)

**Rationale**: Pet projects often have sporadic development cycles. Clean code ensures you can return after weeks or months and quickly understand what's happening.

### II. Monolith with Clear Boundaries

The application is a server-side rendered monolith. API endpoints are a supplementary feature, not the primary architecture.

- Pages MUST be rendered server-side; client-side JS enhances, not replaces
- Business logic SHOULD live in service classes/modules, not in route handlers or templates
- API endpoints (when provided) MUST follow consistent JSON response formats
- API endpoints SHOULD be grouped under `/api/` and documented separately
- Shared logic between SSR pages and API MUST be extracted to reusable services

**Rationale**: SSR monoliths are simpler to deploy and reason about. Keeping business logic in services (not routes) allows both pages and API to reuse the same core functionality.

### III. Separation of Concerns

The codebase MUST maintain clear boundaries between routing, templates, services, and data access.

- **Routes/Controllers**: Handle HTTP requests, validate input, call services, render responses
- **Templates/Views**: Presentation logic only—no business logic in templates
- **Services**: Business logic, orchestration, external integrations
- **Models/Data Layer**: Database access, queries, data validation, migrations
- **API Routes** (optional): Thin wrappers that call services and return JSON

Each layer SHOULD be modifiable without cascading changes to others.

**Rationale**: Even in a monolith, clear separation prevents "spaghetti code." Services as the core allows routes and API to stay thin.

### IV. Comprehensive Unit Testing

Unit tests are mandatory and MUST be maintained throughout development with measurable coverage.

**Coverage Requirements**:
- Unit test coverage MUST be tracked and reported (use coverage tools)
- All services and business logic MUST have unit tests
- All models with validation/logic MUST have unit tests
- API endpoints MUST have unit tests for all response scenarios
- Route handlers SHOULD have unit tests for input validation and error cases

**Development Workflow**:
- Each development stage MUST end with tests for all new functionality created
- All unit tests MUST pass before a stage is considered complete
- Full test suite MUST run after each significant development stage (regression check)
- New tests MUST be written for bug fixes (regression prevention)

**Test Pipeline**:
- A test runner MUST be configured to execute all tests with a single command
- Coverage reports MUST be generated and accessible (HTML or terminal output)
- Test results MUST clearly show: passed, failed, skipped, and coverage percentage
- CI pipeline SHOULD run tests automatically on commits (when CI is set up)

**Rationale**: Deep unit testing catches bugs early and enables confident refactoring. Coverage stats keep testing honest. Running all tests after each stage ensures old functionality isn't broken by new changes.

### V. Pragmatic Documentation

Document enough to onboard your future self. Over-documentation is as harmful as under-documentation.

- README MUST explain: what the project does, how to run it, how to develop
- API endpoints MUST be documented (inline or separate file)
- Complex algorithms or business rules SHOULD have explanatory comments
- Architecture decisions SHOULD be briefly noted when non-obvious
- Self-documenting code is preferred over excessive comments

**Rationale**: Documentation rot is real. Keep docs focused on what's not obvious from the code itself.

## Technology & Structure Guidelines

### Project Organization

- Use a monolith structure with logical grouping by layer:
  - `src/routes/` or `src/controllers/` — HTTP handlers for pages and API
  - `src/services/` — Business logic (reusable by routes and API)
  - `src/models/` — Data models and database access
  - `src/templates/` or `src/views/` — Server-rendered HTML templates
  - `src/static/` — CSS, JS, images served directly
- API routes MAY live in `src/routes/api/` or `src/api/` for clear separation
- Configuration MUST be environment-based (`.env` files, not hardcoded)

### Dependency Management

- Pin major versions of dependencies to avoid surprise breakages
- Prefer well-maintained, popular libraries over obscure alternatives
- Document why non-obvious dependencies were chosen
- Keep dependencies reasonably up-to-date (security patches promptly)

### Code Quality Tools

- A linter MUST be configured and enforced (e.g., ESLint, Ruff, etc.)
- A code formatter SHOULD be used for consistency (e.g., Prettier, Black)
- Pre-commit hooks are RECOMMENDED but not mandatory for a pet project

## Development Workflow

### Branching Strategy

- `master` branch SHOULD always be deployable/runnable
- Feature work SHOULD happen on feature branches
- Direct commits to `master` are acceptable for small, isolated fixes

### Commit Practices

- Write descriptive commit messages (what and why, not just what)
- Atomic commits preferred (one logical change per commit)
- Squash/rebase messy history before merging is OPTIONAL

### Code Review

- Self-review before considering work complete
- External review is OPTIONAL for a pet project but encouraged for learning

### Environment Management

- Local development MUST work without external dependencies (use Docker or local DBs)
- Document any required setup steps in README
- Secrets MUST NOT be committed (use `.env.example` as a template)

## Governance

This constitution guides development practices for this pet project. It prioritizes practicality over rigid process.

### Amendment Process

- Principles MAY be amended as the project evolves and needs change
- Document the reason for any principle changes in commit messages
- Version updates follow semantic versioning:
  - **MAJOR**: Fundamental approach changes (e.g., dropping testing requirements)
  - **MINOR**: New principles or significant expansions
  - **PATCH**: Clarifications and minor adjustments

### Compliance

- Use this constitution as a checklist during planning and code review
- Violations are acceptable when justified and documented
- The goal is maintainable code, not bureaucratic compliance

### Guidance

For runtime development guidance beyond this constitution, refer to:
- `README.md` for project-specific setup and workflows
- Feature specs in `specs/` directories for implementation details

**Version**: 1.2.0 | **Ratified**: 2026-02-03 | **Last Amended**: 2026-02-03
