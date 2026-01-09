document.addEventListener('DOMContentLoaded', () => {
    loadEvents();
});

async function loadEvents() {
    try {
        const response = await fetch('events.json');
        const events = await response.json();
        renderEvents(events);
    } catch (error) {
        console.error('Failed to load events:', error);
        document.getElementById('upcoming-events').innerHTML =
            '<p class="no-events">Failed to load events. Please try again later.</p>';
    }
}

function renderEvents(events) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const twoWeeksAgo = new Date(today);
    twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);

    // Sort by date
    events.sort((a, b) => new Date(a.date) - new Date(b.date));

    const upcoming = [];
    const recent = [];

    for (const event of events) {
        const eventDate = new Date(event.date);
        eventDate.setHours(0, 0, 0, 0);

        if (eventDate >= today) {
            upcoming.push(event);
        } else if (eventDate >= twoWeeksAgo) {
            recent.push({ ...event, past: true });
        }
    }

    // Recent events: most recent first
    recent.reverse();

    const upcomingContainer = document.getElementById('upcoming-events');
    const recentContainer = document.getElementById('recent-events');

    if (upcoming.length === 0) {
        upcomingContainer.innerHTML = '<p class="no-events">No upcoming events scheduled.</p>';
    } else {
        upcomingContainer.innerHTML = upcoming.map(renderEvent).join('');
    }

    if (recent.length === 0) {
        recentContainer.innerHTML = '<p class="no-events">No recent events.</p>';
    } else {
        recentContainer.innerHTML = recent.map(renderEvent).join('');
    }
}

function renderEvent(event) {
    const date = formatDate(event.date);
    const time = event.time || '';

    const titleHtml = event.url
        ? `<a href="${escapeHtml(event.url)}">${escapeHtml(event.title)}</a>`
        : escapeHtml(event.title);

    const speakerHtml = event.speaker
        ? `<div class="event-speaker">${escapeHtml(event.speaker)}${event.affiliation ? ` (${escapeHtml(event.affiliation)})` : ''}</div>`
        : '';

    const seriesHtml = event.series
        ? (event.series_url
            ? `<a href="${escapeHtml(event.series_url)}" class="event-series">${escapeHtml(event.series)}</a>`
            : `<span class="event-series">${escapeHtml(event.series)}</span>`)
        : '';

    return `
        <article class="event${event.past ? ' past' : ''}">
            <div class="event-title">${titleHtml}</div>
            ${speakerHtml}
            <div class="event-meta">
                <span>${date}${time ? ' at ' + time : ''}</span>
                <span>${escapeHtml(event.location || 'TBD')}</span>
            </div>
            ${seriesHtml}
        </article>
    `;
}

function formatDate(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    const options = { weekday: 'short', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
