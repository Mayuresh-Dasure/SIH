/**
 * dashboard.js — MPLADS AI Monitor Dashboard (SIH26102 Upgraded)
 *
 * Features:
 *   - Role-Based Access Control (RBAC) Switcher & Context Scoping
 *   - 5 Navigation Tabs Management
 *   - Multi-Signal Filterable Projects Table
 *   - Leaflet Map with Color-Coded Risk Markers
 *   - Chart.js Donut & Quarterly Completion Trends Line Chart
 *   - Alert Inbox & Dispatch Actions (Assign Inspection, Resolve, Escalate)
 *   - eSAKSHI CSV Drag-and-Drop Ingestion Pipeline
 */

(function () {
    'use strict';

    // ── Application State ───────────────────────────────────────
    let currentRole = 'ministry';
    let currentMp = 'Shri Piyush Goyal';
    let currentDistrict = 'Mumbai Suburban';
    let allProjects = [];
    let sortColumn = 'risk_score';
    let sortDirection = 'desc';
    let searchTimeout = null;
    let map = null;
    let markersLayer = null;
    let donutChart = null;
    let trendsChart = null;

    // ── Initialization ──────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        initRoleFromUrl();
        initTabs();
        initRoleSwitcher();
        fetchSummary();
        fetchProjects();
        initMap();
        initCharts();
        bindFilters();
        bindSort();
        bindRecalculate();
        initCsvUpload();
        fetchAlerts();
    });

    // ── RBAC Role Switcher ──────────────────────────────────────
    function initRoleFromUrl() {
        const params = new URLSearchParams(window.location.search);
        const role = params.get('role');
        if (role && ['ministry', 'state_nodal', 'district_authority', 'mp'].includes(role)) {
            currentRole = role;
        }
        updateRoleUI(currentRole);
    }

    function initRoleSwitcher() {
        document.querySelectorAll('.role-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const role = btn.dataset.role;
                currentRole = role;
                updateRoleUI(role);

                // Update URL without full page reload
                const url = new URL(window.location);
                url.searchParams.set('role', role);
                window.history.pushState({}, '', url);

                // Refresh data
                fetchSummary();
                fetchProjects();
                refreshMapData();
                fetchAlerts();
            });
        });
    }

    function updateRoleUI(role) {
        document.querySelectorAll('.role-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.role === role);
        });

        const bannerText = document.getElementById('role-banner-text');
        const mpWidget = document.getElementById('mp-entitlement-widget');
        const routingBadge = document.getElementById('routing-current-role');

        if (role === 'ministry') {
            bannerText.innerHTML = 'Viewing as <strong>Ministry (MoSPI)</strong> — Consolidated National & State Portfolio';
            mpWidget.style.display = 'none';
            if (routingBadge) routingBadge.textContent = 'Routed to: MoSPI Central Vigilance';
        } else if (role === 'state_nodal') {
            bannerText.innerHTML = 'Viewing as <strong>Maharashtra State Nodal Officer</strong> — State-Wide Constituency Oversight';
            mpWidget.style.display = 'none';
            if (routingBadge) routingBadge.textContent = 'Routed to: Maharashtra State Nodal';
        } else if (role === 'district_authority') {
            bannerText.innerHTML = 'Viewing as <strong>District Magistrate (Mumbai Suburban)</strong> — Sanctioning & Inspection Queue';
            mpWidget.style.display = 'none';
            if (routingBadge) routingBadge.textContent = 'Routed to: District Planning Authority';
        } else if (role === 'mp') {
            bannerText.innerHTML = `Viewing as <strong>Honorable MP (${currentMp})</strong> — Constituency Fund & Milestone Tracker`;
            mpWidget.style.display = 'block';
            if (routingBadge) routingBadge.textContent = `Routed to: MP Office (${currentMp})`;
        }
    }

    // ── Navigation Tabs ─────────────────────────────────────────
    function initTabs() {
        document.querySelectorAll('.dash-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.dash-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                tab.classList.add('active');
                const target = document.getElementById(tab.dataset.tab);
                if (target) target.classList.add('active');

                if (tab.dataset.tab === 'tab-alerts') {
                    fetchAlerts();
                } else if (tab.dataset.tab === 'tab-kpis') {
                    renderTrendsChart();
                } else if (tab.dataset.tab === 'tab-overview' && map) {
                    setTimeout(() => map.invalidateSize(), 200);
                }
            });
        });
    }

    // ── Summary & Stats ─────────────────────────────────────────
    function fetchSummary() {
        const url = `/api/summary?role=${currentRole}&mp_name=${encodeURIComponent(currentMp)}&district=${encodeURIComponent(currentDistrict)}`;
        fetch(url)
            .then(res => res.json())
            .then(stats => {
                updateText('total-projects', stats.total_projects);
                updateText('completed-count', stats.completed);
                updateText('delayed-count', stats.delayed);
                updateText('total-sanctioned', `₹${stats.total_sanctioned.toFixed(1)}L`);
                updateText('total-utilized', `₹${stats.total_utilized.toFixed(1)}L`);
                updateText('active-alerts-count', stats.total_active_alerts);
                updateText('low-risk-count', stats.low_risk);
                updateText('medium-risk-count', stats.medium_risk);
                updateText('high-risk-count', stats.high_risk);
                updateText('alerts-tab-badge', stats.total_active_alerts);

                if (stats.mp_uncommitted_lakhs !== undefined) {
                    updateText('mp-sanctioned-val', `₹${stats.total_sanctioned.toFixed(1)} Lakhs`);
                    updateText('mp-balance-val', `₹${stats.mp_uncommitted_lakhs.toFixed(1)} Lakhs`);
                }

                updateDonutChart(stats.low_risk, stats.medium_risk, stats.high_risk);
            })
            .catch(err => console.error('Summary error:', err));
    }

    // ── Projects Table & Filters ────────────────────────────────
    function fetchProjects() {
        const params = getFilterParams();
        params.role = currentRole;
        if (currentRole === 'mp') params.mp_name = currentMp;
        if (currentRole === 'district_authority') params.district = currentDistrict;

        const url = '/api/projects?' + new URLSearchParams(params).toString();
        fetch(url)
            .then(res => res.json())
            .then(data => {
                allProjects = data;
                renderTable(data);
                updateText('results-count', data.length);
            })
            .catch(err => console.error('Fetch projects error:', err));
    }

    function getFilterParams() {
        const params = {};
        const q = document.getElementById('search-input')?.value?.trim();
        const status = document.getElementById('filter-status')?.value;
        const risk = document.getElementById('filter-risk')?.value;
        const constituency = document.getElementById('filter-constituency')?.value;
        const category = document.getElementById('filter-category')?.value;
        const compliance = document.getElementById('filter-compliance')?.value;
        const early_warning = document.getElementById('filter-early-warning')?.value;

        if (q) params.q = q;
        if (status) params.status = status;
        if (risk) params.risk = risk;
        if (constituency) params.constituency = constituency;
        if (category) params.category = category;
        if (compliance) params.compliance = compliance;
        if (early_warning) params.early_warning = early_warning;

        return params;
    }

    function renderTable(projects) {
        const tbody = document.getElementById('projects-tbody');
        if (!tbody) return;

        const sorted = [...projects].sort((a, b) => {
            let aVal = a[sortColumn];
            let bVal = b[sortColumn];
            if (typeof aVal === 'string') aVal = aVal.toLowerCase();
            if (typeof bVal === 'string') bVal = bVal.toLowerCase();
            if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        tbody.innerHTML = sorted.map(p => {
            const riskClass = getRiskClass(p.risk_score);
            const statusClass = getStatusClass(p.status);
            const compClass = p.compliance_status === 'PASSED' ? 'comp-badge-pass' : (p.compliance_status === 'WARNING' ? 'comp-badge-warn' : 'comp-badge-fail');
            const ewClass = `ew-${(p.early_warning_level || 'on_track').toLowerCase()}`;

            return `
                <tr>
                    <td>
                        <strong>${escapeHtml(p.project_name)}</strong>
                        <div style="font-size: 0.72rem; color: #64748b;">Agency: ${escapeHtml(p.implementing_agency || 'MCGM')}</div>
                    </td>
                    <td>
                        ${escapeHtml(p.constituency)}<br>
                        <span style="font-size: 0.72rem; color: #94a3b8;">${escapeHtml(p.mp_name)}</span>
                    </td>
                    <td>${escapeHtml(p.category)}</td>
                    <td style="font-family: var(--font-mono); font-weight: 600;">₹${p.sanctioned_amount.toFixed(1)}L</td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <div style="width: 45px; height: 4px; background: rgba(255,255,255,0.08); border-radius: 100px;">
                                <div style="width: ${Math.min(p.utilization_pct, 100)}%; height: 100%; background: var(--gradient-primary); border-radius: 100px;"></div>
                            </div>
                            <span style="font-family: var(--font-mono); font-size: 0.75rem;">${p.utilization_pct}%</span>
                        </div>
                    </td>
                    <td><span class="comp-badge ${compClass}">${p.compliance_status}</span></td>
                    <td><span class="ew-badge ${ewClass}">${p.early_warning_level || 'ON_TRACK'}</span></td>
                    <td><span class="risk-badge ${riskClass}">${p.risk_score.toFixed(0)}</span></td>
                    <td><a href="/project/${p.id}?role=${currentRole}" class="btn" style="padding: 4px 10px; font-size: 0.75rem;">View →</a></td>
                </tr>
            `;
        }).join('');
    }

    // ── Alerts & Escalation Inbox ───────────────────────────────
    function fetchAlerts() {
        const url = `/api/alerts?role=${currentRole}&mp_name=${encodeURIComponent(currentMp)}&district=${encodeURIComponent(currentDistrict)}`;
        fetch(url)
            .then(res => res.json())
            .then(alerts => {
                renderAlertsTable(alerts);
                updateText('alerts-tab-badge', alerts.length);
            })
            .catch(err => console.error('Alerts error:', err));
    }

    function renderAlertsTable(alerts) {
        const tbody = document.getElementById('alerts-tbody');
        if (!tbody) return;

        if (alerts.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: #94a3b8;">✓ No active critical alerts in current jurisdiction.</td></tr>`;
            return;
        }

        tbody.innerHTML = alerts.map(a => {
            const riskClass = getRiskClass(a.risk_score);
            const compFlag = (a.compliance_flags && a.compliance_flags.length > 0) ? a.compliance_flags[0] : 'Guideline flag';

            return `
                <tr>
                    <td>
                        <strong>${escapeHtml(a.project_name)}</strong>
                        <div style="font-size: 0.72rem; color: #ef4444; margin-top: 2px;">
                            ${(a.risk_reasons && a.risk_reasons.length > 0) ? escapeHtml(a.risk_reasons[0]) : ''}
                        </div>
                    </td>
                    <td>${escapeHtml(a.constituency)}</td>
                    <td><span class="routing-badge">${escapeHtml(a.alert_assigned_to || 'DM')}</span></td>
                    <td style="font-family: var(--font-mono);">₹${a.sanctioned_amount.toFixed(1)}L</td>
                    <td><span class="risk-badge ${riskClass}">${a.risk_score.toFixed(0)}</span></td>
                    <td><span style="font-size: 0.72rem; color: #f59e0b;">${escapeHtml(compFlag.substring(0, 50))}...</span></td>
                    <td><span class="status-badge ${a.alert_status === 'RESOLVED' ? 'status-completed' : 'status-delayed'}">${a.alert_status}</span></td>
                    <td>
                        <div style="display: flex; gap: 4px;">
                            <button class="btn-action" onclick="window.dispatchAlertAction(${a.id}, 'ASSIGN_INSPECTION')">🔍 Inspect</button>
                            <button class="btn-action" onclick="window.dispatchAlertAction(${a.id}, 'RESOLVE')">✓ Resolve</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    window.dispatchAlertAction = function (projectId, actionType) {
        fetch(`/api/alerts/${projectId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action_type: actionType,
                performed_by: currentRole === 'ministry' ? 'MoSPI Vigilance' : 'District Magistrate',
                role: currentRole,
                notes: `Action ${actionType} triggered from Alert Inbox.`
            })
        })
        .then(res => res.json())
        .then(data => {
            alert(`✓ ${data.message}`);
            fetchAlerts();
            fetchSummary();
        })
        .catch(err => alert('Failed to execute alert action.'));
    };

    // ── Map Initialization ──────────────────────────────────────
    function initMap() {
        const mapEl = document.getElementById('mumbai-map');
        if (!mapEl) return;

        map = L.map('mumbai-map').setView([19.076, 72.877], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        markersLayer = L.layerGroup().addTo(map);
        refreshMapData();
    }

    function refreshMapData() {
        if (!markersLayer) return;
        markersLayer.clearLayers();

        const url = `/api/map-data?role=${currentRole}&mp_name=${encodeURIComponent(currentMp)}&district=${encodeURIComponent(currentDistrict)}`;
        fetch(url)
            .then(res => res.json())
            .then(data => {
                data.forEach(p => {
                    if (!p.latitude || !p.longitude) return;
                    const color = p.risk_score > 60 ? '#ef4444' : (p.risk_score > 30 ? '#f59e0b' : '#10b981');
                    const radius = p.risk_score > 60 ? 8 : (p.risk_score > 30 ? 6 : 5);

                    const marker = L.circleMarker([p.latitude, p.longitude], {
                        radius: radius,
                        fillColor: color,
                        color: color,
                        weight: 1.5,
                        opacity: 0.9,
                        fillOpacity: 0.6
                    });

                    marker.bindPopup(`
                        <div style="min-width: 190px;">
                            <strong>${escapeHtml(p.project_name)}</strong><br>
                            <span style="font-size: 0.75rem; color: #94a3b8;">${escapeHtml(p.category)} • ${escapeHtml(p.constituency)}</span>
                            <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.1);">
                                <span style="color: ${color}; font-weight: 700;">Score: ${p.risk_score.toFixed(0)}</span> |
                                <span style="font-size: 0.75rem;">${escapeHtml(p.compliance_status || 'PASSED')}</span>
                            </div>
                            <a href="/project/${p.id}?role=${currentRole}" style="color: #67e8f9; font-size: 0.8rem; display: inline-block; margin-top: 6px;">View Full Details →</a>
                        </div>
                    `);
                    marker.addTo(markersLayer);
                });
            })
            .catch(err => console.error('Map fetch error:', err));
    }

    // ── Charts ──────────────────────────────────────────────────
    function initCharts() {
        const donutCanvas = document.getElementById('risk-donut-chart');
        if (donutCanvas) {
            donutChart = new Chart(donutCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                    datasets: [{
                        data: [110, 10, 8],
                        backgroundColor: ['rgba(16, 185, 129, 0.85)', 'rgba(245, 158, 11, 0.85)', 'rgba(239, 68, 68, 0.85)'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    cutout: '70%',
                    plugins: { legend: { display: false } }
                }
            });
        }
    }

    function updateDonutChart(low, med, high) {
        if (donutChart) {
            donutChart.data.datasets[0].data = [low, med, high];
            donutChart.update();
        }
    }

    function renderTrendsChart() {
        const canvas = document.getElementById('completion-trends-chart');
        if (!canvas) return;

        if (trendsChart) {
            trendsChart.destroy();
        }

        fetch('/api/kpis')
            .then(res => res.json())
            .then(data => {
                const trends = data.completion_trends || [];
                const labels = trends.map(t => t.month);
                const completed = trends.map(t => t.completed);
                const expenditure = trends.map(t => t.expenditure_cr);

                trendsChart = new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Cumulative Completed Works',
                                data: completed,
                                borderColor: '#10b981',
                                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                                fill: true,
                                tension: 0.35
                            },
                            {
                                label: 'Expenditure (₹ Crores)',
                                data: expenditure,
                                borderColor: '#6366f1',
                                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                                fill: true,
                                tension: 0.35
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: '#94a3b8' }
                            }
                        },
                        scales: {
                            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
                        }
                    }
                });
            })
            .catch(err => console.error('Trends fetch error:', err));
    }

    // ── eSAKSHI CSV Ingestion ───────────────────────────────────
    function initCsvUpload() {
        const dropzone = document.getElementById('upload-dropzone');
        const fileInput = document.getElementById('csv-file-input');
        const statusEl = document.getElementById('upload-status');

        if (!dropzone || !fileInput) return;

        ['dragenter', 'dragover'].forEach(e => {
            dropzone.addEventListener(e, ev => { ev.preventDefault(); dropzone.classList.add('dragover'); });
        });
        ['dragleave', 'drop'].forEach(e => {
            dropzone.addEventListener(e, ev => { ev.preventDefault(); dropzone.classList.remove('dragover'); });
        });

        dropzone.addEventListener('drop', ev => {
            const files = ev.dataTransfer.files;
            if (files.length > 0) handleFileUpload(files[0]);
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) handleFileUpload(fileInput.files[0]);
        });

        function handleFileUpload(file) {
            statusEl.style.display = 'block';
            statusEl.className = 'upload-status';
            statusEl.textContent = `Processing and evaluating ${file.name}...`;

            const formData = new FormData();
            formData.append('file', file);

            fetch('/api/upload-csv', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    statusEl.className = 'upload-status msg-success';
                    statusEl.textContent = `✓ ${data.message}`;
                    fetchSummary();
                    fetchProjects();
                    refreshMapData();
                } else {
                    statusEl.className = 'upload-status msg-error';
                    statusEl.textContent = `✕ ${data.error}`;
                }
            })
            .catch(err => {
                statusEl.className = 'upload-status msg-error';
                statusEl.textContent = 'Upload failed: ' + err.message;
            });
        }
    }

    // ── Recalculate ─────────────────────────────────────────────
    function bindRecalculate() {
        const btn = document.getElementById('btn-recalculate');
        if (!btn) return;

        btn.addEventListener('click', () => {
            btn.classList.add('loading');
            fetch('/api/recalculate', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    alert('✓ ' + data.message);
                    window.location.reload();
                })
                .catch(err => {
                    alert('Recalculation error: ' + err.message);
                    btn.classList.remove('loading');
                });
        });
    }

    // ── Table Sorting & Search Handlers ─────────────────────────
    function bindFilters() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(fetchProjects, 300);
            });
        }

        ['filter-constituency', 'filter-risk', 'filter-compliance', 'filter-early-warning', 'filter-category'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', fetchProjects);
        });
    }

    function bindSort() {
        document.querySelectorAll('.sortable').forEach(th => {
            th.addEventListener('click', () => {
                const col = th.dataset.sort;
                sortDirection = (sortColumn === col && sortDirection === 'asc') ? 'desc' : 'asc';
                sortColumn = col;
                renderTable(allProjects);
            });
        });
    }

    // ── Helpers ─────────────────────────────────────────────────
    function updateText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function getRiskClass(score) {
        if (score > 60) return 'risk-badge-high';
        if (score > 30) return 'risk-badge-medium';
        return 'risk-badge-low';
    }

    function getStatusClass(status) {
        const map = {
            'Completed': 'status-completed',
            'Ongoing': 'status-ongoing',
            'Delayed': 'status-delayed',
            'Not Started': 'status-not-started'
        };
        return map[status] || 'status-not-started';
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

})();
