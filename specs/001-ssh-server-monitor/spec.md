# Feature Specification: SSH Server Monitor

**Feature Branch**: `001-ssh-server-monitor`  
**Created**: 2026-02-03  
**Status**: Draft  
**Input**: User description: "All-in-one SSH-based server resources monitoring platform with centralized web interface and configurable alerting"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add and Monitor First Server (Priority: P1)

As a user, I want to add my first VPS server to the monitoring system and see its live metrics, so I can verify the system works and start tracking my server's health.

**Why this priority**: This is the core value proposition—without being able to add a server and see its metrics, the product has no utility. This establishes the fundamental SSH-based monitoring capability.

**Independent Test**: Can be fully tested by adding one server with SSH credentials and viewing its metrics on the detail page. Delivers immediate value by showing server health status.

**Acceptance Scenarios**:

1. **Given** I am on the servers list page, **When** I click "Add Server" and provide server name, host/IP, port, and password credentials, **Then** the server is added and appears in the list with a "Connecting..." status that updates to show basic metrics within 60 seconds.

2. **Given** I am adding a server, **When** I choose "SSH Key File" authentication and upload my private key file, **Then** the system accepts the key and uses it for all subsequent connections.

3. **Given** I am adding a server, **When** I choose "Generate SSH Key" and provide my current password, **Then** the system connects with the password, generates a new key pair, installs the public key on the server, and uses the private key for future connections.

4. **Given** a server is successfully added, **When** I click on the server in the list, **Then** I see a detail page with live metrics including CPU load, RAM usage, disk space, and other available system parameters.

5. **Given** I am on the server detail page, **When** the configured check interval passes, **Then** the metrics automatically refresh without manual page reload.

---

### User Story 2 - Configure Server Alerts (Priority: P2)

As a user, I want to set up alert rules for my server so that I get notified when resource usage exceeds thresholds I define.

**Why this priority**: Monitoring without alerting requires constant manual checking. Alerts transform the system from passive display to proactive notification, which is essential for managing servers effectively.

**Independent Test**: Can be tested by adding an alert rule (e.g., "RAM usage > 80%") and verifying it triggers when conditions are met. Delivers value by automating the detection of server issues.

**Acceptance Scenarios**:

1. **Given** I am on a server's detail page, **When** I navigate to the alerts section and create a new alert with type "warning", parameter "RAM usage percentage", condition "greater than", and value "80", **Then** the alert is saved and appears in the server's alert list.

2. **Given** an alert is configured with a remind timer of "1 hour", **When** the alert condition remains true after the initial notification, **Then** I receive reminder notifications at the specified interval until the condition clears.

3. **Given** an alert is configured with "notify on dismissal" enabled, **When** the alert condition that was previously triggered becomes false, **Then** I receive a dismissal notification.

4. **Given** an alert with a dismissal threshold of "5 minutes" is triggered, **When** the condition briefly clears for 2 minutes and then triggers again, **Then** no dismissal notification is sent (threshold not met).

5. **Given** I have created multiple alerts for a server, **When** I view the server's alert configuration, **Then** I see all alerts listed with their type (warning/critical), parameter, condition, value, and current status (active/triggered/dismissed).

---

### User Story 3 - Set Up Telegram Notifications (Priority: P3)

As a user, I want to configure Telegram as my notification channel so that I receive alerts on my phone or desktop via Telegram.

**Why this priority**: Alerts are only useful if they reach the user. Telegram provides a widely accessible, real-time notification channel that works across devices without additional infrastructure.

**Independent Test**: Can be tested by configuring Telegram credentials and triggering a test notification. Delivers value by connecting the alerting system to a real communication channel.

**Acceptance Scenarios**:

1. **Given** I am on the alerting channels configuration page, **When** I enter a valid Telegram bot token and chat/group ID, **Then** the system validates the credentials by sending a test message and confirms successful setup.

2. **Given** Telegram is configured, **When** any server alert is triggered, **Then** I receive a Telegram message containing the server name, alert type (warning/critical), parameter, current value, and threshold.

3. **Given** Telegram is configured, **When** an alert with "notify on dismissal" is cleared, **Then** I receive a Telegram message indicating the alert has been resolved.

4. **Given** Telegram credentials are invalid or the bot is removed from the group, **When** an alert tries to send, **Then** the system logs the delivery failure and displays a warning in the UI about the broken notification channel.

---

### User Story 4 - Manage Default Alert Templates (Priority: P4)

As a user, I want to define default alert rules that automatically apply to every new server I add, so I don't have to manually configure the same basic alerts repeatedly.

**Why this priority**: Once users have multiple servers, manually configuring identical alerts becomes tedious. Default templates reduce setup friction and ensure consistent monitoring across the fleet.

**Independent Test**: Can be tested by creating default alerts, adding a new server, and verifying the alerts are automatically cloned to it. Delivers value by automating repetitive configuration.

**Acceptance Scenarios**:

1. **Given** I am on the default alerts configuration page, **When** I create a default alert (e.g., "Disk space < 10%", critical), **Then** the alert is saved as a template.

2. **Given** default alerts are configured, **When** I add a new server, **Then** all default alerts are automatically cloned to the new server's alert configuration.

3. **Given** a server has cloned default alerts, **When** I modify one of those alerts on the server, **Then** only that server's alert is changed—the default template and other servers remain unaffected.

4. **Given** I modify a default alert template, **When** I view existing servers, **Then** their previously cloned alerts remain unchanged (no retroactive updates).

---

### User Story 5 - View Historical Metrics and Trends (Priority: P5)

As a user, I want to see historical metrics and graphs for my servers so that I can identify trends, plan capacity, and investigate past incidents.

**Why this priority**: Live metrics show current state but don't help with trend analysis or post-incident investigation. Historical data enables proactive capacity planning and root cause analysis.

**Independent Test**: Can be tested by monitoring a server for a period, then viewing historical graphs. Delivers value by enabling trend analysis and capacity planning.

**Acceptance Scenarios**:

1. **Given** a server has been monitored for at least 1 hour, **When** I view the server detail page, **Then** I see graphs showing metric history over selectable time ranges (1 hour, 6 hours, 24 hours, 7 days, 30 days).

2. **Given** I am viewing a historical graph, **When** I hover over a point on the graph, **Then** I see the exact timestamp and metric value at that point.

3. **Given** a server had an alert trigger in the past, **When** I view the historical graph for that metric, **Then** the time period when the alert was active is visually indicated on the graph.

---

### User Story 6 - Quick Server Access and Dashboard (Priority: P6)

As a user, I want a dashboard overview of all servers and quick navigation to any server's details, so I can efficiently manage multiple servers without excessive clicking.

**Why this priority**: With multiple servers, navigation efficiency becomes important. The dashboard provides at-a-glance fleet health, and quick access reduces friction for common workflows.

**Independent Test**: Can be tested by adding multiple servers and using the sidebar dropdown for quick navigation. Delivers value by improving daily workflow efficiency.

**Acceptance Scenarios**:

1. **Given** I have multiple servers added, **When** I view the dashboard, **Then** I see all servers listed with their current status (online/offline), key metrics summary (CPU, RAM, disk), and alert status (normal/warning/critical).

2. **Given** I am on any page in the application, **When** I click the server dropdown in the sidebar, **Then** I see a list of all servers and can click any to go directly to its detail page.

3. **Given** a server has active alerts, **When** I view the dashboard or sidebar, **Then** that server is visually distinguished (color/icon) to indicate it needs attention.

---

### User Story 7 - Server Management Operations (Priority: P7)

As a user, I want to edit server configurations, temporarily disable monitoring, or remove servers, so I can maintain my server inventory as my infrastructure changes.

**Why this priority**: Infrastructure changes over time—servers are decommissioned, IPs change, credentials rotate. Management operations ensure the monitoring system can evolve with the infrastructure.

**Independent Test**: Can be tested by editing a server's settings, toggling monitoring off/on, and deleting a server. Delivers value by enabling ongoing maintenance of the server fleet.

**Acceptance Scenarios**:

1. **Given** I am viewing a server's details, **When** I click "Edit" and change the server's name, SSH credentials, or check interval, **Then** the changes are saved and take effect on the next monitoring cycle.

2. **Given** a server exists in the system, **When** I toggle the monitoring switch to "off", **Then** the system stops collecting metrics for that server but retains its configuration and historical data.

3. **Given** monitoring is disabled for a server, **When** I toggle monitoring back "on", **Then** metric collection resumes using the existing configuration.

4. **Given** I want to remove a server, **When** I click "Delete" and confirm, **Then** the server and all its metrics/alerts are permanently removed from the system.

5. **Given** I am editing a server, **When** I change the check interval to any value between 1 minute and 24 hours, **Then** the system adjusts the polling frequency accordingly.

---

### Edge Cases

- What happens when SSH connection fails during a check cycle? System immediately retries 3 times in succession. If all 3 fail, system also pings the server, then triggers a non-configurable connectivity alert that includes both SSH failure status and ping result (to distinguish SSH-only issues from full network outages). Server is marked as "unreachable".
- What happens when a server's SSH credentials become invalid? System marks server as "authentication failed", stops attempting connections, and notifies the user to update credentials.
- What happens when the monitoring service restarts? All server checks resume from their configured intervals; no historical data is lost.
- What happens when disk is full on the monitoring server? System should gracefully handle storage issues—alerting the admin and potentially pausing historical data collection while continuing live monitoring.
- What happens when a metric command fails on a specific server? System records null/error for that metric, continues collecting other metrics, and includes partial data in the response.
- What happens when Telegram bot rate limits are hit? System queues notifications and retries with exponential backoff; groups related alerts to reduce message volume.
- What happens when a server is added with an unreachable IP? System attempts initial connection, fails, marks server as "unreachable" from the start, and schedules retries.

## Requirements *(mandatory)*

### Functional Requirements

**Server Management**

- **FR-001**: System MUST allow users to add servers by providing: display name, SSH username, hostname/IP, SSH port (default placeholder: 22), and authentication method.
- **FR-002**: System MUST support three SSH authentication methods: password, SSH key file upload, and automatic key generation using a provided password.
- **FR-003**: System MUST store SSH credentials securely (encrypted at rest).
- **FR-004**: System MUST allow users to edit any server configuration after creation.
- **FR-005**: System MUST allow users to delete servers, removing all associated data.
- **FR-006**: System MUST provide a per-server toggle to enable/disable monitoring without deleting the server.
- **FR-007**: System MUST allow configurable check intervals per server, ranging from 1 minute to 24 hours.

**Metrics Collection**

- **FR-008**: System MUST collect metrics via SSH commands without requiring agent installation on monitored servers.
- **FR-009**: System MUST collect at minimum: CPU load (1/5/15 min averages), RAM usage (used/total/percentage), disk usage per mount point (used/total/percentage), swap usage, and system uptime.
- **FR-010**: System MUST store historical metrics data at full resolution (no downsampling) for trend analysis and graphing.
- **FR-011**: System MUST handle metric collection failures gracefully, logging errors without crashing the monitoring cycle.
- **FR-011a**: On SSH connection failure, system MUST immediately retry 3 consecutive times before marking server as unreachable.
- **FR-011b**: When SSH connection fails after retries, system MUST also ping the server and include ping status in the connectivity alert.
- **FR-011c**: SSH connectivity alerts are non-configurable (always enabled) and cannot be disabled by users.
- **FR-012**: System MUST display live metrics on server detail pages with automatic refresh via data polling (not full page reload).
- **FR-012a**: Frontend MUST use unified rendering logic for both initial page data and polled updates (same code path renders initial server-provided data and subsequent fetched data).

**Alerting**

- **FR-013**: System MUST support two alert severity levels: warning and critical.
- **FR-014**: System MUST support alerts on all collected metrics (CPU, RAM, disk, swap, load average, etc.).
- **FR-015**: System MUST support alert conditions: greater than, less than, equals, greater than or equals, less than or equals, and within/outside range.
- **FR-016**: System MUST support configurable reminder intervals for ongoing alert conditions (off, or 15 minutes to 24 hours).
- **FR-017**: System MUST support optional dismissal notifications when alert conditions clear.
- **FR-018**: System MUST support dismissal thresholds to prevent notification spam from flapping conditions.
- **FR-019**: System MUST support default alert templates that automatically apply to newly added servers.
- **FR-020**: Default alerts MUST be cloned (not linked) to new servers, allowing independent modification per server.

**Notification Channels**

- **FR-021**: System MUST support Telegram as a notification channel.
- **FR-022**: System MUST provide a configuration interface for Telegram bot token and chat/group ID.
- **FR-023**: System MUST validate Telegram credentials by sending a test message.
- **FR-024**: System MUST be architecturally designed to support additional notification channels in the future.
- **FR-025**: Alert notifications MUST include: server name, alert severity, metric name, current value, threshold, and timestamp.

**User Interface**

- **FR-026**: System MUST provide a dashboard showing all servers with status summaries.
- **FR-027**: System MUST provide a sidebar with dropdown for quick access to any server's detail page.
- **FR-028**: System MUST visually distinguish servers with active alerts (warning vs critical vs normal).
- **FR-029**: System MUST provide historical metric graphs with selectable time ranges.
- **FR-030**: System MUST display tooltips with exact values when hovering over graph points.
- **FR-031**: System MUST indicate alert-active periods on historical graphs.
- **FR-031a**: System MUST provide a global alert history page showing all alert events across servers.
- **FR-031b**: System MUST provide per-server alert history on server detail pages.
- **FR-031c**: Alert history views MUST support filtering by server, event type (triggered/reminded/dismissed), metric type, and date range.

**Users & Access**

- **FR-032**: System MUST support multiple user accounts with username/password authentication (local accounts, no external identity providers).
- **FR-033**: All users MUST have equal administrative access (no role hierarchy).
- **FR-034**: All users MUST see and control the same servers and settings (shared data model).
- **FR-035**: System MUST provide a CLI management command to create user accounts (used for initial setup and user administration).

### Key Entities

- **Server**: Represents a monitored VPS. Attributes: name, ssh_username, host, port, auth type, credentials (encrypted), check interval, monitoring enabled flag, created date, last check timestamp, connection status. **Uniqueness**: host+port combination must be unique (no duplicate servers allowed).

- **Metric Snapshot**: A point-in-time collection of metrics for a server. Attributes: server reference, timestamp, CPU loads, RAM values, disk values per mount, swap values, uptime, collection status (success/partial/failed).

- **Alert Rule**: A condition that triggers notifications. Attributes: server reference (or null for default), severity level, metric parameter, condition operator, threshold value(s), reminder interval, notify on dismissal flag, dismissal threshold, enabled flag, current state (normal/triggered).

- **Alert Event**: A record of an alert triggering or clearing. Attributes: alert rule reference, event type (triggered/reminded/dismissed), timestamp, metric value at event time, notification delivery status.

- **Notification Channel**: Configuration for a notification delivery method. Attributes: channel type (telegram), configuration data (bot token, chat ID), enabled flag, last validation timestamp, validation status.

- **User**: A person who can access the system. Attributes: username, password hash, created date, last login.

- **Default Alert Template**: A blueprint for alerts auto-applied to new servers. Attributes: same as Alert Rule but without server reference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add a new server and see live metrics within 2 minutes of providing valid SSH credentials.
- **SC-002**: System can monitor at least 50 servers simultaneously without degradation in check frequency accuracy.
- **SC-003**: Alert notifications are delivered within 60 seconds of condition detection.
- **SC-004**: Historical metric data is retained for at least 30 days.
- **SC-005**: Users can navigate from dashboard to any server's detail page in 2 clicks or fewer.
- **SC-006**: Server detail page loads and displays current metrics within 3 seconds.
- **SC-007**: 95% of scheduled metric checks complete within their scheduled interval (no significant drift).
- **SC-008**: Users can configure a complete alert (all fields) in under 1 minute.
- **SC-009**: System recovers and resumes monitoring within 5 minutes after an unexpected restart.

## Clarifications

### Session 2026-02-03

- Q: How do users authenticate to the monitoring system? → A: Username/password with local accounts (no external dependencies)
- Q: Should historical metrics be downsampled over time? → A: No downsampling; full resolution for entire 30-day retention period
- Q: How should SSH connectivity failures trigger alerts? → A: Non-configurable alert; 3 immediate consecutive retries; on failure also ping server and include ping status in alert to distinguish SSH-only vs full network outage
- Q: Can users add the same server (host+port) multiple times? → A: No; host+port combination must be unique (duplicates prevented)
- Q: How should live metrics updates work? → A: Polling (data only, not full page); unified rendering logic for initial page load and polled updates—backend serves page with initial data, frontend renders using same logic for both initial and subsequent data
- Q: How is SSH username specified? → A: User specifies all connection details (username, hostname, port); only port has default placeholder (22)
- Q: How is the first admin user created? → A: CLI/devops management command (run before or during deployment)
- Q: Should users see alert history in the UI? → A: Both global and per-server views, with filters (server, event type, metric type, etc.)
- Q: How long should user sessions last? → A: Use framework default (defer to technical implementation)
- Q: Should users be able to export metrics data? → A: No export; view in UI only (export can be added later if needed)

## Assumptions

- Target servers are Linux-based and have standard commands available (top, free, df, uptime, cat /proc/*).
- SSH access is available on target servers with appropriate permissions to read system metrics.
- The monitoring system has reliable network connectivity to target servers.
- Users have basic familiarity with SSH credentials and server administration.
- Telegram bot creation and chat/group ID retrieval are handled outside this system (users bring their own bot).
- Data retention policies beyond 30 days are out of scope for initial release.
- The system will run as a self-hosted application, not as a multi-tenant SaaS.
- Metrics data export is out of scope for initial release (UI viewing only).
