# Top Python Web Frameworks
A list of popular github projects related to Python web framework (ranked by stars automatically)

* ADD access_token.txt into this repository.
* UPDATE **list.txt** (via Pull Request)

## 📈 Current Rankings

| Project Name | Stars | Forks | Open Issues | Last Commit |
| ------------ | ----- | ----- | ----------- | ----------- |
| [fastapi](https://github.com/fastapi/fastapi) | 87556 | 7628 | 317 | 2025-07-21 12:21:22 |
| [django](https://github.com/django/django) | 84318 | 32739 | 356 | 2025-07-22 19:29:14 |
| [flask](https://github.com/pallets/flask) | 70021 | 16505 | 14 | 2025-06-12 20:48:07 |
| [dash](https://github.com/plotly/dash) | 23507 | 2175 | 538 | 2025-07-18 17:18:35 |
| [tornado](https://github.com/tornadoweb/tornado) | 22063 | 5533 | 211 | 2025-07-22 20:43:43 |
| [sanic](https://github.com/sanic-org/sanic) | 18445 | 1575 | 140 | 2025-03-31 21:19:26 |
| [aiohttp](https://github.com/aio-libs/aiohttp) | 15849 | 2107 | 253 | 2025-07-21 16:54:06 |
| [starlette](https://github.com/encode/starlette) | 11267 | 1021 | 44 | 2025-07-20 17:29:09 |
| [falcon](https://github.com/falconry/falcon) | 9692 | 960 | 159 | 2025-07-22 19:31:00 |
| [bottle](https://github.com/bottlepy/bottle) | 8633 | 1485 | 282 | 2025-06-27 10:14:03 |

## 📊 Growth Trends

<div id="chartContainer">
  <div style="margin-bottom: 30px;">
    <canvas id="starsChart" width="800" height="400"></canvas>
  </div>
  <div style="margin-bottom: 30px;">
    <canvas id="forksChart" width="800" height="400"></canvas>
  </div>
  <div style="margin-bottom: 30px;">
    <canvas id="issuesChart" width="800" height="400"></canvas>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
<script>
// Load and display historical data
fetch('./example_framework_stars_history.json')
  .then(response => response.json())
  .then(data => {
    const projects = data.projects;
    const topProjects = Object.keys(projects)
      .filter(name => projects[name].history.length > 0)
      .sort((a, b) => {
        const latestA = projects[a].history[projects[a].history.length - 1];
        const latestB = projects[b].history[projects[b].history.length - 1];
        return latestB.stars - latestA.stars;
      })
      .slice(0, 10);

    // Stars Chart
    const starsCtx = document.getElementById('starsChart').getContext('2d');
    new Chart(starsCtx, {
      type: 'line',
      data: {
        datasets: topProjects.map((projectName, index) => ({
          label: projectName,
          data: projects[projectName].history.map(point => ({
            x: point.timestamp,
            y: point.stars
          })),
          borderColor: `hsl(${index * 36}, 70%, 50%)`,
          backgroundColor: `hsla(${index * 36}, 70%, 50%, 0.1)`,
          tension: 0.1
        }))
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'GitHub Stars Over Time (Top 10)'
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Stars'
            }
          }
        }
      }
    });

    // Forks Chart
    const forksCtx = document.getElementById('forksChart').getContext('2d');
    new Chart(forksCtx, {
      type: 'line',
      data: {
        datasets: topProjects.map((projectName, index) => ({
          label: projectName,
          data: projects[projectName].history.map(point => ({
            x: point.timestamp,
            y: point.forks
          })),
          borderColor: `hsl(${index * 36}, 70%, 50%)`,
          backgroundColor: `hsla(${index * 36}, 70%, 50%, 0.1)`,
          tension: 0.1
        }))
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'GitHub Forks Over Time (Top 10)'
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Forks'
            }
          }
        }
      }
    });

    // Issues Chart
    const issuesCtx = document.getElementById('issuesChart').getContext('2d');
    new Chart(issuesCtx, {
      type: 'line',
      data: {
        datasets: topProjects.map((projectName, index) => ({
          label: projectName,
          data: projects[projectName].history.map(point => ({
            x: point.timestamp,
            y: point.open_issues
          })),
          borderColor: `hsl(${index * 36}, 70%, 50%)`,
          backgroundColor: `hsla(${index * 36}, 70%, 50%, 0.1)`,
          tension: 0.1
        }))
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Open Issues Over Time (Top 10)'
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Open Issues'
            }
          }
        }
      }
    });
  })
  .catch(error => {
    console.error('Error loading chart data:', error);
    document.getElementById('chartContainer').innerHTML = '<p>Charts will be available after data collection.</p>';
  });
</script>

*Last Automatic Update: 2025-07-23T18:30:00*