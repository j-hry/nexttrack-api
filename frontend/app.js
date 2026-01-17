// --- DOM REFERENCES ---
const trackRows = document.getElementById("track-rows");
const addRowBtn = document.getElementById("add-row-btn");
const recommendBtn = document.getElementById("recommend-btn");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");
const resultsSection = document.getElementById("results-section");
const diversitySlider = document.getElementById("diversity-slider");
const diversityValue = document.getElementById("diversity-value");

const MIN_ROWS = 3;
const MAX_ROWS = 10;

// --- TRACK ROW MANAGEMENT ---

/**
 * Creates a new track row element with artist input, track input, and remove button.
 * @returns {HTMLDivElement} The constructed track row element.
 */
function createTrackRow() {
  const row = document.createElement("div");
  row.className = "track-row";
  row.innerHTML = `
        <input type="text" class="artist-input" placeholder="Artist" required>
        <input type="text" class="track-input" placeholder="Track" required>
        <button type="button" class="remove-row-btn">✕</button>
    `;
  return row;
}

/**
 * Updates the enabled/disabled state of all remove buttons and the add button
 * based on the current number of track rows. Remove buttons are disabled at
 * MIN_ROWS; the add button is disabled at MAX_ROWS.
 */
function updateRowButtons() {
  const rows = trackRows.querySelectorAll(".track-row");
  const removeBtns = trackRows.querySelectorAll(".remove-row-btn");

  removeBtns.forEach((btn) => {
    btn.disabled = rows.length <= MIN_ROWS;
  });

  addRowBtn.disabled = rows.length >= MAX_ROWS;
}

addRowBtn.addEventListener("click", () => {
  const rows = trackRows.querySelectorAll(".track-row");
  if (rows.length >= MAX_ROWS) return;

  trackRows.appendChild(createTrackRow());
  updateRowButtons();
});

trackRows.addEventListener("click", (e) => {
  if (!e.target.classList.contains("remove-row-btn")) return;
  const rows = trackRows.querySelectorAll(".track-row");
  if (rows.length <= MIN_ROWS) return;

  e.target.closest(".track-row").remove();
  updateRowButtons();
});

// --- DIVERSITY SLIDER ---

diversitySlider.addEventListener("input", () => {
  diversityValue.textContent = diversitySlider.value;
});

// --- BUILD REQUEST ---

/**
 * Collects all form values and constructs the JSON request body
 * matching the POST /api/v1/recommend contract.
 * @returns {Object} Request body with listening_history, diversity, popularity,
 *                   tags, tag_match_type, and exclude_same_artist.
 */
function buildRequestBody() {
  const rows = trackRows.querySelectorAll(".track-row");
  const listeningHistory = [];

  rows.forEach((row) => {
    const artist = row.querySelector(".artist-input").value.trim();
    const track = row.querySelector(".track-input").value.trim();
    if (artist && track) {
      listeningHistory.push({ artist, track });
    }
  });

  const tags = [];
  document.querySelectorAll(".tag-input").forEach((input) => {
    const val = input.value.trim();
    if (val) tags.push(val);
  });

  const tagMatchType = document.querySelector(
    'input[name="tag-match-type"]:checked',
  ).value;

  return {
    listening_history: listeningHistory,
    diversity: parseFloat(diversitySlider.value),
    popularity: document.getElementById("popularity-select").value,
    tags: tags,
    tag_match_type: tagMatchType,
    exclude_same_artist: document.getElementById("exclude-same-artist").checked,
  };
}

// --- VALIDATION ---

/**
 * Validates the request body before submission.
 * @param {Object} body - The request body from buildRequestBody().
 * @returns {boolean} True if valid, false otherwise.
 */
function validate(body) {
  if (body.listening_history.length < MIN_ROWS) {
    alert(`Please enter at least ${MIN_ROWS} tracks.`);
    return false;
  }
  return true;
}

// --- LOADING INDICATOR ---

/**
 * Shows the loading indicator with contextual text. Track-level tag matching
 * displays a slower-loading message since it requires ~11s for uncached lookups.
 * @param {string} tagMatchType - Either "artist" or "track".
 */
function showLoading(tagMatchType) {
  loading.classList.remove("hidden");
  resultsSection.classList.add("hidden");

  if (tagMatchType === "track") {
    loadingText.textContent =
      "Fetching track-level tags — this may take a moment...";
  } else {
    loadingText.textContent = "Finding your next track...";
  }
}

/**
 * Hides the loading indicator.
 */
function hideLoading() {
  loading.classList.add("hidden");
}

// --- DISPLAY RESULTS ---

/**
 * Populates the results section with the API response data, including
 * the top recommendation card, explanation fields, and top 5 candidate list.
 * @param {Object} data - The parsed JSON response from /api/v1/recommend.
 */
function displayResults(data) {
  const rec = data.recommendation;

  document.getElementById("rec-track").textContent = rec.track;
  document.getElementById("rec-artist").textContent = rec.artist;
  document.getElementById("rec-score").textContent =
    data.confidence_score.toFixed(3);
  document.getElementById("rec-link").href = rec.url;

  const exp = data.explanation;
  document.getElementById("exp-match-reason").textContent =
    exp.match_reason || "";
  document.getElementById("exp-diversity-note").textContent =
    exp.diversity_note || "";
  document.getElementById("exp-popularity-note").textContent =
    exp.popularity_note || "";
  document.getElementById("exp-tag-match").textContent = exp.tag_match || "";

  const list = document.getElementById("top-five-list");
  list.innerHTML = "";

  if (data.top_five) {
    data.top_five.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = `${item.artist} — ${item.track} (${item.score.toFixed(3)})`;
      list.appendChild(li);
    });
  }

  resultsSection.classList.remove("hidden");
}

// --- FETCH RECOMMENDATION ---

/**
 * Handles the full recommendation flow: builds the request body, validates,
 * shows loading state, sends the POST request, and displays results or errors.
 */
async function getRecommendation() {
  const body = buildRequestBody();
  if (!validate(body)) return;

  showLoading(body.tag_match_type);
  recommendBtn.disabled = true;

  try {
    const response = await fetch("/api/v1/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || `Server error: ${response.status}`);
    }

    const data = await response.json();
    displayResults(data);
  } catch (error) {
    alert(error.message);
    console.error("Recommendation error:", error);
  } finally {
    hideLoading();
    recommendBtn.disabled = false;
  }
}

recommendBtn.addEventListener("click", getRecommendation);
