/* Chart.js defaults for dark theme */
Chart.defaults.color = '#8b8fa3';
Chart.defaults.borderColor = '#2e3140';
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

/* Activity chart (users + checks by day) */
if (typeof usersByDay !== 'undefined') {
    const allDays = [...new Set([
        ...usersByDay.map(d => d.day),
        ...checksByDay.map(d => d.day),
    ])].sort();

    const usersMap = Object.fromEntries(usersByDay.map(d => [d.day, d.count]));
    const checksMap = Object.fromEntries(checksByDay.map(d => [d.day, d.count]));

    new Chart(document.getElementById('activityChart'), {
        type: 'line',
        data: {
            labels: allDays,
            datasets: [
                {
                    label: 'Юзеры',
                    data: allDays.map(d => usersMap[d] || 0),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59,130,246,0.1)',
                    fill: true,
                    tension: 0.3,
                },
                {
                    label: 'Проверки',
                    data: allDays.map(d => checksMap[d] || 0),
                    borderColor: '#a855f7',
                    backgroundColor: 'rgba(168,85,247,0.1)',
                    fill: true,
                    tension: 0.3,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } },
                x: {
                    ticks: {
                        maxTicksLimit: 10,
                        callback: function(val) {
                            const label = this.getLabelForValue(val);
                            return label ? label.slice(5) : '';  /* MM-DD */
                        }
                    }
                },
            },
        },
    });
}

/* Checks by type (pie) */
if (typeof checksByType !== 'undefined' && checksByType.length) {
    new Chart(document.getElementById('typeChart'), {
        type: 'doughnut',
        data: {
            labels: checksByType.map(d => d.type),
            datasets: [{
                data: checksByType.map(d => d.count),
                backgroundColor: ['#3b82f6', '#a855f7', '#22c55e'],
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } },
        },
    });
}

/* Checks by color (pie) */
if (typeof checksByColor !== 'undefined' && checksByColor.length) {
    const colorMap = { red: '#ef4444', yellow: '#eab308', green: '#22c55e' };
    new Chart(document.getElementById('colorChart'), {
        type: 'doughnut',
        data: {
            labels: checksByColor.map(d => d.color || 'unknown'),
            datasets: [{
                data: checksByColor.map(d => d.count),
                backgroundColor: checksByColor.map(d => colorMap[d.color] || '#6b7280'),
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } },
        },
    });
}

/* Leads by type (pie) */
if (typeof leadsByType !== 'undefined' && leadsByType.length) {
    new Chart(document.getElementById('leadsChart'), {
        type: 'doughnut',
        data: {
            labels: leadsByType.map(d => d.type),
            datasets: [{
                data: leadsByType.map(d => d.count),
                backgroundColor: ['#f97316', '#3b82f6', '#22c55e'],
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } },
        },
    });
}
