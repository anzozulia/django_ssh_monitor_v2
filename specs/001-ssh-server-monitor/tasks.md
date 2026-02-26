# Tasks: SSH Server Monitor

**Input**: Design documents from `/specs/001-ssh-server-monitor/`  
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/urls.md, research.md, quickstart.md

**Tests**: Per Constitution Principle IV (Comprehensive Unit Testing), tests are REQUIRED after each phase. Each stage MUST end with tests for all new functionality.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Django project root**: `ssh_monitor/`
- **Apps**: `ssh_monitor/apps/`
- **Tests**: `ssh_monitor/tests/`
- **Templates**: `ssh_monitor/apps/<app>/templates/`
- **Static**: `ssh_monitor/static/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, Docker setup, and basic Django structure

- [x] T001 Create Django project structure with `django-admin startproject ssh_monitor` in repository root
- [x] T002 Create requirements files in `ssh_monitor/requirements/base.txt`, `local.txt`, `production.txt` with Django 5.x, Celery, Paramiko, django-tailwind, pytest-django, pytest-cov
- [x] T003 [P] Create `ssh_monitor/pyproject.toml` with Ruff, Black, and pytest configuration
- [x] T004 [P] Create `ssh_monitor/.env.example` with all required environment variables per quickstart.md
- [x] T005 Create `ssh_monitor/Dockerfile` with multi-stage build per python_devops.mdc
- [x] T006 [P] Create `ssh_monitor/docker-compose.local.yml` with app, postgres, redis, celery-worker, celery-beat services
- [x] T007 [P] Create `ssh_monitor/docker-compose.prod.yml` with production configuration
- [x] T008 Create `ssh_monitor/.gitignore` with Python, Django, Docker, .env patterns
- [x] T009 Create Django settings package structure in `ssh_monitor/ssh_monitor/settings/__init__.py`, `base.py`, `local.py`, `production.py`
- [x] T010 Configure Celery app in `ssh_monitor/ssh_monitor/celery.py` with Redis broker
- [x] T011 [P] Initialize django-tailwind theme app in `ssh_monitor/theme/`
- [x] T012 Create base template with admin-panel layout and sidebar in `ssh_monitor/apps/core/templates/base.html`
- [x] T013 Create context processor for sidebar server list in `ssh_monitor/apps/core/context_processors.py`

**Checkpoint**: Docker containers start, Django runs, Tailwind compiles

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T014 Create `apps/core/` app with `__init__.py` and register in settings
- [x] T015 [P] Create `apps/accounts/` app with `__init__.py` and register in settings
- [x] T016 [P] Create `apps/servers/` app with `__init__.py` and register in settings
- [x] T017 [P] Create `apps/alerts/` app with `__init__.py` and register in settings
- [x] T018 [P] Create `apps/notifications/` app with `__init__.py` and register in settings
- [x] T019 Implement credential encryption utility in `ssh_monitor/apps/core/encryption.py` using Fernet
- [x] T020 Configure logging with rotation in `ssh_monitor/ssh_monitor/settings/base.py` per python.mdc
- [x] T021 Create login/logout views in `ssh_monitor/apps/accounts/views.py` using Django's built-in auth
- [x] T022 Create login template in `ssh_monitor/apps/accounts/templates/accounts/login.html`
- [x] T023 Create `createadmin` management command in `ssh_monitor/apps/accounts/management/commands/createadmin.py`
- [x] T024 Configure project URLs in `ssh_monitor/ssh_monitor/urls.py` with all app includes
- [x] T025 Create accounts URLs in `ssh_monitor/apps/accounts/urls.py`
- [x] T026 Run initial migrations and verify database setup

### Tests for Phase 2 (Required per Constitution)

- [x] T027 [P] Create pytest configuration in `ssh_monitor/tests/conftest.py` with Django fixtures
- [x] T028 [P] Unit tests for encryption utility in `ssh_monitor/tests/unit/test_encryption.py`
- [x] T029 [P] Unit tests for createadmin command in `ssh_monitor/tests/unit/test_createadmin.py`
- [x] T030 Run full test suite and verify coverage reporting works

**Checkpoint**: Foundation ready - user can log in, encryption works, all apps registered

---

## Phase 3: User Story 1 - Add and Monitor First Server (Priority: P1) 🎯 MVP

**Goal**: Users can add a server with SSH credentials and see live metrics on a detail page

**Independent Test**: Add one server with password auth, view detail page showing CPU, RAM, disk metrics

### Models for User Story 1

- [x] T031 [P] [US1] Create Server model with all fields in `ssh_monitor/apps/servers/models.py` per data-model.md
- [x] T032 [P] [US1] Create MetricSnapshot model in `ssh_monitor/apps/servers/models.py`
- [x] T033 [P] [US1] Create DiskMetric model in `ssh_monitor/apps/servers/models.py`
- [x] T034 [US1] Create and run migrations for servers app

### Services for User Story 1

- [x] T035 [US1] Implement SSHService with connect, execute_command, disconnect in `ssh_monitor/apps/servers/services/ssh_service.py`
- [x] T036 [US1] Implement key generation and installation in SSHService for "Generate SSH Key" auth type
- [x] T037 [US1] Implement MetricsService with parse_loadavg, parse_free, parse_df in `ssh_monitor/apps/servers/services/metrics_service.py`
- [x] T038 [US1] Implement PingService for connectivity diagnostics in `ssh_monitor/apps/servers/services/ping_service.py`
- [x] T039 [US1] Implement collect_metrics orchestration combining SSH and parsing in MetricsService

### Celery Tasks for User Story 1

- [x] T040 [US1] Create collect_server_metrics Celery task in `ssh_monitor/apps/servers/tasks.py`
- [x] T041 [US1] Implement dynamic task scheduling with django-celery-beat on server create/update
- [x] T042 [US1] Implement 3-retry logic with ping fallback in collect_server_metrics task
- [x] T042a [US1] Create non-configurable SSH connectivity AlertRule automatically on server creation in ServerCreateView (FR-011c: always enabled, cannot be disabled)

### Views & Forms for User Story 1

- [x] T043 [US1] Create ServerForm with all fields and auth type handling in `ssh_monitor/apps/servers/forms.py`
- [x] T044 [US1] Create ServerCreateView in `ssh_monitor/apps/servers/views.py`
- [x] T045 [US1] Create ServerDetailView with current metrics in `ssh_monitor/apps/servers/views.py`
- [x] T046 [US1] Create ServerMetricsView (JSON endpoint for polling) in `ssh_monitor/apps/servers/views.py`
- [x] T047 [US1] Create servers URLs in `ssh_monitor/apps/servers/urls.py`

### Templates for User Story 1

- [x] T048 [P] [US1] Create server add form template in `ssh_monitor/apps/servers/templates/servers/server_form.html`
- [x] T049 [P] [US1] Create server detail template with metrics display in `ssh_monitor/apps/servers/templates/servers/server_detail.html`

### Frontend for User Story 1

- [x] T050 [US1] Create unified metrics rendering JS in `ssh_monitor/static/js/metrics-polling.js`
- [x] T051 [US1] Implement polling logic that calls ServerMetricsView and updates UI

### Tests for User Story 1 (Required per Constitution)

- [x] T052 [P] [US1] Unit tests for Server model in `ssh_monitor/tests/unit/test_server_model.py`
- [x] T053 [P] [US1] Unit tests for SSHService (mocked) in `ssh_monitor/tests/unit/test_ssh_service.py`
- [x] T054 [P] [US1] Unit tests for MetricsService parsing in `ssh_monitor/tests/unit/test_metrics_service.py`
- [x] T055 [P] [US1] Unit tests for PingService in `ssh_monitor/tests/unit/test_ping_service.py`
- [x] T056 [US1] Integration tests for server CRUD flow in `ssh_monitor/tests/integration/test_server_crud.py`
- [x] T057 [US1] Run full test suite and verify all US1 tests pass

**Checkpoint**: User Story 1 complete - can add server, see live metrics, metrics auto-refresh

---

## Phase 4: User Story 2 - Configure Server Alerts (Priority: P2)

**Goal**: Users can create alert rules for servers with flexible conditions and state tracking

**Independent Test**: Create alert rule "RAM > 80%", verify it shows in server's alert list with correct state

### Models for User Story 2

- [x] T058 [P] [US2] Create AlertRule model with all fields in `ssh_monitor/apps/alerts/models.py` per data-model.md
- [x] T059 [P] [US2] Create AlertEvent model in `ssh_monitor/apps/alerts/models.py`
- [x] T060 [US2] Create and run migrations for alerts app

### Services for User Story 2

- [x] T061 [US2] Implement AlertEvaluationService with condition checking in `ssh_monitor/apps/alerts/services/evaluation_service.py`
- [x] T062 [US2] Implement all condition operators (gt, lt, eq, gte, lte, in_range, out_of_range)
- [x] T063 [US2] Implement alert state transitions (normal→triggered, triggered→dismissed)
- [x] T064 [US2] Implement reminder logic with interval checking
- [x] T065 [US2] Implement dismissal threshold logic to prevent flapping

### Celery Tasks for User Story 2

- [x] T066 [US2] Create evaluate_server_alerts Celery task in `ssh_monitor/apps/alerts/tasks.py`
- [x] T067 [US2] Integrate alert evaluation into collect_server_metrics task (call after metrics saved)

### Views & Forms for User Story 2

- [x] T068 [US2] Create AlertRuleForm in `ssh_monitor/apps/alerts/forms.py`
- [x] T069 [US2] Create ServerAlertListView in `ssh_monitor/apps/alerts/views.py`
- [x] T070 [US2] Create AlertRuleCreateView in `ssh_monitor/apps/alerts/views.py`
- [x] T071 [US2] Create AlertRuleUpdateView in `ssh_monitor/apps/alerts/views.py`
- [x] T072 [US2] Create AlertRuleDeleteView in `ssh_monitor/apps/alerts/views.py`
- [x] T073 [US2] Create AlertRuleToggleView in `ssh_monitor/apps/alerts/views.py`
- [x] T074 [US2] Create alerts URLs in `ssh_monitor/apps/alerts/urls.py`

### Templates for User Story 2

- [x] T075 [P] [US2] Create alert list template in `ssh_monitor/apps/alerts/templates/alerts/alert_list.html`
- [x] T076 [P] [US2] Create alert form template in `ssh_monitor/apps/alerts/templates/alerts/alert_form.html`
- [x] T077 [US2] Add alerts section to server detail template

### Tests for User Story 2 (Required per Constitution)

- [x] T078 [P] [US2] Unit tests for AlertRule model in `ssh_monitor/tests/unit/test_alert_model.py`
- [x] T079 [P] [US2] Unit tests for AlertEvaluationService in `ssh_monitor/tests/unit/test_alert_evaluation.py`
- [x] T080 [US2] Integration tests for alert CRUD in `ssh_monitor/tests/integration/test_alert_crud.py`
- [x] T081 [US2] Run full test suite and verify all US1+US2 tests pass

**Checkpoint**: User Story 2 complete - can create/edit/delete alerts, alerts evaluate on metrics collection

---

## Phase 4a: Post-Implementation Reworks (applied during Phases 3-4)

**Purpose**: Reworks applied to existing implementation based on user feedback and refinement

### UI/UX Reworks (all completed)

- [x] T200 Rewrite all admin templates from scratch using TailAdmin design system (demo.tailadmin.com)
- [x] T201 Upgrade from Tailwind CSS v3 (django-tailwind) to Tailwind CSS v4 (@tailwindcss/cli), light theme only
- [x] T202 Add Alpine.js for dynamic UI interactivity (conditional form fields, toggle switches)
- [x] T203 Widen main content areas from max-w-7xl to max-w-screen-2xl across all pages
- [x] T204 Redesign server_form.html and alert_form.html to match TailAdmin "Add Product" layout
- [x] T205 Implement dynamic auth_type field visibility in server addition form
- [x] T206 Move action buttons ("Add Server", "Add Alert") from header into their respective content blocks
- [x] T207 Consolidate alert rule listing into server_detail.html; remove dedicated alert_list.html page
- [x] T208 Implement async toggle switches for all boolean settings (enabled, monitoring) without page reload
- [x] T209 Round all percentages and numeric load values to two decimal places in frontend
- [x] T210 Fix sidebar server highlighting on all server subpages (detail, alert create/edit)
- [x] T211 Highlight "Add Server" link in sidebar when on server creation page
- [x] T212 Align sidebar "SSH Monitor" block height with main content header

### Dashboard Reworks (all completed)

- [x] T213 Replace status dots with badge-style indicators (pill with dot + text) in All Servers table
- [x] T214 Add Fleet Health Overview panel to dashboard (healthy/warning/critical counts + segmented bar)

### Metrics Expansion (all completed)

- [x] T215 Expand MetricSnapshot model with detailed RAM fields (free, available, cached, buffers, shared bytes + percents)
- [x] T216 Expand MetricSnapshot model with detailed swap fields (free, cached bytes + free percent)
- [x] T217 Add cpu_cores field to MetricSnapshot model
- [x] T218 Add filesystem and available_bytes fields to DiskMetric model
- [x] T219 Replace parse_free with parse_meminfo (/proc/meminfo) in MetricsService
- [x] T220 Update parse_df to use df -kPT for filesystem type and available bytes
- [x] T221 Add nproc command to collect CPU core count
- [x] T222 Expand MetricType choices with all new RAM/swap/disk/uptime alert metrics
- [x] T223 Update AlertEvaluationService._resolve_metric() for all new metric types
- [x] T224 Restructure server_detail.html: Server Info sections (Connection, Monitoring, Access, Capacity), Memory Breakdown with % in parentheses, Disk Usage as cards
- [x] T225 Hide /docker/ entries from Disk Usage details
- [x] T226 Update metrics-polling.js for new metric fields and layout
- [x] T227 Show resource totals (CPU cores, total RAM/Swap/Disk) in server detail

### Alert Form Reworks (all completed)

- [x] T228 Reorganize alert form metric_type choices into optgroups with separators; remove "Custom" from user selection
- [x] T229 Implement dynamic threshold unit selection (B/KB/MB/GB/TB for bytes; h/d/w/mo for uptime)
- [x] T230 Add uptime as trackable metric with configurable units
- [x] T231 Make Condition + Threshold fields appear in single responsive row with dynamic column count
- [x] T232 Dynamic threshold field labels (From/To for range, Threshold for single; unit suffix appended)
- [x] T233 Remove all form animations for instant layout switches

### Dismissal Threshold Rework (all completed)

- [x] T234 Replace time-based dismissal_threshold_minutes with value-based dismissal_threshold_value + dismissal_threshold_value_2
- [x] T235 Implement _dismissal_matches() in AlertEvaluationService with per-condition hysteresis logic
- [x] T236 Make dismissal threshold optional (opt-in toggle in form, nullable in model)
- [x] T237 Implement dismissal form UI: opt-in toggle, dynamic labels per condition, contextual hint text
- [x] T238 Restructure alert form into three card sections: Rule, Trigger Definition, Recovery & Notifications
- [x] T239 Remove "Rule Enabled" toggle from alert form (managed from server rules list only)
- [x] T240 Unit conversion support for dismissal thresholds (same units as main thresholds)

### Server Management Reworks (all completed)

- [x] T241 Add ServerDeleteView with PeriodicTask cleanup and dashboard redirect
- [x] T242 Add "Danger Zone" with delete button to server_detail.html
- [x] T243 Trigger immediate metric collection (collect_server_metrics.delay) after server creation
- [x] T244 Fix GENERATED_KEY SSH auth: detect credential type (password vs private key) dynamically in SSHService.connect()

### Tests Added During Reworks (all completed)

- [x] T245 Unit tests for parse_meminfo and expanded parse_df
- [x] T246 Unit tests for GENERATED_KEY SSH auth flow (password and key modes)
- [x] T247 Unit tests for alert form unit conversion (bytes and uptime)
- [x] T248 Unit tests for uptime metric evaluation
- [x] T249 Unit tests for value-based dismissal with hysteresis (gt and in_range)
- [x] T250 Unit test for form without dismissal threshold (toggle off)

**Checkpoint**: All reworks applied, tested, and validated

---

## Phase 5: User Story 3 - Set Up Telegram Notifications (Priority: P3)

**Goal**: Users can configure Telegram and receive alert notifications

**Independent Test**: Configure Telegram bot, trigger alert, receive Telegram message

### Models for User Story 3

- [x] T082 [US3] Create NotificationChannel model in `ssh_monitor/apps/notifications/models.py` per data-model.md
- [x] T083 [US3] Create and run migrations for notifications app

### Services for User Story 3

- [x] T084 [US3] Create abstract NotificationChannel base class in `ssh_monitor/apps/notifications/services/base.py`
- [x] T085 [US3] Implement TelegramChannel with send(), validate_config(), and rate limit handling with exponential backoff in `ssh_monitor/apps/notifications/services/telegram.py`
- [x] T086 [US3] Implement NotificationDispatcher that routes to enabled channels in `ssh_monitor/apps/alerts/services/notification_service.py`
- [x] T087 [US3] Implement notification message formatting with server name, severity, metric, value, threshold

### Integration for User Story 3

- [x] T088 [US3] Integrate NotificationDispatcher into AlertEvaluationService (send on trigger/remind/dismiss)
- [x] T089 [US3] Integrate notification tracking into AlertEvaluationService to update AlertEvent.notification_sent and notification_error fields (fields already defined in data-model.md)

### Views & Forms for User Story 3

- [x] T090 [US3] Create TelegramConfigForm in `ssh_monitor/apps/notifications/forms.py`
- [x] T091 [US3] Create ChannelListView in `ssh_monitor/apps/notifications/views.py`
- [x] T092 [US3] Create TelegramConfigView in `ssh_monitor/apps/notifications/views.py`
- [x] T093 [US3] Create TelegramTestView (sends test message) in `ssh_monitor/apps/notifications/views.py`
- [x] T094 [US3] Create ChannelToggleView in `ssh_monitor/apps/notifications/views.py`
- [x] T095 [US3] Create notifications URLs in `ssh_monitor/apps/notifications/urls.py`

### Templates for User Story 3

- [x] T096 [P] [US3] Create channel list template in `ssh_monitor/apps/notifications/templates/notifications/channel_list.html`
- [x] T097 [P] [US3] Create Telegram config template in `ssh_monitor/apps/notifications/templates/notifications/telegram_config.html`

### Tests for User Story 3 (Required per Constitution)

- [x] T098 [P] [US3] Unit tests for TelegramChannel (mocked API) in `ssh_monitor/tests/unit/test_telegram_service.py`
- [x] T099 [P] [US3] Unit tests for NotificationDispatcher in `ssh_monitor/tests/unit/test_notification_service.py`
- [x] T100 [US3] Integration tests for notification flow in `ssh_monitor/tests/integration/test_notification_flow.py`
- [x] T101 [US3] Run full test suite and verify all US1+US2+US3 tests pass

**Checkpoint**: User Story 3 complete - Telegram configured, alerts send notifications

---

## Phase 6: User Story 4 - Manage Default Alert Templates (Priority: P4)

**Goal**: Users can create default alerts that auto-apply to new servers

**Independent Test**: Create default alert template, add new server, verify alert is cloned to server

### Models for User Story 4

- [x] T102 [US4] Create DefaultAlertTemplate model in `ssh_monitor/apps/alerts/models.py`
- [x] T103 [US4] Add cloned_from_template FK to AlertRule model
- [x] T104 [US4] Create and run migrations

### Services for User Story 4

- [x] T105 [US4] Implement clone_default_alerts_to_server() in `ssh_monitor/apps/alerts/services/template_service.py`
- [x] T106 [US4] Integrate template cloning into server creation flow

### Views & Forms for User Story 4

- [x] T107 [US4] Create DefaultAlertTemplateForm in `ssh_monitor/apps/alerts/forms.py`
- [x] T108 [US4] Create DefaultAlertListView in `ssh_monitor/apps/alerts/views.py`
- [x] T109 [US4] Create DefaultAlertCreateView in `ssh_monitor/apps/alerts/views.py`
- [x] T110 [US4] Create DefaultAlertUpdateView in `ssh_monitor/apps/alerts/views.py`
- [x] T111 [US4] Create DefaultAlertDeleteView in `ssh_monitor/apps/alerts/views.py`
- [x] T112 [US4] Add default alerts URLs to `ssh_monitor/apps/alerts/urls.py`

### Templates for User Story 4

- [x] T113 [P] [US4] Create default alert list template in `ssh_monitor/apps/alerts/templates/alerts/default_list.html`
- [x] T114 [P] [US4] Create default alert form template in `ssh_monitor/apps/alerts/templates/alerts/default_form.html`

### Tests for User Story 4 (Required per Constitution)

- [x] T115 [P] [US4] Unit tests for DefaultAlertTemplate model in `ssh_monitor/tests/unit/test_default_alert.py`
- [x] T116 [US4] Unit tests for clone_default_alerts_to_server in `ssh_monitor/tests/unit/test_template_service.py`
- [x] T117 [US4] Integration tests for template cloning flow in `ssh_monitor/tests/integration/test_template_cloning.py`
- [x] T118 [US4] Run full test suite and verify all US1-US4 tests pass

**Checkpoint**: User Story 4 complete - default templates work, new servers get cloned alerts

---

## Phase 7: User Story 5 - View Historical Metrics and Trends (Priority: P5)

**Goal**: Users can see historical graphs with time range selection and alert overlays

**Independent Test**: Monitor server for 1+ hour, view graphs with different time ranges, see alert periods highlighted

### Views for User Story 5

- [x] T119 [US5] Extend ServerDetailView to include historical data query in `ssh_monitor/apps/servers/views.py`
- [x] T120 [US5] Extend ServerMetricsView to return history data with configurable time range

### Frontend for User Story 5

- [x] T121 [US5] Add Chart.js to project and configure in base template
- [x] T122 [US5] Implement renderMetricsChart() for CPU, RAM, disk, swap in `ssh_monitor/static/js/metrics-polling.js`
- [x] T123 [US5] Implement time range selector (1h, 6h, 24h, 7d, 30d) with chart refresh
- [x] T124 [US5] Implement tooltip with exact timestamp and value on hover
- [x] T125 [US5] Implement alert period overlay on charts (highlight triggered periods)

### Templates for User Story 5

- [x] T126 [US5] Update server detail template with chart containers and time range selector

### Tests for User Story 5 (Required per Constitution)

- [x] T127 [P] [US5] Unit tests for historical data query in `ssh_monitor/tests/unit/test_metrics_history.py`
- [x] T128 [US5] Integration tests for chart data endpoint in `ssh_monitor/tests/integration/test_chart_data.py`
- [x] T129 [US5] Run full test suite and verify all US1-US5 tests pass

**Checkpoint**: User Story 5 complete - historical graphs work with all time ranges

---

## Phase 8: User Story 6 - Quick Server Access and Dashboard (Priority: P6)

**Goal**: Dashboard shows all servers with status, sidebar has quick access dropdown

**Independent Test**: Add multiple servers, view dashboard with status summaries, use sidebar dropdown

### Views for User Story 6

- [x] T130 [US6] Create DashboardView with server list, status summaries, and fleet health overview in `ssh_monitor/apps/servers/views.py` *(completed during reworks: T213, T214)*
- [x] T131 [US6] Update context processor to include servers with alert status for sidebar dropdown *(completed during reworks)*

### Templates for User Story 6

- [x] T132 [US6] Create dashboard template in `ssh_monitor/apps/servers/templates/servers/dashboard.html` *(completed during reworks: T200, T213, T214)*
- [x] T133 [US6] Update base template sidebar with server dropdown component *(completed during reworks: T210, T211, T212)*
- [x] T134 [US6] Add visual indicators for server status (online/offline) and alert status (normal/warning/critical) *(completed during reworks: T213, T214)*

### Tests for User Story 6 (Required per Constitution)

- [x] T135 [P] [US6] Unit tests for dashboard view in `ssh_monitor/tests/unit/test_dashboard.py`
- [x] T136 [US6] Integration tests for dashboard display in `ssh_monitor/tests/integration/test_dashboard.py`
- [x] T137 [US6] Run full test suite and verify all US1-US6 tests pass

**Checkpoint**: User Story 6 complete - dashboard and sidebar navigation work

---

## Phase 9: User Story 7 - Server Management Operations (Priority: P7)

**Goal**: Users can edit, toggle, and delete servers

**Independent Test**: Edit server name/credentials, toggle monitoring off/on, delete server

### Views for User Story 7

- [x] T138 [US7] Create ServerUpdateView in `ssh_monitor/apps/servers/views.py`
- [x] T139 [US7] Create ServerDeleteView with PeriodicTask cleanup in `ssh_monitor/apps/servers/views.py` *(completed during reworks: T241)*
- [x] T140 [US7] Create ServerToggleView for monitoring enable/disable in `ssh_monitor/apps/servers/views.py` *(completed during reworks: T208)*
- [x] T141 [US7] Update Celery task scheduling on server update (interval change)
- [x] T142 [US7] Implement task removal on server delete or monitoring disable *(completed during reworks: T241)*

### Templates for User Story 7

- [x] T143 [P] [US7] Create server edit template (reuse server_form.html with edit mode)
- [x] T144 [P] [US7] Create server delete confirmation template *(N/A - replaced by inline "Danger Zone" in server_detail.html per T242)*
- [x] T145 [US7] Add edit/toggle/delete buttons to server detail and list templates *(completed during reworks: T208, T242)*

### Tests for User Story 7 (Required per Constitution)

- [x] T146 [P] [US7] Unit tests for server update/delete views in `ssh_monitor/tests/unit/test_server_views.py`
- [x] T147 [US7] Integration tests for edit/toggle/delete flow in `ssh_monitor/tests/integration/test_server_management.py`
- [x] T148 [US7] Run full test suite and verify all US1-US7 tests pass

**Checkpoint**: User Story 7 complete - all server management operations work

---

## Phase 10: Alert History (Cross-cutting from US2/US3)

**Goal**: Global and per-server alert history views with filtering

**Independent Test**: Trigger several alerts, view history with filters by server/event type/date

### Views for Alert History

- [x] T149 Create AlertHistoryView (global) in `ssh_monitor/apps/alerts/views.py`
- [x] T150 Create ServerAlertHistoryView (per-server) in `ssh_monitor/apps/alerts/views.py`
- [x] T151 Implement filtering by server, event_type, metric_type, date_from, date_to
- [x] T152 Implement pagination for history views

### Templates for Alert History

- [x] T153 [P] Create global alert history template in `ssh_monitor/apps/alerts/templates/alerts/history.html`
- [x] T154 [P] Create server alert history template in `ssh_monitor/apps/alerts/templates/alerts/server_history.html`
- [x] T155 Add filter form component to history templates

### Tests for Alert History

- [x] T156 [P] Unit tests for alert history views in `ssh_monitor/tests/unit/test_alert_history.py`
- [x] T157 Integration tests for history filtering in `ssh_monitor/tests/integration/test_alert_history.py`
- [x] T158 Run full test suite and verify all tests pass

**Checkpoint**: Alert history complete with filtering and pagination

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T159 [P] Create README.md with project description, setup instructions, development workflow
- [x] T160 [P] Create data cleanup Celery task for 30-day retention in `ssh_monitor/apps/servers/tasks.py`
- [x] T161 [P] Add cleanup task to Celery beat schedule (daily)
- [x] T162 Code cleanup: remove dead code, ensure consistent formatting with Black
- [x] T163 Run Ruff linter and fix all issues
- [x] T164 Review and optimize database queries (add select_related/prefetch_related where needed)
- [x] T165 Security review: verify all views require authentication, credentials encrypted
- [x] T166 Run full test suite with coverage report, ensure >80% coverage on services
- [x] T167 Validate quickstart.md instructions work end-to-end
- [x] T168 Final Docker build and deployment test
- [x] T169 [P] Load test with 50 simulated servers to verify SC-002 (50 servers without degradation)
- [x] T170 Integration test for service restart recovery within 5 minutes (SC-009) in `ssh_monitor/tests/integration/test_service_recovery.py`
- [x] T171 [P] Add logging/metrics for check interval accuracy tracking (SC-007: 95% of scheduled checks execute on time)
- [x] T172 [P] Implement graceful degradation for disk full on monitoring server (log error, continue operation, alert admin)

**Checkpoint**: Production-ready, all tests pass, documentation complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phases 3-9 (User Stories)**: All depend on Phase 2 completion
  - US1 (P1): No dependencies on other stories - **MVP**
  - US2 (P2): Depends on US1 (needs Server and MetricSnapshot models)
  - US3 (P3): Depends on US2 (needs AlertRule and AlertEvent models)
  - US4 (P4): Depends on US2 (needs AlertRule model)
  - US5 (P5): Depends on US1 (needs MetricSnapshot model)
  - US6 (P6): Depends on US1 (needs Server model)
  - US7 (P7): Depends on US1 (needs Server model)
- **Phase 10 (Alert History)**: Depends on US2 and US3
- **Phase 11 (Polish)**: Depends on all desired user stories being complete

### User Story Independence

| Story | Can Start After | Independent Test |
|-------|-----------------|------------------|
| US1 | Phase 2 | Add server, see metrics |
| US2 | US1 | Create alert, see in list |
| US3 | US2 | Configure Telegram, receive notification |
| US4 | US2 | Create template, add server, verify clone |
| US5 | US1 | View historical graphs |
| US6 | US1 | View dashboard, use sidebar |
| US7 | US1 | Edit/toggle/delete server |

### Parallel Opportunities

**Within Phase 1 (Setup)**:
```
T003, T004, T006, T007, T011 can run in parallel
```

**Within Phase 2 (Foundational)**:
```
T015, T016, T017, T018 can run in parallel (app creation)
T027, T028, T029 can run in parallel (tests)
```

**Within US1**:
```
T031, T032, T033 can run in parallel (models)
T048, T049 can run in parallel (templates)
T052, T053, T054, T055 can run in parallel (tests)
```

**After Phase 2, user stories can proceed in parallel if team capacity allows**

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently
5. Deploy/demo if ready

### Recommended Incremental Delivery

1. Setup + Foundational → Foundation ready
2. **US1** → Test → Deploy (MVP: Add server, see metrics)
3. **US2** → Test → Deploy (Alerting rules)
4. **US3** → Test → Deploy (Telegram notifications)
5. **US5** → Test → Deploy (Historical graphs)
6. **US6** → Test → Deploy (Dashboard)
7. **US4** → Test → Deploy (Default templates)
8. **US7** → Test → Deploy (Server management)
9. Alert History → Test → Deploy
10. Polish → Final release

---

## Task Summary

| Phase | Tasks | Parallel Tasks |
|-------|-------|----------------|
| Phase 1: Setup | 13 | 5 |
| Phase 2: Foundational | 17 | 8 |
| Phase 3: US1 (MVP) | 28 | 11 |
| Phase 4: US2 | 24 | 6 |
| Phase 5: US3 | 20 | 6 |
| Phase 6: US4 | 17 | 4 |
| Phase 7: US5 | 11 | 2 |
| Phase 8: US6 | 8 | 2 |
| Phase 9: US7 | 11 | 4 |
| Phase 10: Alert History | 10 | 4 |
| Phase 11: Polish | 14 | 7 |
| **Total** | **173** | **60** |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are REQUIRED per Constitution Principle IV
- Run full test suite after each phase (regression check)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
