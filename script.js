// Replace with your Google Sheets JSON URL
const sheetUrl = 'https://docs.google.com/spreadsheets/d/1axUmdj7sbmA7wn0gTVU-tr4bMiXoLd1ntRdXdEdQwOU/gviz/tq?tqx=out:json';

// Fetch data from Google Sheets
async function fetchSheetData() {
  const response = await fetch(sheetUrl);
  const text = await response.text();
  const json = JSON.parse(text.substr(47).slice(0, -2)); // Parse Google Sheets JSON
  return json.table.rows.map(row => row.c.map(cell => (cell ? cell.v : null)));
}


// Generate Chart
function generateChart(data) {
  const ctx = document.getElementById('beverageChart').getContext('2d');
  const beverageCounts = data.reduce((counts, row) => {
    const bevType = row[1];
    if (bevType) counts[bevType] = (counts[bevType] || 0) + 1;
    return counts;
  }, {});

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Object.keys(beverageCounts),
      datasets: [
        {
          label: 'Beverage Consumption',
          data: Object.values(beverageCounts),
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true },
      },
    },
  });
}

// Main Function
async function main() {
  const data = await fetchSheetData();
  generateChart(data);
}

main();
