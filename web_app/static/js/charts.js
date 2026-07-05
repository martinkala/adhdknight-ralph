const ADHD = {
    colors: {
        positive: 'rgba(76,175,80,0.7)',
        positiveBorder: '#388E3C',
        negative: 'rgba(244,67,54,0.7)',
        negativeBorder: '#C62828',
        primary: '#1976D2',
        primaryLight: 'rgba(25,118,210,0.4)',
    },
    defaultFont: { family: "system-ui, -apple-system, sans-serif", size: 13 },
    barChartDefaults(labels, values) {
        const colors = values.map(v => v >= 0 ? this.colors.positive : this.colors.negative);
        const borders = values.map(v => v >= 0 ? this.colors.positiveBorder : this.colors.negativeBorder);
        return {
            type: 'bar',
            data: { labels, datasets: [{ data: values, backgroundColor: colors, borderColor: borders, borderWidth: 1, borderRadius: 3 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { ticks: { maxRotation: 45 } } }
            }
        };
    },
};
