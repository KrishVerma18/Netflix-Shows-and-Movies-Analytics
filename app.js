/**
 * Netflix Content Analytics - Executive Web Application Logic
 * Pure Vanilla JavaScript & Chart.js
 */

document.addEventListener('DOMContentLoaded', async () => {
  // ----------------------------------------------------
  // 1. DATA INITIALIZATION
  // ----------------------------------------------------
  let allData = [];
  if (window.NETFLIX_DATA && Array.isArray(window.NETFLIX_DATA)) {
    allData = window.NETFLIX_DATA;
  } else {
    try {
      const resp = await fetch('web_data.json');
      allData = await resp.json();
    } catch (e) {
      console.error('Failed to load web_data.json:', e);
    }
  }
  console.log(`Loaded ${allData.length} records into analytics engine.`);

  // ----------------------------------------------------
  // 2. DOM ELEMENT REFERENCES
  // ----------------------------------------------------
  // Sidebar navigation
  const navItems = document.querySelectorAll('.nav-item');
  const contentPages = document.querySelectorAll('.content-page');

  // Theme toggle
  const themeSwitch = document.getElementById('themeSwitch');
  const themeLabelText = document.getElementById('themeLabelText');

  // Global filters
  const filterTypeSelect = document.getElementById('filterTypeSelect');
  const filterCountrySelect = document.getElementById('filterCountrySelect');
  const filterGenreSelect = document.getElementById('filterGenreSelect');
  const filterRatingSelect = document.getElementById('filterRatingSelect');
  const filterYearSlider = document.getElementById('filterYearSlider');
  const yearMinVal = document.getElementById('yearMinVal');
  const resetFiltersButton = document.getElementById('resetFiltersButton');
  const filterStatusText = document.getElementById('filterStatusText');

  // KPI elements
  const kpiTotal = document.getElementById('kpiTotal');
  const kpiTotalSub = document.getElementById('kpiTotalSub');
  const kpiMovies = document.getElementById('kpiMovies');
  const kpiMoviesSub = document.getElementById('kpiMoviesSub');
  const kpiTVShows = document.getElementById('kpiTVShows');
  const kpiTVSub = document.getElementById('kpiTVSub');
  const kpiCountries = document.getElementById('kpiCountries');
  const kpiGenres = document.getElementById('kpiGenres');
  const kpiRuntime = document.getElementById('kpiRuntime');

  // Donut stats in Overview
  const donutMoviePct = document.getElementById('donutMoviePct');
  const donutMovieCount = document.getElementById('donutMovieCount');
  const donutTVPct = document.getElementById('donutTVPct');
  const donutTVCount = document.getElementById('donutTVCount');
  const ratingLegendList = document.getElementById('ratingLegendList');

  // Catalog Explorer
  const catalogSearchInput = document.getElementById('catalogSearchInput');
  const catalogTableBody = document.getElementById('catalogTableBody');
  const paginationStatusText = document.getElementById('paginationStatusText');
  const btnPagePrev = document.getElementById('btnPagePrev');
  const btnPageNext = document.getElementById('btnPageNext');
  const pageIndexDisplay = document.getElementById('pageIndexDisplay');

  // Title modal
  const titleDetailModal = document.getElementById('titleDetailModal');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalTypeTag = document.getElementById('modalTypeTag');
  const modalTitleText = document.getElementById('modalTitleText');
  const modalRelease = document.getElementById('modalRelease');
  const modalAdded = document.getElementById('modalAdded');
  const modalRatingBadge = document.getElementById('modalRatingBadge');
  const modalDurationVal = document.getElementById('modalDurationVal');
  const modalCountryVal = document.getElementById('modalCountryVal');
  const modalGenreVal = document.getElementById('modalGenreVal');
  const modalDirectorVal = document.getElementById('modalDirectorVal');
  const modalCastVal = document.getElementById('modalCastVal');
  const modalSynopsisVal = document.getElementById('modalSynopsisVal');

  // Geography page
  const geoLeaderboardBody = document.getElementById('geoLeaderboardBody');

  // Methodology
  const sqlAccordionContainer = document.getElementById('sqlAccordionContainer');
  const btnExploreTrends = document.getElementById('btnExploreTrends');

  // State
  let filteredData = [...allData];
  let catalogPage = 1;
  const catalogRowsPerPage = 25;
  let currentTheme = localStorage.getItem('netflix_analytics_theme') || 'dark';

  // Chart instances
  let chartTypeDonut = null;
  let chartTimeline = null;
  let chartCountries = null;
  let chartGenres = null;
  let chartRatings = null;
  let chartRuntime = null;
  let chartSeasons = null;
  let chartTrendsAdditions = null;
  let chartTrendsDecades = null;
  let chartGeoStacked = null;

  // ----------------------------------------------------
  // 3. THEME TOGGLE (DARK / LIGHT)
  // ----------------------------------------------------
  function applyTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('netflix_analytics_theme', theme);
    if (theme === 'light') {
      themeSwitch.checked = true;
      themeLabelText.textContent = 'Dark Mode';
    } else {
      themeSwitch.checked = false;
      themeLabelText.textContent = 'Light Mode';
    }
    // Update Chart.js default colors
    Chart.defaults.color = theme === 'light' ? '#4B5563' : '#9CA3AF';
    updateAllCharts();
  }

  themeSwitch.addEventListener('change', () => {
    applyTheme(themeSwitch.checked ? 'light' : 'dark');
  });
  applyTheme(currentTheme);

  // ----------------------------------------------------
  // 4. SIDEBAR NAVIGATION
  // ----------------------------------------------------
  function navigateToPage(pageKey) {
    navItems.forEach(item => {
      item.classList.toggle('active', item.dataset.page === pageKey);
    });
    contentPages.forEach(page => {
      page.classList.toggle('active', page.id === `page-${pageKey}`);
    });

    if (pageKey === 'trends') renderTrendsCharts();
    if (pageKey === 'geography') renderGeographyView();
    if (pageKey === 'methodology') renderSqlAccordions();
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navigateToPage(item.dataset.page);
    });
  });

  if (btnExploreTrends) {
    btnExploreTrends.addEventListener('click', () => {
      navigateToPage('trends');
    });
  }

  // ----------------------------------------------------
  // 5. POPULATE FILTER DROPDOWNS
  // ----------------------------------------------------
  function populateFilterDropdowns() {
    // Countries
    const countries = [...new Set(allData.map(d => d.primary_country).filter(c => c && c !== 'Unknown'))].sort();
    countries.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = c;
      filterCountrySelect.appendChild(opt);
    });

    // Genres
    const genres = [...new Set(allData.map(d => d.primary_genre).filter(Boolean))].sort();
    genres.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g;
      opt.textContent = g;
      filterGenreSelect.appendChild(opt);
    });

    // Ratings
    const ratings = [...new Set(allData.map(d => d.rating).filter(Boolean))].sort();
    ratings.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r;
      opt.textContent = r;
      filterRatingSelect.appendChild(opt);
    });
  }
  populateFilterDropdowns();

  // ----------------------------------------------------
  // 6. FILTER ENGINE & REACTIVITY
  // ----------------------------------------------------
  function applyGlobalFilters() {
    const selectedType = filterTypeSelect.value;
    const selectedCountry = filterCountrySelect.value;
    const selectedGenre = filterGenreSelect.value;
    const selectedRating = filterRatingSelect.value;
    const minYear = parseInt(filterYearSlider.value, 10);

    filteredData = allData.filter(d => {
      if (selectedType !== 'ALL' && d.type !== selectedType) return false;
      if (selectedCountry !== 'ALL' && d.primary_country !== selectedCountry) return false;
      if (selectedGenre !== 'ALL' && d.primary_genre !== selectedGenre) return false;
      if (selectedRating !== 'ALL' && d.rating !== selectedRating) return false;
      if (d.release_year < minYear) return false;
      return true;
    });

    filterStatusText.textContent = `Showing ${filteredData.length.toLocaleString()} titles`;
    catalogPage = 1;

    updateKPIs();
    updateAllCharts();
    renderCatalogTable();
    if (document.getElementById('page-geography').classList.contains('active')) {
      renderGeographyView();
    }
  }

  filterTypeSelect.addEventListener('change', applyGlobalFilters);
  filterCountrySelect.addEventListener('change', applyGlobalFilters);
  filterGenreSelect.addEventListener('change', applyGlobalFilters);
  filterRatingSelect.addEventListener('change', applyGlobalFilters);
  filterYearSlider.addEventListener('input', (e) => {
    yearMinVal.textContent = e.target.value;
    applyGlobalFilters();
  });

  resetFiltersButton.addEventListener('click', () => {
    filterTypeSelect.value = 'ALL';
    filterCountrySelect.value = 'ALL';
    filterGenreSelect.value = 'ALL';
    filterRatingSelect.value = 'ALL';
    filterYearSlider.value = 1925;
    yearMinVal.textContent = '1925';
    catalogSearchInput.value = '';
    applyGlobalFilters();
  });

  // ----------------------------------------------------
  // 7. UPDATE EXECUTIVE KPI SCORECARD
  // ----------------------------------------------------
  function updateKPIs() {
    const total = filteredData.length;
    const movies = filteredData.filter(d => d.type === 'Movie').length;
    const tvShows = filteredData.filter(d => d.type === 'TV Show').length;

    kpiTotal.textContent = total.toLocaleString();
    kpiTotalSub.textContent = total === allData.length ? '100% of Catalog' : `${((total / allData.length) * 100).toFixed(1)}% of Catalog`;

    kpiMovies.textContent = movies.toLocaleString();
    const moviePct = total > 0 ? ((movies / total) * 100).toFixed(1) : '0.0';
    kpiMoviesSub.textContent = `${moviePct}% of Catalog`;

    kpiTVShows.textContent = tvShows.toLocaleString();
    const tvPct = total > 0 ? ((tvShows / total) * 100).toFixed(1) : '0.0';
    kpiTVSub.textContent = `${tvPct}% of Catalog`;

    const uniqueCountries = new Set(filteredData.map(d => d.primary_country).filter(c => c && c !== 'Unknown')).size;
    kpiCountries.textContent = uniqueCountries;

    const uniqueGenres = new Set(filteredData.map(d => d.primary_genre).filter(Boolean)).size;
    kpiGenres.textContent = uniqueGenres;

    const movieMins = filteredData
      .filter(d => d.type === 'Movie' && d.duration_minutes)
      .map(d => d.duration_minutes);

    if (movieMins.length > 0) {
      const avg = (movieMins.reduce((a, b) => a + b, 0) / movieMins.length).toFixed(1);
      kpiRuntime.textContent = `${avg} min`;
    } else {
      kpiRuntime.textContent = 'N/A';
    }

    // Donut stat callouts
    donutMoviePct.textContent = `${moviePct}%`;
    donutMovieCount.textContent = movies.toLocaleString();
    donutTVPct.textContent = `${tvPct}%`;
    donutTVCount.textContent = tvShows.toLocaleString();
  }

  // ----------------------------------------------------
  // 8. RENDER CHARTS
  // ----------------------------------------------------
  function updateAllCharts() {
    renderOverviewTypeDonut();
    renderOverviewTimeline();
    renderOverviewCountries();
    renderOverviewGenres();
    renderOverviewRatings();
    renderOverviewRuntime();
    renderOverviewSeasons();
  }

  // Chart 1: Movies vs TV Shows Donut
  function renderOverviewTypeDonut() {
    const movies = filteredData.filter(d => d.type === 'Movie').length;
    const tvShows = filteredData.filter(d => d.type === 'TV Show').length;

    const ctx = document.getElementById('chartOverviewType').getContext('2d');
    if (chartTypeDonut) chartTypeDonut.destroy();

    const isDark = currentTheme === 'dark';
    chartTypeDonut = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Movies', 'TV Shows'],
        datasets: [{
          data: [movies, tvShows],
          backgroundColor: ['#E50914', '#3B82F6'],
          borderColor: isDark ? '#15161E' : '#FFFFFF',
          borderWidth: 3,
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '76%',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (c) => ` ${c.label}: ${c.raw.toLocaleString()} (${((c.raw / (movies + tvShows || 1)) * 100).toFixed(1)}%)`
            }
          }
        }
      }
    });
  }

  // Chart 2: Timeline Line Chart
  function renderOverviewTimeline() {
    const years = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021];
    const movies = years.map(y => filteredData.filter(d => d.year_added === y && d.type === 'Movie').length);
    const tv = years.map(y => filteredData.filter(d => d.year_added === y && d.type === 'TV Show').length);

    const ctx = document.getElementById('chartOverviewTimeline').getContext('2d');
    if (chartTimeline) chartTimeline.destroy();

    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

    chartTimeline = new Chart(ctx, {
      type: 'line',
      data: {
        labels: years,
        datasets: [
          {
            label: 'Movies',
            data: movies,
            borderColor: '#E50914',
            backgroundColor: '#E50914',
            borderWidth: 2,
            pointRadius: 3.5,
            pointBackgroundColor: '#E50914',
            tension: 0.3
          },
          {
            label: 'TV Shows',
            data: tv,
            borderColor: '#3B82F6',
            backgroundColor: '#3B82F6',
            borderWidth: 2,
            pointRadius: 3.5,
            pointBackgroundColor: '#3B82F6',
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: {
            grid: { color: gridColor },
            ticks: { callback: v => v >= 1000 ? `${(v/1000).toFixed(1)}K` : v }
          }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  // Chart 3: Top 10 Countries Horizontal Bar
  function renderOverviewCountries() {
    const cMap = {};
    filteredData.forEach(d => {
      const c = d.primary_country;
      if (c && c !== 'Unknown') {
        cMap[c] = (cMap[c] || 0) + 1;
      }
    });

    const top10 = Object.entries(cMap).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const labels = top10.map(i => i[0]);
    const counts = top10.map(i => i[1]);

    const ctx = document.getElementById('chartOverviewCountries').getContext('2d');
    if (chartCountries) chartCountries.destroy();

    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

    chartCountries = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: counts,
          backgroundColor: '#E50914',
          borderRadius: 2
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: { color: gridColor },
            ticks: { callback: v => v >= 1000 ? `${(v/1000).toFixed(0)}K` : v }
          },
          y: { grid: { display: false } }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: c => ` Titles: ${c.raw.toLocaleString()}`
            }
          }
        }
      }
    });
  }

  // Chart 4: Top 10 Genres Horizontal Bar
  function renderOverviewGenres() {
    const gMap = {};
    filteredData.forEach(d => {
      const g = d.primary_genre;
      if (g) gMap[g] = (gMap[g] || 0) + 1;
    });

    const top10 = Object.entries(gMap).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const labels = top10.map(i => i[0]);
    const counts = top10.map(i => i[1]);

    const ctx = document.getElementById('chartOverviewGenres').getContext('2d');
    if (chartGenres) chartGenres.destroy();

    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

    chartGenres = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: counts,
          backgroundColor: '#E50914',
          borderRadius: 2
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: { color: gridColor },
            ticks: { callback: v => v >= 1000 ? `${(v/1000).toFixed(0)}K` : v }
          },
          y: { grid: { display: false } }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: c => ` Titles: ${c.raw.toLocaleString()}`
            }
          }
        }
      }
    });
  }

  // Chart 5: Content Rating Distribution Donut + Legend List
  function renderOverviewRatings() {
    const rMap = {};
    filteredData.forEach(d => {
      const r = d.rating;
      if (r) rMap[r] = (rMap[r] || 0) + 1;
    });

    const primaryRatings = ['TV-MA', 'TV-14', 'R', 'PG-13', 'TV-PG'];
    let primaryData = primaryRatings.map(r => rMap[r] || 0);
    let others = 0;
    Object.entries(rMap).forEach(([k, v]) => {
      if (!primaryRatings.includes(k)) others += v;
    });

    const labels = [...primaryRatings, 'Others'];
    const data = [...primaryData, others];
    const colors = ['#E50914', '#3B82F6', '#F59E0B', '#10B981', '#6B7280', '#93C5FD'];

    const ctx = document.getElementById('chartOverviewRatings').getContext('2d');
    if (chartRatings) chartRatings.destroy();

    const isDark = currentTheme === 'dark';
    chartRatings = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors,
          borderColor: isDark ? '#15161E' : '#FFFFFF',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: { legend: { display: false } }
      }
    });

    // Populate the legend list on right
    const total = data.reduce((a, b) => a + b, 0) || 1;
    ratingLegendList.innerHTML = labels.map((lbl, idx) => {
      const val = data[idx];
      const pct = ((val / total) * 100).toFixed(1);
      return `
        <div class="rating-legend-row">
          <span><span class="rating-legend-dot" style="background-color: ${colors[idx]}"></span>${lbl}</span>
          <span>${val.toLocaleString()} (${pct}%)</span>
        </div>
      `;
    }).join('');
  }

  // Chart 6: Movie Runtime Distribution (Histogram)
  function renderOverviewRuntime() {
    const buckets = {
      '0-30': 0,
      '30-60': 0,
      '60-90': 0,
      '90-120': 0,
      '120-150': 0,
      '150-180': 0,
      '>180': 0
    };

    filteredData.filter(d => d.type === 'Movie' && d.duration_minutes).forEach(d => {
      const m = d.duration_minutes;
      if (m <= 30) buckets['0-30']++;
      else if (m <= 60) buckets['30-60']++;
      else if (m <= 90) buckets['60-90']++;
      else if (m <= 120) buckets['90-120']++;
      else if (m <= 150) buckets['120-150']++;
      else if (m <= 180) buckets['150-180']++;
      else buckets['>180']++;
    });

    const ctx = document.getElementById('chartOverviewRuntime').getContext('2d');
    if (chartRuntime) chartRuntime.destroy();

    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

    chartRuntime = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(buckets),
        datasets: [{
          data: Object.values(buckets),
          backgroundColor: '#E50914',
          borderRadius: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: {
            grid: { color: gridColor },
            ticks: { callback: v => v >= 1000 ? `${(v/1000).toFixed(1)}K` : v }
          }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  // Chart 7: TV Shows by Number of Seasons
  function renderOverviewSeasons() {
    const sMap = { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6+': 0 };

    filteredData.filter(d => d.type === 'TV Show' && d.duration_seasons).forEach(d => {
      const s = d.duration_seasons;
      if (s === 1) sMap['1']++;
      else if (s === 2) sMap['2']++;
      else if (s === 3) sMap['3']++;
      else if (s === 4) sMap['4']++;
      else if (s === 5) sMap['5']++;
      else sMap['6+']++;
    });

    const ctx = document.getElementById('chartOverviewSeasons').getContext('2d');
    if (chartSeasons) chartSeasons.destroy();

    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

    chartSeasons = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(sMap),
        datasets: [{
          data: Object.values(sMap),
          backgroundColor: '#3B82F6',
          borderRadius: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: {
            grid: { color: gridColor },
            ticks: { callback: v => v >= 1000 ? `${(v/1000).toFixed(1)}K` : v }
          }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  // ----------------------------------------------------
  // 9. TRENDS PAGE CHARTS
  // ----------------------------------------------------
  function renderTrendsCharts() {
    // 1. Additions by year (2008 to 2021)
    const allYears = Array.from({ length: 14 }, (_, i) => 2008 + i);
    const additionsByYear = allYears.map(y => filteredData.filter(d => d.year_added === y).length);

    const ctx1 = document.getElementById('chartTrendsAdditions').getContext('2d');
    if (chartTrendsAdditions) chartTrendsAdditions.destroy();

    chartTrendsAdditions = new Chart(ctx1, {
      type: 'bar',
      data: {
        labels: allYears,
        datasets: [{
          label: 'Titles Ingested',
          data: additionsByYear,
          backgroundColor: '#E50914',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: currentTheme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' } }
        },
        plugins: { legend: { display: false } }
      }
    });

    // 2. Releases by decade
    const decadeMap = {};
    filteredData.forEach(d => {
      const dec = Math.floor(d.release_year / 10) * 10;
      decadeMap[dec] = (decadeMap[dec] || 0) + 1;
    });

    const sortedDecades = Object.entries(decadeMap)
      .filter(([dec]) => parseInt(dec) >= 1950)
      .sort((a, b) => a[0] - b[0]);

    const ctx2 = document.getElementById('chartTrendsDecades').getContext('2d');
    if (chartTrendsDecades) chartTrendsDecades.destroy();

    chartTrendsDecades = new Chart(ctx2, {
      type: 'line',
      data: {
        labels: sortedDecades.map(d => `${d[0]}s`),
        datasets: [{
          label: 'Titles Released',
          data: sortedDecades.map(d => d[1]),
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.15)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: currentTheme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  // ----------------------------------------------------
  // 10. GEOGRAPHY VIEW
  // ----------------------------------------------------
  function renderGeographyView() {
    const cMap = {};
    const movieMap = {};
    const tvMap = {};

    filteredData.forEach(d => {
      const c = d.primary_country;
      if (c && c !== 'Unknown') {
        cMap[c] = (cMap[c] || 0) + 1;
        if (d.type === 'Movie') movieMap[c] = (movieMap[c] || 0) + 1;
        else tvMap[c] = (tvMap[c] || 0) + 1;
      }
    });

    const sorted = Object.entries(cMap).sort((a, b) => b[1] - a[1]);
    const top12 = sorted.slice(0, 12);

    // Render Stacked Bar
    const ctx = document.getElementById('chartGeoStacked').getContext('2d');
    if (chartGeoStacked) chartGeoStacked.destroy();

    chartGeoStacked = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: top12.map(i => i[0]),
        datasets: [
          { label: 'Movies', data: top12.map(i => movieMap[i[0]] || 0), backgroundColor: '#E50914' },
          { label: 'TV Shows', data: top12.map(i => tvMap[i[0]] || 0), backgroundColor: '#3B82F6' }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true, grid: { color: currentTheme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' } },
          y: { stacked: true, grid: { display: false } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, color: currentTheme === 'dark' ? '#E5E7EB' : '#111827' } }
        }
      }
    });

    // Render Leaderboard Table
    geoLeaderboardBody.innerHTML = sorted.slice(0, 20).map(([cntry, total], idx) => {
      const m = movieMap[cntry] || 0;
      const tv = tvMap[cntry] || 0;
      const mPct = ((m / total) * 100).toFixed(1);
      return `
        <tr>
          <td><strong>#${idx + 1}</strong></td>
          <td>${cntry}</td>
          <td>${m.toLocaleString()}</td>
          <td>${tv.toLocaleString()}</td>
          <td><strong>${total.toLocaleString()}</strong></td>
          <td>${mPct}%</td>
        </tr>
      `;
    }).join('');
  }

  // ----------------------------------------------------
  // 11. CATALOG EXPLORER TABLE & SEARCH
  // ----------------------------------------------------
  function renderCatalogTable() {
    const term = catalogSearchInput.value.trim().toLowerCase();
    let list = filteredData;

    if (term) {
      list = filteredData.filter(d => 
        d.title.toLowerCase().includes(term) ||
        d.director.toLowerCase().includes(term) ||
        d.cast.toLowerCase().includes(term) ||
        d.country.toLowerCase().includes(term) ||
        d.primary_genre.toLowerCase().includes(term)
      );
    }

    const total = list.length;
    const totalPages = Math.ceil(total / catalogRowsPerPage) || 1;
    if (catalogPage > totalPages) catalogPage = totalPages;

    const start = (catalogPage - 1) * catalogRowsPerPage;
    const slice = list.slice(start, start + catalogRowsPerPage);

    catalogTableBody.innerHTML = slice.map(d => {
      const badgeCls = d.type === 'Movie' ? 'badge-movie' : 'badge-tv';
      return `
        <tr>
          <td><strong>${d.title}</strong></td>
          <td><span class="badge ${badgeCls}">${d.type}</span></td>
          <td>${d.release_year}</td>
          <td>${d.date_added || '-'}</td>
          <td>${d.primary_country || 'Unknown'}</td>
          <td><span class="badge" style="background:#222; border:1px solid #333; color:#DDD">${d.rating}</span></td>
          <td>${d.duration}</td>
          <td>${d.primary_genre}</td>
          <td><button class="btn-inspect" data-id="${d.id}">Inspect</button></td>
        </tr>
      `;
    }).join('');

    paginationStatusText.textContent = `Showing ${total > 0 ? start + 1 : 0} - ${Math.min(start + catalogRowsPerPage, total)} of ${total.toLocaleString()} titles`;
    pageIndexDisplay.textContent = `Page ${catalogPage} of ${totalPages}`;
    btnPagePrev.disabled = catalogPage <= 1;
    btnPageNext.disabled = catalogPage >= totalPages;

    document.querySelectorAll('.btn-inspect').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const item = allData.find(d => d.id === e.target.dataset.id);
        if (item) showTitleModal(item);
      });
    });
  }

  catalogSearchInput.addEventListener('input', () => {
    catalogPage = 1;
    renderCatalogTable();
  });

  btnPagePrev.addEventListener('click', () => {
    if (catalogPage > 1) { catalogPage--; renderCatalogTable(); }
  });

  btnPageNext.addEventListener('click', () => {
    catalogPage++;
    renderCatalogTable();
  });

  // Modal
  function showTitleModal(item) {
    modalTitleText.textContent = item.title;
    modalTypeTag.textContent = item.type;
    modalTypeTag.className = `badge ${item.type === 'Movie' ? 'badge-movie' : 'badge-tv'}`;
    modalRelease.textContent = item.release_year;
    modalAdded.textContent = item.date_added || 'Not specified';
    modalRatingBadge.textContent = `${item.rating} (${item.rating_category})`;
    modalDurationVal.textContent = item.duration;
    modalCountryVal.textContent = item.country;
    modalGenreVal.textContent = item.listed_in;
    modalDirectorVal.textContent = item.director;
    modalCastVal.textContent = item.cast;
    modalSynopsisVal.textContent = item.description;

    titleDetailModal.classList.add('show');
  }

  modalCloseBtn.addEventListener('click', () => titleDetailModal.classList.remove('show'));
  window.addEventListener('click', (e) => {
    if (e.target === titleDetailModal) titleDetailModal.classList.remove('show');
  });

  // ----------------------------------------------------
  // 12. METHODOLOGY: COLLAPSIBLE SQL ACCORDIONS
  // ----------------------------------------------------
  const sqlAccordionData = [
    {
      q: "Question 01: Total Titles Available in Catalog",
      desc: "Establishes total distinct assets in the Netflix catalog.",
      sql: "SELECT COUNT(*) AS total_catalog_titles FROM netflix_titles;",
      output: "total_catalog_titles: 8,807"
    },
    {
      q: "Question 02: Catalog Composition (Movies vs TV Shows)",
      desc: "Calculates the exact volume and percentage split between feature films and television series.",
      sql: "SELECT \n  type,\n  COUNT(*) AS title_count,\n  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS percentage_share\nFROM netflix_titles\nGROUP BY type\nORDER BY title_count DESC;",
      output: "Movie: 6,131 (69.61%) | TV Show: 2,676 (30.39%)"
    },
    {
      q: "Question 03: Content Additions Trajectory Over Time",
      desc: "Tracks multi-year platform ingestion volume by calendar year.",
      sql: "SELECT \n  year_added,\n  COUNT(*) AS additions_count,\n  SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies,\n  SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows\nFROM netflix_titles\nWHERE year_added IS NOT NULL\nGROUP BY year_added\nORDER BY year_added ASC;",
      output: "Peak year: 2019 with 2,016 additions (1,424 movies, 592 TV shows)"
    },
    {
      q: "Question 04: Top Content Producing Countries",
      desc: "Ranks countries by total titles produced, including co-productions.",
      sql: "SELECT \n  c.country,\n  COUNT(DISTINCT c.show_id) AS total_titles,\n  SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS movies,\n  SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows\nFROM netflix_countries c\nJOIN netflix_titles t ON c.show_id = t.show_id\nWHERE c.country <> 'Unknown'\nGROUP BY c.country\nORDER BY total_titles DESC\nLIMIT 5;",
      output: "United States (3,690) | India (1,046) | United Kingdom (806) | Canada (445) | France (393)"
    },
    {
      q: "Question 05: Movie-to-TV Show Ratio by Country",
      desc: "Measures regional cultural preference between cinema and serialized television.",
      sql: "SELECT \n  c.country,\n  SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS movies,\n  SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows,\n  ROUND(CAST(SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS FLOAT) / \n        NULLIF(SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END), 0), 2) AS movie_to_tv_ratio\nFROM netflix_countries c\nJOIN netflix_titles t ON c.show_id = t.show_id\nWHERE c.country <> 'Unknown'\nGROUP BY c.country\nHAVING COUNT(DISTINCT c.show_id) >= 30\nORDER BY movie_to_tv_ratio DESC\nLIMIT 5;",
      output: "India (11.45:1) | Egypt (6.80:1) | Nigeria (10.44:1) vs South Korea (0.33:1)"
    },
    {
      q: "Question 06: TV Series Longevity by Season Count",
      desc: "Measures franchise continuation and series renewal rates.",
      sql: "SELECT \n  duration_seasons AS seasons,\n  COUNT(*) AS show_count,\n  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE type = 'TV Show'), 2) AS pct_share\nFROM netflix_titles\nWHERE type = 'TV Show' AND duration_seasons IS NOT NULL\nGROUP BY duration_seasons\nORDER BY seasons ASC;",
      output: "1 Season: 1,793 shows (67.0%) | 2 Seasons: 425 shows (15.9%) | 3+ Seasons: 458 shows (17.1%)"
    },
    {
      q: "Question 07: Cumulative Catalog Growth & Year-over-Year Velocity",
      desc: "Advanced multi-level CTE with Window SUM() and Window LAG() to compute annual growth rates.",
      sql: "WITH annual_additions AS (\n  SELECT year_added, COUNT(*) AS additions_count\n  FROM netflix_titles WHERE year_added IS NOT NULL GROUP BY year_added\n)\nSELECT \n  year_added, additions_count,\n  SUM(additions_count) OVER (ORDER BY year_added) AS cumulative_size,\n  ROUND(((additions_count - LAG(additions_count, 1) OVER (ORDER BY year_added)) * 100.0) / \n        NULLIF(LAG(additions_count, 1) OVER (ORDER BY year_added), 0), 2) AS yoy_growth_pct\nFROM annual_additions ORDER BY year_added ASC;",
      output: "Cumulative size reaches 8,797 titles by 2021 (excluding 10 titles with missing addition dates)"
    }
  ];

  function renderSqlAccordions() {
    if (sqlAccordionContainer.children.length > 0) return; // already rendered
    sqlAccordionContainer.innerHTML = sqlAccordionData.map((item, idx) => `
      <div class="accordion-item">
        <div class="accordion-header" data-idx="${idx}">
          <span class="accordion-title">${item.q}</span>
          <button class="btn-toggle-query">[View Query]</button>
        </div>
        <div class="accordion-body" id="acc-body-${idx}">
          <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 6px;">${item.desc}</p>
          <pre><code>${item.sql}</code></pre>
          <div style="margin-top: 8px; font-size: 11.5px; color: #34D399;"><strong>Verified Output:</strong> ${item.output}</div>
        </div>
      </div>
    `).join('');

    document.querySelectorAll('.accordion-header').forEach(hdr => {
      hdr.addEventListener('click', () => {
        const idx = hdr.dataset.idx;
        const body = document.getElementById(`acc-body-${idx}`);
        const btn = hdr.querySelector('.btn-toggle-query');
        const isOpen = body.classList.contains('open');
        
        body.classList.toggle('open', !isOpen);
        btn.textContent = isOpen ? '[View Query]' : '[Hide Query]';
      });
    });
  }

  // ----------------------------------------------------
  // 13. INITIAL RUN
  // ----------------------------------------------------
  applyGlobalFilters();
  renderCatalogTable();
});
