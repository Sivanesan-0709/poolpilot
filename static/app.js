/**
 * PoolPilot - Frontend Application Logic
 * Vanilla JavaScript (No Build Step Required)
 */

let currentUser = null;
let activeTab = "home";
let map = null;

// Map layers & markers
let driverRouteLayer = null;
let pickupMarker = null;
let dropMarker = null;
let meetingMarker = null;
let walkingLineLayer = null;
let liveCarMarker = null;
let heatmapLayer = null;
let mapPickTarget = null; // 'pickup', 'drop', 'offer-origin', 'offer-dest'

// Live tracking & WebSocket / Polling
let activeWebSocket = null;
let simulationInterval = null;
let pollingInterval = null;
let activeLiveBooking = null;

// Chart.js instances
let chartDemandInstance = null;
let chartCo2Instance = null;

// College & Multimodal state
let currentCollegeFilter = "all";
let currentMultimodalItineraries = [];
let currentPersonalImpact = null;

// -------------------------------------------------------------
// Initialization
// -------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  setupAllAutocompletes();
  checkNightSafetyMode();

  // Initialize with Demo Rider (Rahul Verma - REC Student)
  demoLogin("rider", false);
  loadHomeData();
});

function initMap() {
  const chennaiCenter = [13.04, 80.20]; // Central Chennai
  map = L.map("map", {
    center: chennaiCenter,
    zoom: 11,
    zoomControl: true
  });

  // OpenStreetMap Tile Layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  // Map Click Listener for "Pick on Map" feature
  map.on("click", (e) => {
    if (!mapPickTarget) return;

    const lat = parseFloat(e.latlng.lat.toFixed(5));
    const lng = parseFloat(e.latlng.lng.toFixed(5));

    if (mapPickTarget === "pickup") {
      document.getElementById("find-pickup-input").value = `Pin at (${lat}, ${lng})`;
      document.getElementById("find-pickup-lat").value = lat;
      document.getElementById("find-pickup-lng").value = lng;
      setPickupMarker(lat, lng, "Selected Pickup");
      showToast("Pickup location pinned on map!");
    } else if (mapPickTarget === "drop") {
      document.getElementById("find-drop-input").value = `Pin at (${lat}, ${lng})`;
      document.getElementById("find-drop-lat").value = lat;
      document.getElementById("find-drop-lng").value = lng;
      setDropMarker(lat, lng, "Selected Drop");
      showToast("Drop destination pinned on map!");
    } else if (mapPickTarget === "offer-origin") {
      document.getElementById("offer-origin-input").value = `Pin at (${lat}, ${lng})`;
      document.getElementById("offer-origin-lat").value = lat;
      document.getElementById("offer-origin-lng").value = lng;
      setPickupMarker(lat, lng, "Driver Departure");
      showToast("Departure origin pinned on map!");
    } else if (mapPickTarget === "offer-dest") {
      document.getElementById("offer-dest-input").value = `Pin at (${lat}, ${lng})`;
      document.getElementById("offer-dest-lat").value = lat;
      document.getElementById("offer-dest-lng").value = lng;
      setDropMarker(lat, lng, "Driver Destination");
      showToast("Destination pinned on map!");
    }

    mapPickTarget = null;
  });
}

function switchTab(tabId) {
  activeTab = tabId;
  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-content").forEach(c => {
    c.classList.remove("active");
  });

  const target = document.getElementById(`tab-${tabId}`);
  if (target) {
    target.classList.add("active");
  }

  // Refresh map layout
  setTimeout(() => {
    if (map) map.invalidateSize();
  }, 100);

  if (tabId === "trips") {
    loadMyTrips();
  } else if (tabId === "admin") {
    loadAdminData();
    const monthSelect = document.getElementById("impact-month-select");
    const mVal = monthSelect ? monthSelect.value : "March 2026";
    loadImpactData(mVal);
  } else if (tabId === "home") {
    loadHomeData();
  } else if (tabId === "safety") {
    updateSafetyProfileUI();
    loadTrustedContacts();
  } else if (tabId === "college") {
    loadCollegePools(currentCollegeFilter);
  }
}

function toggleTheme() {
  document.body.classList.toggle("dark-theme");
  const isDark = document.body.classList.contains("dark-theme");
  document.getElementById("theme-toggle-btn").textContent = isDark ? "☀️" : "🌙";
}

// -------------------------------------------------------------
// Demo Login & User Session Management
// -------------------------------------------------------------

async function demoLogin(roleType, showFeedback = true) {
  try {
    const res = await fetch(`/api/auth/demo-login/${roleType}`);
    const data = await res.json();
    if (data.success) {
      currentUser = data.user;
      updateUserUI();
      if (showFeedback) {
        showToast(`Logged in as Demo ${currentUser.name} (${currentUser.role.toUpperCase()})`);
      }
      if (activeTab === "trips") loadMyTrips();
      if (activeTab === "safety") {
        updateSafetyProfileUI();
        loadTrustedContacts();
      }
      if (activeTab === "profile") updateProfileTabUI();
      if (activeTab === "college") loadCollegePools(currentCollegeFilter);
    }
  } catch (err) {
    console.error("Demo login error:", err);
  }
}

function updateUserUI() {
  if (!currentUser) return;

  document.getElementById("header-user-name").textContent = currentUser.name.split(" ")[0];
  document.getElementById("header-avatar").textContent = currentUser.name.charAt(0);
  document.getElementById("header-trust-badge").textContent = `${currentUser.trust_badge} (${currentUser.trust_score})`;
  document.getElementById("header-wallet-balance").textContent = `₹${currentUser.wallet_balance.toFixed(0)}`;

  // Update profile tab values
  updateProfileTabUI();

  // Driver Women-Only toggle check
  const offerWomenToggle = document.getElementById("offer-women-only-container");
  if (offerWomenToggle) {
    if (currentUser.gender !== "female") {
      document.getElementById("offer-women-only").disabled = true;
      offerWomenToggle.title = "Women-only rides are restricted to verified female drivers.";
      offerWomenToggle.style.opacity = "0.5";
    } else {
      document.getElementById("offer-women-only").disabled = false;
      offerWomenToggle.style.opacity = "1.0";
    }
  }
}

function updateProfileTabUI() {
  if (!currentUser) return;
  if (document.getElementById("prof-name")) document.getElementById("prof-name").textContent = currentUser.name;
  if (document.getElementById("prof-phone")) document.getElementById("prof-phone").textContent = currentUser.phone;
  if (document.getElementById("prof-gender")) document.getElementById("prof-gender").textContent = currentUser.gender ? currentUser.gender.toUpperCase() : "OTHER";
  if (document.getElementById("prof-org")) document.getElementById("prof-org").textContent = currentUser.college_company || "Chennai Commuter";
  if (document.getElementById("prof-wallet-amt")) document.getElementById("prof-wallet-amt").textContent = `₹${currentUser.wallet_balance.toFixed(2)}`;
  if (document.getElementById("prof-ref-code")) document.getElementById("prof-ref-code").textContent = currentUser.referral_code || "POOL20";
  if (document.getElementById("profile-role-badge")) document.getElementById("profile-role-badge").textContent = currentUser.role.toUpperCase();
}

// -------------------------------------------------------------
// Autocomplete & Places Search
// -------------------------------------------------------------

function setupAllAutocompletes() {
  setupAutocomplete("find-pickup-input", "pickup-autocomplete-results", "find-pickup-lat", "find-pickup-lng", "pickup");
  setupAutocomplete("find-drop-input", "drop-autocomplete-results", "find-drop-lat", "find-drop-lng", "drop");
  setupAutocomplete("offer-origin-input", "offer-origin-autocomplete", "offer-origin-lat", "offer-origin-lng", "offer-origin");
  setupAutocomplete("offer-dest-input", "offer-dest-autocomplete", "offer-dest-lat", "offer-dest-lng", "offer-dest");
}

function setupAutocomplete(inputId, dropdownId, latId, lngId, targetType) {
  const input = document.getElementById(inputId);
  const dropdown = document.getElementById(dropdownId);
  if (!input || !dropdown) return;

  let debounceTimer;

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const query = input.value.trim();
    if (query.length === 0) {
      dropdown.style.display = "none";
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/places/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        if (data.success && data.places.length > 0) {
          dropdown.innerHTML = "";
          data.places.forEach(place => {
            const item = document.createElement("div");
            item.className = "autocomplete-item";
            item.innerHTML = `
              <strong>${place.name}</strong>
              <span>Zone: ${place.zone || "Chennai"} | ${place.category.toUpperCase()}</span>
            `;
            item.addEventListener("click", () => {
              input.value = place.name;
              document.getElementById(latId).value = place.lat;
              document.getElementById(lngId).value = place.lng;
              dropdown.style.display = "none";

              if (targetType === "pickup" || targetType === "offer-origin") {
                setPickupMarker(place.lat, place.lng, place.name);
              } else {
                setDropMarker(place.lat, place.lng, place.name);
              }
            });
            dropdown.appendChild(item);
          });
          dropdown.style.display = "block";
        } else {
          dropdown.style.display = "none";
        }
      } catch (err) {
        console.error("Autocomplete fetch error:", err);
      }
    }, 200);
  });

  // Close dropdown on outside click
  document.addEventListener("click", (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = "none";
    }
  });
}

function selectLocationFromMap(targetType) {
  mapPickTarget = targetType;
  showToast(`Click anywhere on the map to set ${targetType.replace('-', ' ')} point.`);
}

function useCurrentLocation(targetType) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = parseFloat(pos.coords.latitude.toFixed(5));
        const lng = parseFloat(pos.coords.longitude.toFixed(5));
        if (targetType === "pickup") {
          document.getElementById("find-pickup-input").value = `Current Location (${lat}, ${lng})`;
          document.getElementById("find-pickup-lat").value = lat;
          document.getElementById("find-pickup-lng").value = lng;
          setPickupMarker(lat, lng, "Current Location");
        } else {
          document.getElementById("find-drop-input").value = `Current Location (${lat}, ${lng})`;
          document.getElementById("find-drop-lat").value = lat;
          document.getElementById("find-drop-lng").value = lng;
          setDropMarker(lat, lng, "Current Location");
        }
        showToast("GPS Location acquired successfully!");
      },
      (err) => {
        const defaultLat = 13.0067, defaultLng = 80.2025;
        if (targetType === "pickup") {
          document.getElementById("find-pickup-input").value = "Guindy Kathipara Hub (Fallback)";
          document.getElementById("find-pickup-lat").value = defaultLat;
          document.getElementById("find-pickup-lng").value = defaultLng;
          setPickupMarker(defaultLat, defaultLng, "Guindy Kathipara");
        }
        showToast("Geolocation denied. Using Guindy Central Hub as default.");
      },
      { timeout: 5000 }
    );
  }
}

// -------------------------------------------------------------
// Map Marker & Route Renderers
// -------------------------------------------------------------

function setPickupMarker(lat, lng, label = "Pickup") {
  if (pickupMarker) map.removeLayer(pickupMarker);
  const icon = L.divIcon({
    className: "custom-pin-icon",
    html: `<div style="background:#10B981; color:white; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white; box-shadow:0 2px 6px rgba(0,0,0,0.3);">📍</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 28]
  });
  pickupMarker = L.marker([lat, lng], { icon }).addTo(map).bindPopup(`<b>Pickup:</b> ${label}`).openPopup();
  map.panTo([lat, lng]);
}

function setDropMarker(lat, lng, label = "Drop") {
  if (dropMarker) map.removeLayer(dropMarker);
  const icon = L.divIcon({
    className: "custom-pin-icon",
    html: `<div style="background:#EF4444; color:white; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white; box-shadow:0 2px 6px rgba(0,0,0,0.3);">🏁</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 28]
  });
  dropMarker = L.marker([lat, lng], { icon }).addTo(map).bindPopup(`<b>Drop:</b> ${label}`).openPopup();
}

function renderRouteOnMap(polyline, isOffline = false) {
  if (driverRouteLayer) map.removeLayer(driverRouteLayer);
  if (!polyline || polyline.length === 0) return;

  const color = isOffline ? "#F59E0B" : "#2563EB";
  driverRouteLayer = L.polyline(polyline, {
    color: color,
    weight: 5,
    opacity: 0.85,
    lineJoin: "round"
  }).addTo(map);

  map.fitBounds(driverRouteLayer.getBounds(), { padding: [40, 40] });

  const badge = document.getElementById("routing-status-badge");
  const badgeText = document.getElementById("routing-status-text");
  if (badge && badgeText) {
    if (isOffline) {
      badge.className = "badge-status badge-offline";
      badgeText.textContent = "Offline Routing Mode";
    } else {
      badge.className = "badge-status badge-online";
      badgeText.textContent = "Online OSRM Routing";
    }
  }
}

function renderMeetingPoint(meetingPoint, originalPoint) {
  if (meetingMarker) map.removeLayer(meetingMarker);
  if (walkingLineLayer) map.removeLayer(walkingLineLayer);
  if (!meetingPoint || !meetingPoint.lat) return;

  const icon = L.divIcon({
    className: "meeting-pin-icon",
    html: `<div style="background:#F59E0B; color:white; border-radius:50%; width:24px; height:24px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white; box-shadow:0 2px 6px rgba(0,0,0,0.3);">🚶</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24]
  });
  meetingMarker = L.marker([meetingPoint.lat, meetingPoint.lng], { icon })
    .addTo(map)
    .bindPopup(`<b>Dynamic Meeting Point:</b><br>${meetingPoint.walk_meters}m walk (~${meetingPoint.walk_minutes} min)`);

  if (originalPoint && originalPoint[0]) {
    walkingLineLayer = L.polyline([[originalPoint[0], originalPoint[1]], [meetingPoint.lat, meetingPoint.lng]], {
      color: "#F59E0B",
      dashArray: "6, 6",
      weight: 3,
      opacity: 0.9
    }).addTo(map);
  }
}

// -------------------------------------------------------------
// DYNAMIC SAFETY PREFERENCES & ACCORDION
// -------------------------------------------------------------

function toggleSafetyAccordion() {
  const content = document.getElementById("safety-pref-content");
  const icon = document.getElementById("safety-pref-toggle-icon");
  if (!content) return;

  if (content.style.display === "none") {
    content.style.display = "block";
    if (icon) icon.textContent = "▲ Collapse";
  } else {
    content.style.display = "none";
    if (icon) icon.textContent = "▼ Expand";
  }
}

function updateRatingSliderDisplay(val) {
  const label = document.getElementById("pref-rating-val");
  if (label) label.textContent = `${parseFloat(val).toFixed(1)}★`;
}

function applySafetyRelaxation(filterKey, suggestedVal) {
  if (filterKey === "min_driver_rating") {
    const slider = document.getElementById("pref-min-rating");
    if (slider) {
      slider.value = suggestedVal;
      updateRatingSliderDisplay(suggestedVal);
    }
  } else if (filterKey === "verified_id_only") {
    const chk = document.getElementById("pref-verified-id");
    if (chk) chk.checked = false;
  } else if (filterKey === "same_college_or_company_only") {
    const chk = document.getElementById("pref-same-org");
    if (chk) chk.checked = false;
  } else if (filterKey === "same_gender_only") {
    const chk = document.getElementById("pref-same-gender");
    if (chk) chk.checked = false;
  } else if (filterKey === "zero_complaints_only") {
    const chk = document.getElementById("pref-zero-complaints");
    if (chk) chk.checked = false;
  } else if (filterKey === "has_emergency_contact") {
    const chk = document.getElementById("pref-emergency-contact");
    if (chk) chk.checked = false;
  }

  showToast("Filter relaxed! Searching for matches again...");
  const form = document.getElementById("find-ride-form");
  if (form) {
    handleFindRide(new Event("submit"));
  }
}

// -------------------------------------------------------------
// FIND RIDE (6-FACTOR AI MATCHING ENGINE)
// -------------------------------------------------------------

async function handleFindRide(e) {
  if (e) e.preventDefault();
  const pickupLat = parseFloat(document.getElementById("find-pickup-lat").value);
  const pickupLng = parseFloat(document.getElementById("find-pickup-lng").value);
  const dropLat = parseFloat(document.getElementById("find-drop-lat").value);
  const dropLng = parseFloat(document.getElementById("find-drop-lng").value);

  if (!pickupLat || !dropLat) {
    showToast("Please select valid Pickup and Drop locations from search or map!");
    return;
  }

  const safetyPreferences = {
    verified_id_only: document.getElementById("pref-verified-id") ? document.getElementById("pref-verified-id").checked : true,
    same_college_or_company_only: document.getElementById("pref-same-org") ? document.getElementById("pref-same-org").checked : false,
    same_gender_only: document.getElementById("pref-same-gender") ? document.getElementById("pref-same-gender").checked : false,
    min_driver_rating: document.getElementById("pref-min-rating") ? parseFloat(document.getElementById("pref-min-rating").value) : 4.0,
    zero_complaints_only: document.getElementById("pref-zero-complaints") ? document.getElementById("pref-zero-complaints").checked : false,
    has_emergency_contact: document.getElementById("pref-emergency-contact") ? document.getElementById("pref-emergency-contact").checked : false
  };

  const priorityEl = document.querySelector('input[name="priority_mode"]:checked');

  const payload = {
    rider_id: currentUser ? currentUser.id : 1,
    pickup_name: document.getElementById("find-pickup-input").value,
    pickup_lat: pickupLat,
    pickup_lng: pickupLng,
    drop_name: document.getElementById("find-drop-input").value,
    drop_lat: dropLat,
    drop_lng: dropLng,
    departure_time: document.getElementById("find-dept-time").value,
    seats_needed: parseInt(document.getElementById("find-seats").value),
    max_budget: document.getElementById("find-max-budget").value ? parseFloat(document.getElementById("find-max-budget").value) : null,
    priority_mode: priorityEl ? priorityEl.value : "balanced",
    women_only_filter: document.getElementById("find-women-only") ? document.getElementById("find-women-only").checked : false,
    safety_preferences: safetyPreferences
  };

  const searchBtn = document.getElementById("btn-search-matches");
  searchBtn.innerHTML = "<span>⚡ AI 6-Factor Matching & Safety Filter...</span>";
  searchBtn.disabled = true;

  try {
    const res = await fetch("/api/rides/match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    renderMatchingResults(data, payload);
  } catch (err) {
    console.error("Match request error:", err);
    showToast("Error executing AI matching engine. Please try again.");
  } finally {
    searchBtn.innerHTML = "<span>⚡ Find Matching Rides (6-Factor AI Ranking)</span>";
    searchBtn.disabled = false;
  }
}

function renderMatchingResults(data, searchPayload) {
  const container = document.getElementById("matches-list-container");
  const section = document.getElementById("matching-results-section");
  const countTag = document.getElementById("results-count-tag");
  const summaryBox = document.getElementById("candidate-filtering-summary");
  const relaxContainer = document.getElementById("safety-relaxation-container");

  section.style.display = "block";
  container.innerHTML = "";

  // Render Filtering Summary
  if (summaryBox) {
    if (data.filtering_summary) {
      summaryBox.innerHTML = `<span>ℹ️ <strong>Candidate Filtering:</strong> ${data.filtering_summary}</span>`;
      summaryBox.style.display = "block";
    } else {
      summaryBox.style.display = "none";
    }
  }

  // Check 0 matches scenario
  if (!data.matches || data.matches.length === 0) {
    countTag.className = "badge badge-warning";
    countTag.textContent = "0 Direct Matches";

    // Show single-click relaxation suggestions if available
    if (relaxContainer) {
      if (data.relaxation_suggestions && data.relaxation_suggestions.length > 0) {
        relaxContainer.innerHTML = `
          <div class="card" style="background:#FFFBEB; border:1px solid #FCD34D; padding:12px;">
            <div style="font-weight:700; color:#92400E; font-size:13px; margin-bottom:6px;">
              💡 Single-Click Filter Relaxation Suggestions:
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:8px;">
              ${data.relaxation_suggestions.map(s => `
                <button class="btn btn-sm btn-outline" style="border-color:#D97706; color:#B45309; background:white;" onclick="applySafetyRelaxation('${s.filter_key}', ${s.suggested_value})">
                  🔓 ${s.label} (${s.additional_matches > 0 ? `+${s.additional_matches} matches` : 'expand'})
                </button>
              `).join('')}
            </div>
          </div>
        `;
        relaxContainer.style.display = "block";
      } else {
        relaxContainer.style.display = "none";
      }
    }

    const advice = data.fallback_advice || { tips: ["Widen departure window by 15-30 mins.", "Relax safety filters or rating slider."], transit_alternatives: [] };
    let tipsHtml = advice.tips.map(t => `<li>${t}</li>`).join("");
    let transitHtml = (advice.transit_alternatives || []).map(alt => `
      <div class="card mt-2" style="background:var(--input-bg);">
        <strong>🚇 ${alt.title}</strong>
        <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">${alt.route}</div>
        <div style="font-size:11px; font-weight:bold; color:var(--primary-dark); margin-top:4px;">Fare: ${alt.fare_estimate} | CO₂ Saved: ${alt.co2_saved}</div>
      </div>
    `).join("");

    container.innerHTML = `
      <div class="card" style="border-left: 4px solid var(--warning);">
        <h3>💡 ${advice.title || "No Exact Match"}</h3>
        <p class="text-muted" style="margin-top:4px;">Here are suggestions and multimodal transit options:</p>
        <ul style="margin:8px 0 12px 20px; font-size:12px; line-height:1.5;">${tipsHtml}</ul>
        ${transitHtml ? `<h4 style="margin-top:12px; font-size:13px;">Chennai Multimodal Transit Fallbacks:</h4>${transitHtml}` : ""}
      </div>
    `;
    return;
  }

  // We have matches
  if (relaxContainer) relaxContainer.style.display = "none";
  countTag.className = "badge badge-success";
  countTag.textContent = `${data.matches.length} Top Matches`;

  data.matches.forEach((m, idx) => {
    const ride = m.ride;
    const driver = m.driver;
    const breakdown = m.score_breakdown || {};
    const pricing = m.pricing || {};
    const isRecommended = m.match_score >= 85;

    const matchCard = document.createElement("div");
    matchCard.className = "match-card";
    matchCard.innerHTML = `
      <div class="match-header">
        <div class="driver-info-box">
          <div class="driver-avatar-circle">${driver ? driver.name.charAt(0) : "D"}</div>
          <div>
            <div style="font-weight:700; font-size:14px; display:flex; align-items:center; gap:6px;">
              <span>${driver ? driver.name : "Driver"}</span>
              ${isRecommended ? `<span class="badge badge-gold" style="font-size:10px;">⭐ RECOMMENDED MATCH</span>` : ''}
            </div>
            <div style="font-size:11px; color:var(--text-muted);">
              <span class="badge badge-${driver && driver.trust_badge === 'Gold' ? 'gold' : 'silver'}">${driver ? driver.trust_badge : 'Silver'}</span>
              <span>⭐ ${driver ? driver.avg_rating : 5.0}★ (${driver ? driver.total_rides : 0} trips)</span>
              ${driver && driver.college_company ? `<span>• 🏫 ${driver.college_company}</span>` : ''}
            </div>
            <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">
              🚘 ${ride.vehicle || "Car"} • Departs <strong>${ride.departure_time && ride.departure_time.includes('T') ? ride.departure_time.split('T')[1] : ride.departure_time}</strong>
            </div>
          </div>
        </div>

        <div class="match-score-pill">
          <div class="score-number">${m.match_score}%</div>
          <div class="score-sub">AI MATCH SCORE</div>
        </div>
      </div>

      <!-- Plain English Match Reasons -->
      <div class="match-reasons-box">
        ${(m.match_reasons || []).map(r => `<div class="reason-bullet"><span>✓</span> <span>${r}</span></div>`).join("")}
      </div>

      <!-- Explainable AI 6-Bar Breakdown -->
      <div class="ai-breakdown-panel">
        <div class="ai-breakdown-title">WHY THIS MATCH? (6-FACTOR EXPLAINABLE AI BREAKDOWN)</div>
        
        <div class="factor-bar-row">
          <span class="factor-name">Route Overlap</span>
          <div class="factor-bar-track"><div class="factor-bar-fill" style="width:${breakdown.route_score || 0}%; background:#2563EB;"></div></div>
          <span class="factor-score-val">${breakdown.route_score || 0}</span>
        </div>
        <div class="factor-bar-row">
          <span class="factor-name">Time Compatibility</span>
          <div class="factor-bar-track"><div class="factor-bar-fill" style="width:${breakdown.time_score || 0}%; background:#3B82F6;"></div></div>
          <span class="factor-score-val">${breakdown.time_score || 0}</span>
        </div>
        <div class="factor-bar-row">
          <span class="factor-name">Detour Required</span>
          <div class="factor-bar-track"><div class="factor-bar-fill" style="width:${breakdown.detour_score || 90}%; background:#06B6D4;"></div></div>
          <span class="factor-score-val">${breakdown.detour_score || 90}</span>
        </div>
        <div class="factor-bar-row">
          <span class="factor-name">Cost Compatibility</span>
          <div class="factor-bar-track"><div class="factor-bar-fill" style="width:${breakdown.cost_score || breakdown.budget_score || 85}%; background:#10B981;"></div></div>
          <span class="factor-score-val">${breakdown.cost_score || breakdown.budget_score || 85}</span>
        </div>
        <div class="factor-bar-row">
          <span class="factor-name">Safety Compatibility</span>
          <div class="factor-bar-track"><div class="factor-bar-fill" style="width:${breakdown.safety_score || 0}%; background:#F59E0B;"></div></div>
          <span class="factor-score-val">${breakdown.safety_score || 0}</span>
        </div>
        <div class="factor-bar-row">
          <span class="factor-name">Driver Reliability</span>
          <div class="factor-bar-track"><div class="factor-bar-fill" style="width:${breakdown.reliability_score || 92}%; background:#8B5CF6;"></div></div>
          <span class="factor-score-val">${breakdown.reliability_score || 92}</span>
        </div>
      </div>

      <!-- Pricing Comparison -->
      <div class="match-pricing-bar">
        <div>
          <span class="pool-fare-text">₹${pricing.fare_amount || 45}</span>
          <span class="auto-compare-text">₹${pricing.auto_fare_estimate || pricing.auto_estimate || 140} auto</span>
          <span class="savings-tag">Save ₹${pricing.savings_amount || 95} (${pricing.savings_percent || 68}%)</span>
        </div>
        <div>
          <span style="font-size:11px; color:#047857;">🌱 ${pricing.co2_saved_kg || 1.8} kg CO₂</span>
        </div>
      </div>

      <div style="display:flex; gap:8px; margin-top:12px;">
        <button class="btn btn-outline btn-sm" style="flex:1;" onclick='previewMatchOnMap(${JSON.stringify(m)})'>
          🗺️ Preview on Map
        </button>
        <button class="btn btn-primary btn-sm" style="flex:1;" onclick='bookMatchRide(${JSON.stringify(m)}, ${JSON.stringify(searchPayload)})'>
          ⚡ Book Ride (Get OTP)
        </button>
      </div>
    `;

    container.appendChild(matchCard);

    // Automatically preview the #1 match on map
    if (idx === 0) {
      previewMatchOnMap(m);
    }
  });
}

function previewMatchOnMap(match) {
  renderRouteOnMap(match.ride.route_polyline, match.ride.is_offline_routing);
  setPickupMarker(match.meeting_point.pickup_original[0], match.meeting_point.pickup_original[1], "Your Pickup");
  setDropMarker(match.drop_meeting_point.drop_original[0], match.drop_meeting_point.drop_original[1], "Your Drop");
  renderMeetingPoint(match.meeting_point, match.meeting_point.pickup_original);
}

async function bookMatchRide(match, searchPayload) {
  const bookingData = {
    ride_id: match.ride_id,
    rider_id: currentUser ? currentUser.id : 1,
    pickup_name: searchPayload.pickup_name,
    pickup_lat: searchPayload.pickup_lat,
    pickup_lng: searchPayload.pickup_lng,
    drop_name: searchPayload.drop_name,
    drop_lat: searchPayload.drop_lat,
    drop_lng: searchPayload.drop_lng,
    meeting_point: match.meeting_point,
    drop_meeting_point: match.drop_meeting_point,
    seats_booked: searchPayload.seats_needed || 1,
    segment_km: match.segment_km,
    priority_mode: searchPayload.priority_mode,
    match_score: match.match_score,
    match_reasons: match.match_reasons,
    score_breakdown: match.score_breakdown,
    auto_accept: true // Instant demo auto-accept
  };

  try {
    const res = await fetch("/api/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bookingData)
    });
    const data = await res.json();
    if (data.success) {
      showBookingModal(data.booking);
      showToast("Ride booked successfully!");
    } else {
      showToast(data.detail || "Booking failed.");
    }
  } catch (err) {
    console.error("Booking error:", err);
    showToast("Error processing booking.");
  }
}

function showBookingModal(booking) {
  const modal = document.getElementById("modal-booking");
  const body = document.getElementById("modal-booking-body");

  body.innerHTML = `
    <div style="text-align:center; padding:10px 0;">
      <div style="font-size:36px; margin-bottom:8px;">🎉</div>
      <h4>Your Commute Pool is Confirmed!</h4>
      <p class="text-muted">Driver ${booking.driver_name} (${booking.driver_vehicle}) has been matched.</p>
      
      <div class="otp-box-display mt-3" style="background:#FEF3C7; border-color:#F59E0B;">
        <div style="font-size:11px; color:#92400E; font-weight:700;">4-DIGIT PICKUP OTP (SHOW TO DRIVER)</div>
        <div class="otp-code-big" style="color:#B45309;">${booking.otp_code}</div>
      </div>

      <div class="card mt-3" style="text-align:left; background:var(--input-bg);">
        <div style="font-size:12px; margin-bottom:4px;">📍 <strong>Pickup:</strong> ${booking.pickup_name}</div>
        ${booking.meeting_point ? `<div style="font-size:12px; color:#D97706; margin-bottom:4px;">🚶 <strong>Suggested Meeting Point:</strong> ${booking.meeting_point.walk_meters}m walk (~${booking.meeting_point.walk_minutes} min)</div>` : ''}
        <div style="font-size:12px; margin-bottom:4px;">🏁 <strong>Drop:</strong> ${booking.drop_name}</div>
        <div style="font-size:12px; margin-top:8px; font-weight:bold; color:var(--primary-dark);">
          Fare: ₹${booking.fare_amount} (You save ₹${booking.savings_amount} vs Auto!)
        </div>
      </div>
    </div>
  `;

  modal.style.display = "flex";
}

// -------------------------------------------------------------
// OFFER RIDE (DRIVER)
// -------------------------------------------------------------

async function previewDriverRoute() {
  const oLat = parseFloat(document.getElementById("offer-origin-lat").value);
  const oLng = parseFloat(document.getElementById("offer-origin-lng").value);
  const dLat = parseFloat(document.getElementById("offer-dest-lat").value);
  const dLng = parseFloat(document.getElementById("offer-dest-lng").value);

  if (!oLat || !dLat) {
    showToast("Please enter origin and destination to preview route.");
    return;
  }

  showToast("Calculating driving route geometry...");
  setPickupMarker(oLat, oLng, "Origin");
  setDropMarker(dLat, dLng, "Destination");
}

async function handleOfferRide(e) {
  e.preventDefault();
  const oLat = parseFloat(document.getElementById("offer-origin-lat").value);
  const oLng = parseFloat(document.getElementById("offer-origin-lng").value);
  const dLat = parseFloat(document.getElementById("offer-dest-lat").value);
  const dLng = parseFloat(document.getElementById("offer-dest-lng").value);

  if (!oLat || !dLat) {
    showToast("Please select origin and destination from search or map!");
    return;
  }

  const payload = {
    driver_id: currentUser ? currentUser.id : 3,
    origin_name: document.getElementById("offer-origin-input").value,
    origin_lat: oLat,
    origin_lng: oLng,
    dest_name: document.getElementById("offer-dest-input").value,
    dest_lat: dLat,
    dest_lng: dLng,
    departure_time: document.getElementById("offer-time").value,
    seats: parseInt(document.getElementById("offer-seats").value),
    price_per_km: parseFloat(document.getElementById("offer-price-km").value),
    is_women_only: document.getElementById("offer-women-only") ? document.getElementById("offer-women-only").checked : false,
    is_recurring: document.getElementById("offer-recurring") ? document.getElementById("offer-recurring").checked : true
  };

  const btn = document.getElementById("btn-post-ride");
  btn.textContent = "Posting & Computing Road Geometry...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/rides", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      showToast("Ride offered successfully! AI is matching commuters along your corridor.");
      renderRouteOnMap(data.ride.route_polyline, data.ride.is_offline_routing);
      switchTab("trips");
    } else {
      showToast(data.detail || "Failed to post ride.");
    }
  } catch (err) {
    console.error("Post ride error:", err);
    showToast("Error posting ride.");
  } finally {
    btn.textContent = "✨ Post Ride & Enable Pool Matches";
    btn.disabled = false;
  }
}

// -------------------------------------------------------------
// COLLEGE NETWORK & STUDENT COMMUTE POOLING
// -------------------------------------------------------------

async function loadCollegePools(domain = "all") {
  currentCollegeFilter = domain;
  const container = document.getElementById("college-pools-list-container");
  if (!container) return;
  container.innerHTML = `<div class="p-3 text-muted">Loading active campus pools...</div>`;

  try {
    const url = domain && domain !== "all" 
      ? `/api/college/pools?college_domain=${encodeURIComponent(domain)}`
      : `/api/college/pools`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.success) {
      renderCollegePools(data.pools);
    } else {
      container.innerHTML = `<p class="text-muted p-3">No campus pools found.</p>`;
    }
  } catch (err) {
    console.error("Load college pools error:", err);
    container.innerHTML = `<p class="text-muted p-3">Failed to load campus pools.</p>`;
  }
}

function filterCollegePools(domain, btnElement) {
  document.querySelectorAll(".btn-campus").forEach(b => b.classList.remove("active"));
  if (btnElement) btnElement.classList.add("active");
  loadCollegePools(domain);
}

function renderCollegePools(pools) {
  const container = document.getElementById("college-pools-list-container");
  if (!container) return;

  if (!pools || pools.length === 0) {
    container.innerHTML = `<div class="card p-4 text-center text-muted" style="grid-column: 1 / -1;">No active campus pools found for this filter. Click "+ Create Campus Pool" to publish one!</div>`;
    return;
  }

  const userId = currentUser ? currentUser.id : 1;

  container.innerHTML = pools.map(p => {
    const isMember = (p.members || []).includes(userId) || p.creator_id === userId;
    const isFull = p.members_count >= p.total_seats;
    const discountedFare = (p.fare_per_seat * 0.85).toFixed(0);

    return `
      <div class="college-pool-card card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <div class="badge badge-info" style="font-size:10px;">${p.college_domain || 'Campus Pool'}</div>
            <h4 style="margin:6px 0 2px 0; font-size:15px; font-weight:700;">${p.title}</h4>
            <div style="font-size:12px; color:var(--text-muted);">
              🛣️ <strong>${p.home_zone}</strong> ➔ <strong>${p.campus_destination}</strong>
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:16px; font-weight:800; color:var(--primary-dark);">₹${discountedFare}</div>
            <div style="font-size:10px; color:#10B981; font-weight:bold;">15% Student Disc.</div>
          </div>
        </div>

        <div style="margin-top:10px; font-size:12px; display:flex; justify-content:space-between; background:var(--input-bg); padding:8px 10px; border-radius:6px;">
          <div>⏰ <strong>${p.departure_time}</strong> (Mon-Fri)</div>
          <div>💺 <strong>${p.members_count}/${p.total_seats}</strong> Seats Filled</div>
        </div>

        ${p.notices && p.notices.length > 0 ? `
          <div class="campus-notice-box mt-2" style="background:#FEF3C7; border:1px dashed #F59E0B; padding:6px 8px; border-radius:6px; font-size:11px; color:#92400E;">
            📢 <strong>Notice:</strong> "${p.notices[p.notices.length - 1].message}"
          </div>
        ` : ''}

        <div style="display:flex; gap:8px; margin-top:12px;">
          ${isMember ? `
            <button class="btn btn-outline text-danger btn-sm" style="flex:1;" onclick="leaveCollegePool(${p.id})">Leave Pool</button>
          ` : `
            <button class="btn btn-primary btn-sm" style="flex:1;" ${isFull ? 'disabled' : ''} onclick="joinCollegePool(${p.id})">
              ${isFull ? 'Pool Full' : '🤝 Join Campus Pool'}
            </button>
          `}
          <button class="btn btn-secondary btn-sm" onclick="viewPoolNotices(${p.id}, '${p.title.replace(/'/g, "\\'")}')">📢 Notice Board</button>
        </div>
      </div>
    `;
  }).join('');
}

async function joinCollegePool(poolId) {
  const userId = currentUser ? currentUser.id : 1;
  try {
    const res = await fetch(`/api/college/pools/${poolId}/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
    const data = await res.json();
    if (data.success) {
      showToast("🎉 Joined campus pool! 15% student fare discount applied.");
      loadCollegePools(currentCollegeFilter);
    } else {
      showToast(data.detail || "Could not join pool.");
    }
  } catch (err) {
    console.error("Join pool error:", err);
    showToast("Error joining campus pool.");
  }
}

async function leaveCollegePool(poolId) {
  const userId = currentUser ? currentUser.id : 1;
  try {
    const res = await fetch(`/api/college/pools/${poolId}/leave`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
    const data = await res.json();
    if (data.success) {
      showToast("Left campus pool.");
      loadCollegePools(currentCollegeFilter);
    }
  } catch (err) {
    console.error("Leave pool error:", err);
  }
}

function openCreateCollegePoolModal() {
  const modal = document.getElementById("modal-create-college-pool");
  if (modal) modal.style.display = "flex";
}

async function handleCreateCollegePoolSubmit(e) {
  e.preventDefault();
  const userId = currentUser ? currentUser.id : 1;
  const colName = document.getElementById("cpool-college").value;
  let domain = "rec.ac.in";
  if (colName.includes("Anna University")) domain = "annauniv.edu";
  else if (colName.includes("IIT")) domain = "iitm.ac.in";
  else if (colName.includes("SRM")) domain = "srmist.edu.in";

  const payload = {
    title: document.getElementById("cpool-name").value,
    college_name: colName,
    college_domain: domain,
    direction: document.getElementById("cpool-direction").value,
    home_zone: document.getElementById("cpool-origin").value,
    campus_destination: document.getElementById("cpool-dest").value,
    departure_time: document.getElementById("cpool-time").value,
    total_seats: parseInt(document.getElementById("cpool-seats").value),
    fare_per_seat: parseFloat(document.getElementById("cpool-fare").value),
    creator_id: userId
  };

  try {
    const res = await fetch("/api/college/pools", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      closeModal("modal-create-college-pool");
      showToast("🎓 Campus pool published to student notice board!");
      loadCollegePools(currentCollegeFilter);
    } else {
      showToast(data.detail || "Failed to create pool.");
    }
  } catch (err) {
    console.error("Create pool error:", err);
    showToast("Error creating campus pool.");
  }
}

function openStudentVerifyModal() {
  const modal = document.getElementById("modal-student-verify");
  if (modal) modal.style.display = "flex";
}

async function handleStudentEmailVerify(e) {
  e.preventDefault();
  const email = document.getElementById("student-email-input").value.trim();
  const userId = currentUser ? currentUser.id : 1;

  try {
    const res = await fetch("/api/college/verify-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, email })
    });
    const data = await res.json();
    if (data.success) {
      closeModal("modal-student-verify");
      const tag = document.getElementById("student-college-tag");
      if (tag) tag.textContent = `${data.college_name} (@${data.domain})`;
      showToast(`🎓 ${data.message}`);
      loadCollegePools(data.domain);
    } else {
      showToast(data.detail || "Email domain verification failed.");
    }
  } catch (err) {
    console.error("Student verify error:", err);
    showToast("Error verifying student email.");
  }
}

function viewPoolNotices(poolId, poolName) {
  const msg = prompt(`Post a notice on campus board for "${poolName}":`, "Running 5 mins late tomorrow due to Tambaram railway crossing traffic.");
  if (!msg) return;
  const userId = currentUser ? currentUser.id : 1;
  const authorName = currentUser ? currentUser.name : "Student";

  fetch(`/api/college/pools/${poolId}/notices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, author_name: authorName, message: msg })
  }).then(res => res.json()).then(data => {
    if (data.success) {
      showToast("Notice posted to campus board!");
      loadCollegePools(currentCollegeFilter);
    }
  });
}

// -------------------------------------------------------------
// SMART COMMUTE PLANNER (MULTIMODAL TRANSIT GRAPH)
// -------------------------------------------------------------

async function handleMultimodalPlan(e) {
  if (e) e.preventDefault();
  const origin = document.getElementById("mm-origin-input").value;
  const dest = document.getElementById("mm-dest-input").value;
  const priorityRadio = document.querySelector('input[name="mm_priority"]:checked');
  const priority = priorityRadio ? priorityRadio.value : "fastest";

  const resultsSection = document.getElementById("multimodal-results-section");
  const container = document.getElementById("multimodal-itineraries-container");

  if (!origin || !dest) {
    showToast("Please enter origin and destination hubs.");
    return;
  }

  resultsSection.style.display = "block";
  container.innerHTML = `<div class="p-3 text-muted">Calculating multimodal door-to-door transit graph across Metro, Bus, Train & Carpools...</div>`;

  try {
    const res = await fetch("/api/multimodal/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        origin_name: origin,
        dest_name: dest,
        departure_time: "08:30",
        priority_mode: priority
      })
    });
    const data = await res.json();
    if (data.success && data.itineraries && data.itineraries.length > 0) {
      currentMultimodalItineraries = data.itineraries;
      renderMultimodalItineraries(data.itineraries);
      previewMultimodalOnMap(data.itineraries[0]);
    } else {
      container.innerHTML = `<div class="card p-3 text-muted">No direct multimodal routes found. Try central hubs like Tambaram, Guindy, Central, or Velachery.</div>`;
    }
  } catch (err) {
    console.error("Multimodal plan error:", err);
    container.innerHTML = `<div class="card p-3 text-muted">Failed to compute multimodal itineraries.</div>`;
  }
}

function renderMultimodalItineraries(itineraries) {
  const container = document.getElementById("multimodal-itineraries-container");
  if (!container) return;

  container.innerHTML = itineraries.map((it, idx) => {
    const carpoolLeg = (it.legs || []).find(l => l.mode === "carpool");
    return `
      <div class="card mb-3" style="border-left: 4px solid var(--primary-color);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <span class="badge badge-info">Option #${idx + 1}</span>
            <h4 style="margin:4px 0; font-size:15px; font-weight:700;">${it.title}</h4>
            <div style="font-size:12px; color:var(--text-muted);">
              ⏱️ <strong>${it.total_duration_mins} mins</strong> • 💰 <strong>₹${it.total_cost_inr}</strong> • 🌱 <strong>${it.co2_saved_kg} kg CO₂</strong> • 🛡️ <strong>${it.safety_rating}★</strong>
            </div>
          </div>
          <button class="btn btn-xs btn-outline" onclick="previewMultimodalOnMap(currentMultimodalItineraries[${idx}])">🗺️ Show on Map</button>
        </div>

        <!-- Transit Leg Timeline -->
        <div class="transit-legs-timeline mt-3">
          ${(it.legs || []).map(leg => {
            let modeIcon = "🚶";
            let badgeClass = "badge-secondary";
            if (leg.mode === "metro") { modeIcon = "🚇"; badgeClass = "badge-primary"; }
            else if (leg.mode === "suburban_train") { modeIcon = "🚆"; badgeClass = "badge-info"; }
            else if (leg.mode === "bus") { modeIcon = "🚌"; badgeClass = "badge-warning"; }
            else if (leg.mode === "carpool") { modeIcon = "🚗"; badgeClass = "badge-success"; }

            return `
              <div class="transit-leg-item">
                <div class="leg-mode-pill">
                  <span class="badge ${badgeClass}">${modeIcon} ${leg.mode.toUpperCase().replace('_', ' ')}</span>
                  <span style="font-size:11px; font-weight:bold; margin-left:6px;">${leg.from_name} ➔ ${leg.to_name}</span>
                </div>
                <div style="font-size:11px; color:var(--text-muted); margin-left:8px;">
                  ${leg.duration_mins} min • ₹${leg.cost_inr} • ${leg.instructions}
                </div>
              </div>
            `;
          }).join('')}
        </div>

        ${carpoolLeg ? `
          <div class="mt-3 pt-2" style="border-top:1px dashed var(--border-color); display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:12px; color:var(--primary-dark); font-weight:600;">🚗 Peer carpool leg available (${carpoolLeg.from_name} ➔ ${carpoolLeg.to_name})</span>
            <button class="btn btn-sm btn-primary" onclick='bookCarpoolLeg(${JSON.stringify(carpoolLeg)})'>
              ⚡ Book This Carpool Leg
            </button>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

function previewMultimodalOnMap(itinerary) {
  if (!itinerary || !itinerary.legs) return;
  if (driverRouteLayer) map.removeLayer(driverRouteLayer);

  const polylineCoords = [];
  (itinerary.legs || []).forEach(l => {
    if (l.polyline && l.polyline.length > 0) {
      polylineCoords.push(...l.polyline);
    }
  });

  if (polylineCoords.length > 0) {
    driverRouteLayer = L.polyline(polylineCoords, {
      color: "#2563EB",
      weight: 5,
      opacity: 0.85
    }).addTo(map);
    map.fitBounds(driverRouteLayer.getBounds(), { padding: [40, 40] });

    setPickupMarker(polylineCoords[0][0], polylineCoords[0][1], itinerary.legs[0].from_name);
    setDropMarker(polylineCoords[polylineCoords.length - 1][0], polylineCoords[polylineCoords.length - 1][1], itinerary.legs[itinerary.legs.length - 1].to_name);
  }
}

function bookCarpoolLeg(leg) {
  switchTab("find");
  document.getElementById("find-pickup-input").value = leg.from_name;
  document.getElementById("find-pickup-lat").value = leg.polyline && leg.polyline[0] ? leg.polyline[0][0] : 12.9249;
  document.getElementById("find-pickup-lng").value = leg.polyline && leg.polyline[0] ? leg.polyline[0][1] : 80.1000;
  
  document.getElementById("find-drop-input").value = leg.to_name;
  document.getElementById("find-drop-lat").value = leg.polyline && leg.polyline.length > 0 ? leg.polyline[leg.polyline.length - 1][0] : 13.0067;
  document.getElementById("find-drop-lng").value = leg.polyline && leg.polyline.length > 0 ? leg.polyline[leg.polyline.length - 1][1] : 80.2025;

  showToast(`Pre-filled carpool leg: ${leg.from_name} ➔ ${leg.to_name}`);
  const form = document.getElementById("find-ride-form");
  if (form) handleFindRide(new Event("submit"));
}

// -------------------------------------------------------------
// MY TRIPS & LIVE TRACKING ENGINE
// -------------------------------------------------------------

async function loadMyTrips() {
  if (!currentUser) return;
  try {
    const res = await fetch(`/api/my-trips?user_id=${currentUser.id}`);
    const data = await res.json();
    if (data.success) {
      renderMyTrips(data.bookings, data.offered_rides);
    }
  } catch (err) {
    console.error("Load trips error:", err);
  }
}

function renderMyTrips(bookings, offeredRides) {
  const container = document.getElementById("my-trips-list");
  const bannerContainer = document.getElementById("active-trip-banner-container");
  container.innerHTML = "";
  bannerContainer.innerHTML = "";

  const activeBooking = bookings.find(b => b.status === "confirmed" || b.status === "in_progress" || b.status === "driver_arriving");
  
  if (activeBooking) {
    activeLiveBooking = activeBooking;
    bannerContainer.innerHTML = `
      <div class="active-trip-card">
        <div class="active-trip-header">
          <div>
            <span class="badge badge-warning">LIVE TRIP ACTIVE</span>
            <h3 style="margin-top:4px;">${activeBooking.pickup_name.split('(')[0]} → ${activeBooking.drop_name.split('(')[0]}</h3>
          </div>
          <div style="text-align:right;">
            <div style="font-size:12px; opacity:0.9;">Status: <strong>${activeBooking.status.toUpperCase()}</strong></div>
            <div style="font-size:14px; font-weight:800; color:#FDE047;">₹${activeBooking.fare_amount}</div>
          </div>
        </div>

        <div class="otp-box-display">
          <div style="font-size:10px; text-transform:uppercase; letter-spacing:1px;">Pickup Verification OTP</div>
          <div class="otp-code-big">${activeBooking.otp_code}</div>
        </div>

        <!-- Driver OTP Entry (if current user is driver) -->
        ${(currentUser.role === 'driver' || currentUser.role === 'both') && activeBooking.status === 'confirmed' ? `
          <div style="background:rgba(255,255,255,0.1); padding:10px; border-radius:8px; margin:8px 0;">
            <label style="font-size:11px; font-weight:bold;">Driver: Enter Rider's 4-Digit OTP to Start Trip</label>
            <div style="display:flex; gap:6px; margin-top:4px;">
              <input type="text" id="driver-otp-input" placeholder="e.g. ${activeBooking.otp_code}" style="background:white; color:black; font-size:16px; font-weight:bold; letter-spacing:2px; text-align:center;">
              <button class="btn btn-success btn-sm" onclick="verifyOtpAndStart(${activeBooking.id})">Start Trip</button>
            </div>
          </div>
        ` : ''}

        <div class="trip-live-actions">
          <button class="btn btn-secondary btn-sm" onclick='startLiveTracking(${JSON.stringify(activeBooking)})'>
            📡 Live GPS Tracking
          </button>
          <button class="btn btn-warning btn-sm" onclick='simulateDriveAlongRoute(${JSON.stringify(activeBooking)})'>
            🚗 Simulate Drive (Demo)
          </button>
          <button class="btn btn-outline btn-sm text-white" onclick='simulateRouteDeviation(${JSON.stringify(activeBooking)})'>
            ⚠️ Simulate 600m Deviation
          </button>
          <button class="btn btn-danger btn-sm" onclick="triggerSos(${activeBooking.ride_id})">
            🚨 SOS
          </button>
          <button class="btn btn-outline btn-sm text-white" onclick='openShareModal("${activeBooking.tracking_token}")'>
            🔗 Share Trip
          </button>
          ${activeBooking.status === 'in_progress' ? `
            <button class="btn btn-success btn-sm" onclick='openPaymentModal(${JSON.stringify(activeBooking)})'>
              🏁 Complete Trip
            </button>
          ` : ''}
        </div>
      </div>
    `;

    // Draw route on map
    if (activeBooking.route_polyline && activeBooking.route_polyline.length > 0) {
      renderRouteOnMap(activeBooking.route_polyline);
      setPickupMarker(activeBooking.pickup_lat, activeBooking.pickup_lng, activeBooking.pickup_name);
      setDropMarker(activeBooking.drop_lat, activeBooking.drop_lng, activeBooking.drop_name);
      if (activeBooking.meeting_point) {
        renderMeetingPoint(activeBooking.meeting_point, [activeBooking.pickup_lat, activeBooking.pickup_lng]);
      }
    }
  }

  // Render past bookings list
  if (bookings.length === 0 && offeredRides.length === 0) {
    container.innerHTML = `<p class="text-muted text-center" style="padding:20px;">No trips found. Find a pool or offer empty seats to get started!</p>`;
    return;
  }

  bookings.forEach(b => {
    const card = document.createElement("div");
    card.className = "card mb-2";
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <strong>${b.pickup_name.split('(')[0]} → ${b.drop_name.split('(')[0]}</strong>
          <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">
            Driver: ${b.driver_name} • Fare: ₹${b.fare_amount} (Saved ₹${b.savings_amount})
          </div>
        </div>
        <div style="text-align:right;">
          <span class="badge badge-${b.status === 'completed' ? 'success' : (b.status === 'cancelled' ? 'danger' : 'primary')}">${b.status.toUpperCase()}</span>
          ${b.status === 'confirmed' ? `<button class="btn btn-xs btn-outline text-danger mt-1" onclick="cancelBooking(${b.id})">Cancel</button>` : ''}
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

async function verifyOtpAndStart(bookingId) {
  const otpInput = document.getElementById("driver-otp-input");
  const otp = otpInput ? otpInput.value.trim() : "";
  if (!otp) {
    showToast("Please enter the 4-digit OTP.");
    return;
  }

  try {
    const res = await fetch(`/api/bookings/${bookingId}/verify-otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ otp })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      loadMyTrips();
    } else {
      showToast(data.detail || "Invalid OTP code.");
    }
  } catch (err) {
    console.error("OTP verification error:", err);
    showToast("Error verifying OTP.");
  }
}

async function cancelBooking(bookingId) {
  if (!confirm("Are you sure you want to cancel this booking?")) return;
  try {
    const res = await fetch(`/api/bookings/${bookingId}/cancel`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showToast("Booking cancelled and seats restored.");
      loadMyTrips();
    }
  } catch (err) {
    console.error("Cancel error:", err);
  }
}

// -------------------------------------------------------------
// Live GPS Simulation & WebSockets + Polling Fallback
// -------------------------------------------------------------

function startLiveTracking(booking) {
  if (activeWebSocket) {
    try { activeWebSocket.close(); } catch(e){}
    activeWebSocket = null;
  }
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }

  const rideId = booking.ride_id || booking.id;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/ride/${rideId}`;

  let wsConnected = false;
  try {
    activeWebSocket = new WebSocket(wsUrl);

    activeWebSocket.onopen = () => {
      wsConnected = true;
      showToast("Connected to Live GPS Stream over WebSocket!");
    };

    activeWebSocket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "vehicle_position") {
        updateLiveVehicleMarker(msg.lat, msg.lng, msg.heading);

        const devBanner = document.getElementById("deviation-banner");
        if (devBanner) {
          devBanner.style.display = (msg.deviation && msg.deviation.is_deviated) ? "flex" : "none";
        }
      }
    };

    activeWebSocket.onerror = (err) => {
      console.warn("WebSocket unavailable. Switching to HTTP Polling fallback...");
      startPollingFallback(rideId);
    };

    activeWebSocket.onclose = () => {
      if (!wsConnected) {
        startPollingFallback(rideId);
      }
    };
  } catch (err) {
    console.warn("WebSocket error. Using HTTP polling fallback...");
    startPollingFallback(rideId);
  }
}

function startPollingFallback(rideId) {
  if (pollingInterval) clearInterval(pollingInterval);
  showToast("📡 Live tracking active via HTTP Polling fallback.");

  pollingInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/rides/${rideId}/live-status`);
      const data = await res.json();
      if (data.success && data.ride) {
        const r = data.ride;
        if (r.last_lat && r.last_lng) {
          updateLiveVehicleMarker(r.last_lat, r.last_lng);
        }
        const devBanner = document.getElementById("deviation-banner");
        if (devBanner) {
          devBanner.style.display = (r.last_deviation_m > 200 || r.sos_active) ? "flex" : "none";
        }
      }
    } catch (e) {
      console.error("Polling error:", e);
    }
  }, 2000);
}

function updateLiveVehicleMarker(lat, lng, heading = 0) {
  if (liveCarMarker) map.removeLayer(liveCarMarker);

  const icon = L.divIcon({
    className: "car-gps-icon",
    html: `<div style="background:#2563EB; color:white; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-size:18px; border:2px solid white; box-shadow:0 0 10px rgba(37,99,235,0.6); transform:rotate(${heading}deg);">🚘</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16]
  });

  liveCarMarker = L.marker([lat, lng], { icon }).addTo(map);
  map.panTo([lat, lng]);
}

function simulateDriveAlongRoute(booking) {
  if (!booking.route_polyline || booking.route_polyline.length === 0) {
    showToast("No route polyline available for simulation.");
    return;
  }

  startLiveTracking(booking);
  if (simulationInterval) clearInterval(simulationInterval);

  let step = 0;
  const polyline = booking.route_polyline;
  showToast("🚗 Simulating smooth vehicle movement along Chennai corridor...");

  simulationInterval = setInterval(() => {
    if (step >= polyline.length) {
      clearInterval(simulationInterval);
      showToast("🏁 Vehicle reached destination! Opening safe-drop check-in...");
      document.getElementById("modal-safedrop").style.display = "flex";
      return;
    }

    const [lat, lng] = polyline[step];
    
    // Update live state via REST & WebSocket
    fetch(`/api/rides/${booking.ride_id}/gps-update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat, lng, speed_kmh: 38.0, heading: 45 })
    }).catch(() => {});

    if (activeWebSocket && activeWebSocket.readyState === WebSocket.OPEN) {
      activeWebSocket.send(JSON.stringify({
        type: "gps_update",
        ride_id: booking.ride_id,
        lat: lat,
        lng: lng,
        speed_kmh: 38.0,
        heading: 45,
        simulated: true
      }));
    } else {
      updateLiveVehicleMarker(lat, lng);
    }

    step++;
  }, 1000);
}

function simulateRouteDeviation(booking) {
  if (!booking.route_polyline || booking.route_polyline.length === 0) return;
  const [lat, lng] = booking.route_polyline[Math.floor(booking.route_polyline.length / 2)];
  
  // Shift coordinates by ~700 meters
  const devLat = lat + 0.006;
  const devLng = lng + 0.006;

  showToast("⚠️ Simulating off-route detour (650m deviation)...");

  fetch(`/api/rides/${booking.ride_id}/gps-update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat: devLat, lng: devLng, speed_kmh: 40.0, heading: 90 })
  }).catch(() => {});

  if (activeWebSocket && activeWebSocket.readyState === WebSocket.OPEN) {
    activeWebSocket.send(JSON.stringify({
      type: "gps_update",
      ride_id: booking.ride_id,
      lat: devLat,
      lng: devLng,
      speed_kmh: 40.0,
      heading: 90,
      simulated: true
    }));
  }
}

// -------------------------------------------------------------
// SAFETY SUITE (SOS, ID VERIFICATION, MEMBERSHIP, SHARE)
// -------------------------------------------------------------

async function triggerSos(rideId = null) {
  try {
    const res = await fetch("/api/safety/sos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUser ? currentUser.id : 1,
        ride_id: rideId || (activeLiveBooking ? activeLiveBooking.ride_id : 1),
        lat: 13.0067,
        lng: 80.2025
      })
    });
    const data = await res.json();
    if (data.success) {
      const modal = document.getElementById("modal-sos");
      const body = document.getElementById("modal-sos-body");
      body.innerHTML = `
        <div style="text-align:center;">
          <div style="font-size:40px; margin-bottom:10px;">🚨</div>
          <h4 style="color:#991B1B;">Emergency Services & Contacts Notified!</h4>
          <p style="margin-top:6px; font-size:13px;">${data.message}</p>
          <div class="card mt-3" style="text-align:left; background:#FEF2F2; border-color:#FCA5A5;">
            <div><strong>Dispatched to:</strong> ${data.details.police_control_room}</div>
            <div style="margin-top:4px;"><strong>Live GPS Link:</strong> <a href="${data.details.share_url}" target="_blank">${window.location.origin}${data.details.share_url}</a></div>
          </div>
        </div>
      `;
      modal.style.display = "flex";
    }
  } catch (err) {
    console.error("SOS error:", err);
  }
}

function openShareModal(token) {
  const modal = document.getElementById("modal-share");
  const body = document.getElementById("modal-share-body");
  const t = token || (activeLiveBooking ? activeLiveBooking.tracking_token : 'live_token');
  const shareUrl = `${window.location.origin}/api/track/${t}`;
  const driverName = activeLiveBooking ? activeLiveBooking.driver_name : "Suresh Kumar";
  const vehicle = activeLiveBooking ? activeLiveBooking.driver_vehicle : "White Swift Dzire (TN 09 AB 1234)";
  const waMessage = encodeURIComponent(`Hi! I am traveling on PoolPilot with driver ${driverName} in ${vehicle}. Track my live commute in real-time here: ${shareUrl}`);

  body.innerHTML = `
    <p>Share this live read-only tracking link with family or friends. No login required:</p>
    <div style="display:flex; gap:6px; margin:14px 0;">
      <input type="text" value="${shareUrl}" id="share-link-input" readonly style="font-size:12px;">
      <button class="btn btn-secondary btn-sm" onclick="copyShareLink()">📋 Copy</button>
    </div>
    <div class="mt-2">
      <a href="https://wa.me/?text=${waMessage}" target="_blank" class="btn btn-success btn-block" style="text-decoration:none; display:flex; align-items:center; justify-content:center; gap:6px;">
        <span>💬 Share via WhatsApp (1-Click)</span>
      </a>
    </div>
    <div style="font-size:12px; color:var(--text-muted); margin-top:10px;">
      🔒 Real-time GPS coordinates, vehicle plate, route deviation alerts, and driver trust score are visible in real time.
    </div>
  `;
  modal.style.display = "flex";
}

function copyShareLink() {
  const input = document.getElementById("share-link-input");
  input.select();
  document.execCommand("copy");
  showToast("Tracking link copied to clipboard!");
}

function shareTrackingToWhatsApp(phone = "") {
  const token = activeLiveBooking ? activeLiveBooking.tracking_token : "share_token_demo";
  const driverName = activeLiveBooking ? activeLiveBooking.driver_name : "Suresh Kumar";
  const vehicle = activeLiveBooking ? activeLiveBooking.driver_vehicle : "White Swift Dzire (TN 09 AB 1234)";
  const trackUrl = `${window.location.origin}/api/track/${token}`;

  const message = `Hi! I am traveling on PoolPilot with driver ${driverName} in ${vehicle}. Track my live commute in real-time here: ${trackUrl}`;
  const encodedMsg = encodeURIComponent(message);
  const waUrl = phone ? `https://wa.me/91${phone.replace(/\D/g, '')}?text=${encodedMsg}` : `https://wa.me/?text=${encodedMsg}`;
  window.open(waUrl, "_blank");
}

async function loadTrustedContacts() {
  const userId = currentUser ? currentUser.id : 1;
  const container = document.getElementById("trusted-contacts-list");
  if (!container) return;

  try {
    const res = await fetch(`/api/user/${userId}/trusted-contacts`);
    const data = await res.json();
    if (data.success) {
      renderTrustedContacts(data.contacts);
    }
  } catch (err) {
    console.error("Load trusted contacts error:", err);
  }
}

function renderTrustedContacts(contacts) {
  const container = document.getElementById("trusted-contacts-list");
  if (!container) return;

  if (!contacts || contacts.length === 0) {
    container.innerHTML = `<p class="text-muted" style="font-size:12px;">No trusted contacts in your circle yet. Add up to 5 contacts for 1-click WhatsApp trip sharing and automatic deviation alerts.</p>`;
    return;
  }

  container.innerHTML = contacts.map((c, idx) => `
    <div class="card mt-2" style="background:var(--input-bg); padding:8px 12px; display:flex; justify-content:space-between; align-items:center;">
      <div>
        <strong>${c.name} (${c.relation || 'Contact'})</strong>
        <div style="font-size:11px; color:var(--text-muted);">📞 ${c.phone}</div>
      </div>
      <div style="display:flex; gap:6px;">
        <button class="btn btn-xs btn-outline" style="border-color:#10B981; color:#059669;" onclick="shareTrackingToWhatsApp('${c.phone}')">
          💬 WhatsApp
        </button>
        <button class="btn btn-xs btn-outline text-danger" onclick="deleteTrustedContact(${idx})">✕</button>
      </div>
    </div>
  `).join('');
}

function openAddTrustedContactModal() {
  const modal = document.getElementById("modal-add-contact");
  if (modal) modal.style.display = "flex";
}

async function handleAddTrustedContactSubmit(e) {
  e.preventDefault();
  const userId = currentUser ? currentUser.id : 1;
  const name = document.getElementById("contact-name").value.trim();
  const phone = document.getElementById("contact-phone").value.trim();
  const relation = document.getElementById("contact-relation").value;

  try {
    const res = await fetch(`/api/user/${userId}/trusted-contacts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone, relation })
    });
    const data = await res.json();
    if (data.success) {
      closeModal("modal-add-contact");
      showToast("✅ Trusted contact added to your circle!");
      loadTrustedContacts();
    } else {
      showToast(data.detail || "Failed to add contact.");
    }
  } catch (err) {
    console.error("Add contact error:", err);
    showToast("Error adding contact.");
  }
}

async function deleteTrustedContact(index) {
  const userId = currentUser ? currentUser.id : 1;
  try {
    const res = await fetch(`/api/user/${userId}/trusted-contacts/${index}`, { method: "DELETE" });
    const data = await res.json();
    if (data.success) {
      showToast("Contact removed.");
      loadTrustedContacts();
    }
  } catch (err) {
    console.error("Delete contact error:", err);
  }
}

async function handleMockVerifyId(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-verify-id");
  const docType = document.getElementById("verify-doc-type").value;
  btn.textContent = "Scanning Document & Verifying Biometrics...";
  btn.disabled = true;

  setTimeout(async () => {
    try {
      const res = await fetch("/api/user/verify-id", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: currentUser ? currentUser.id : 1,
          doc_type: docType,
          filename: "sample_verified_id.png"
        })
      });
      const data = await res.json();
      if (data.success) {
        currentUser = data.user;
        updateUserUI();
        updateSafetyProfileUI();
        showToast(`🎉 ${data.message} Trust Score upgraded to ${data.trust_score}!`);
      }
    } catch (err) {
      console.error("Verify ID error:", err);
    } finally {
      btn.textContent = "⚡ Run Mock ID & Face Verification";
      btn.disabled = false;
    }
  }, 1200);
}

async function handleRegisterVehicle(e) {
  e.preventDefault();
  const vNum = document.getElementById("reg-plate-num").value;
  const vModel = document.getElementById("reg-plate-model").value;

  try {
    const res = await fetch("/api/user/register-vehicle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUser ? currentUser.id : 1,
        vehicle_number: vNum,
        vehicle_model: vModel,
        total_seats: 4
      })
    });
    const data = await res.json();
    if (data.success) {
      currentUser = data.user;
      updateUserUI();
      showToast("✅ Vehicle registered and plate format validated!");
    } else {
      showToast(data.detail || "Validation failed.");
    }
  } catch (err) {
    console.error("Vehicle registration error:", err);
  }
}

async function purchaseMembership() {
  try {
    const res = await fetch("/api/user/membership", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: currentUser ? currentUser.id : 1 })
    });
    const data = await res.json();
    if (data.success) {
      currentUser = data.user;
      updateUserUI();
      updateSafetyProfileUI();
      showToast("⭐ Verified Trust Membership activated! Enjoy 5% platform commission!");
    }
  } catch (err) {
    console.error("Membership error:", err);
  }
}

function updateSafetyProfileUI() {
  if (!currentUser) return;
  document.getElementById("safety-score-value").textContent = currentUser.trust_score;
  const badgePill = document.getElementById("safety-badge-pill");
  badgePill.textContent = `${currentUser.trust_badge} Verified`;
  badgePill.className = `badge badge-${currentUser.trust_badge.toLowerCase()}`;

  // Trust items
  document.getElementById("trust-item-id").querySelector(".trust-status").textContent =
    currentUser.is_id_verified ? "✓ Verified (+25 pts)" : "Pending Verification";
  document.getElementById("trust-member-status").textContent =
    currentUser.is_member ? "Active (5% Fee, +5 pts)" : "Not Active (10% Fee)";
}

function checkNightSafetyMode() {
  const hour = new Date().getHours();
  // 9 PM (21) to 5 AM (5)
  if (hour >= 21 || hour < 5) {
    const banner = document.getElementById("night-mode-banner");
    if (banner) banner.style.display = "flex";
  }
}

function handleSafeDropResponse(isSafe) {
  closeModal("modal-safedrop");
  fetch("/api/safety/safe-drop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: currentUser ? currentUser.id : 1,
      is_safe: isSafe,
      feedback: isSafe ? "Reached home safely." : "Deviation noted."
    })
  });
  showToast(isSafe ? "Safe-drop verified! Thank you for carpooling with PoolPilot." : "Report recorded.");
}

function openPaymentModal(booking) {
  const modal = document.getElementById("modal-payment");
  const body = document.getElementById("modal-payment-body");

  body.innerHTML = `
    <div style="text-align:center;">
      <div style="font-size:24px; font-weight:800; color:var(--primary-dark);">₹${booking.fare_amount}</div>
      <div style="font-size:12px; color:var(--text-muted); margin-bottom:12px;">Ride Completed • Saved ₹${booking.savings_amount} vs Auto!</div>

      <!-- Commission & Driver Payout Split -->
      <div class="card" style="background:var(--input-bg); text-align:left; font-size:12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <span>Driver Payout (${booking.driver_name}):</span>
          <strong>₹${booking.driver_payout}</strong>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <span>Platform Commission (${booking.commission_amount > 0 ? '5-10%' : '10%'}):</span>
          <strong>₹${booking.commission_amount}</strong>
        </div>
        <div style="display:flex; justify-content:space-between; color:#047857; font-weight:bold; margin-top:6px; border-top:1px dashed var(--border-color); padding-top:4px;">
          <span>🌱 CO₂ Emissions Saved:</span>
          <span>${(booking.fare_amount * 0.05).toFixed(2)} kg</span>
        </div>
      </div>

      <!-- Mock UPI QR Code Visual -->
      <div style="margin:14px auto; width:130px; height:130px; background:white; border:2px solid black; padding:6px; display:flex; align-items:center; justify-content:center; border-radius:8px;">
        <div style="font-size:10px; font-weight:bold; text-align:center; color:#333;">
          [ MOCK UPI QR ]<br>
          upi://pay?pa=poolpilot@okaxis<br>&am=${booking.fare_amount}
        </div>
      </div>

      <div style="display:flex; gap:8px;">
        <button class="btn btn-primary btn-block" onclick="processPayment(${booking.id}, 'wallet')">
          💳 Pay via Wallet (₹${currentUser ? currentUser.wallet_balance : 150})
        </button>
        <button class="btn btn-secondary btn-block" onclick="processPayment(${booking.id}, 'upi')">
          📱 Pay via UPI
        </button>
      </div>
    </div>
  `;
  modal.style.display = "flex";
}

async function processPayment(bookingId, method) {
  try {
    const res = await fetch(`/api/bookings/${bookingId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payment_method: method })
    });
    const data = await res.json();
    if (data.success) {
      closeModal("modal-payment");
      showToast(`Payment successful via ${method.toUpperCase()}!`);
      loadMyTrips();
    }
  } catch (err) {
    console.error("Payment error:", err);
  }
}

// -------------------------------------------------------------
// PERSONAL & COLLEGE IMPACT DASHBOARD
// -------------------------------------------------------------

async function loadAdminData() {
  try {
    const res = await fetch("/api/admin/metrics");
    const data = await res.json();
    if (data.success) {
      renderAdminCharts(data.hourly_distribution);
      renderGreenLeaderboard(data.green_leaderboard);
      renderTopRoutes(data.top_routes);
      loadAIModelsStatus();
    }
  } catch (err) {
    console.error("Admin data error:", err);
  }
}

async function loadImpactData(month = "March 2026") {
  const userId = currentUser ? currentUser.id : 1;
  try {
    // 1. Personal Impact
    const resP = await fetch(`/api/impact/personal?user_id=${userId}&month=${encodeURIComponent(month)}`);
    const dataP = await resP.json();
    if (dataP.success) {
      currentPersonalImpact = dataP;
      const s = dataP.selected_month;
      if (document.getElementById("imp-co2")) document.getElementById("imp-co2").textContent = `${s.co2_saved_kg} kg`;
      if (document.getElementById("imp-money")) document.getElementById("imp-money").textContent = `₹${s.money_saved_inr}`;
      if (document.getElementById("imp-fuel")) document.getElementById("imp-fuel").textContent = `${s.fuel_saved_liters} L`;
      if (document.getElementById("imp-rides")) document.getElementById("imp-rides").textContent = s.rides_pooled;

      renderSocialShareCanvas(dataP);
    }

    // 2. College Impact Cascade & Leaderboard
    const resC = await fetch(`/api/impact/college?user_id=${userId}&month=${encodeURIComponent(month)}`);
    const dataC = await resC.json();
    if (dataC.success) {
      const bannerHeadline = document.getElementById("cascade-headline");
      if (bannerHeadline) {
        bannerHeadline.textContent = dataC.banner_headline;
      }
      renderGreenLeaderboard(dataC.leaderboard);
    }
  } catch (err) {
    console.error("Load impact data error:", err);
  }
}

function renderSocialShareCanvas(data) {
  const canvas = document.getElementById("social-share-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const width = canvas.width;
  const height = canvas.height;

  // Clear & Draw gradient background
  const grad = ctx.createLinearGradient(0, 0, width, height);
  grad.addColorStop(0, "#0F172A");
  grad.addColorStop(1, "#1E293B");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, width, height);

  // Border Accent
  ctx.strokeStyle = "#10B981";
  ctx.lineWidth = 3;
  ctx.strokeRect(6, 6, width - 12, height - 12);

  // Header Title
  ctx.fillStyle = "#10B981";
  ctx.font = "bold 15px sans-serif";
  ctx.fillText("🌱 POOLPILOT CHENNAI IMPACT", 24, 34);

  const userName = currentUser ? currentUser.name : "Rahul Verma";
  const userOrg = currentUser && currentUser.college_company ? currentUser.college_company : "REC Chennai";
  const month = data && data.selected_month ? data.selected_month.month : "March 2026";

  ctx.fillStyle = "#F8FAFC";
  ctx.font = "bold 17px sans-serif";
  ctx.fillText(userName, 24, 62);

  ctx.fillStyle = "#94A3B8";
  ctx.font = "12px sans-serif";
  ctx.fillText(`${userOrg} • ${month}`, 24, 80);

  // Stats Boxes
  const s = (data && data.selected_month) ? data.selected_month : { co2_saved_kg: 52.8, money_saved_inr: 3100, fuel_saved_liters: 35.2, rides_pooled: 18 };

  // Box 1: CO2
  ctx.fillStyle = "rgba(16, 185, 129, 0.15)";
  ctx.fillRect(24, 96, 205, 58);
  ctx.fillStyle = "#34D399";
  ctx.font = "bold 19px sans-serif";
  ctx.fillText(`${s.co2_saved_kg} kg`, 34, 124);
  ctx.fillStyle = "#94A3B8";
  ctx.font = "11px sans-serif";
  ctx.fillText("CO₂ Emissions Prevented", 34, 142);

  // Box 2: Money
  ctx.fillStyle = "rgba(59, 130, 246, 0.15)";
  ctx.fillRect(245, 96, 210, 58);
  ctx.fillStyle = "#60A5FA";
  ctx.font = "bold 19px sans-serif";
  ctx.fillText(`₹${s.money_saved_inr}`, 255, 124);
  ctx.fillStyle = "#94A3B8";
  ctx.font = "11px sans-serif";
  ctx.fillText("Commute Money Saved", 255, 142);

  // Box 3: Fuel
  ctx.fillStyle = "rgba(245, 158, 11, 0.15)";
  ctx.fillRect(24, 164, 205, 58);
  ctx.fillStyle = "#FBBF24";
  ctx.font = "bold 19px sans-serif";
  ctx.fillText(`${s.fuel_saved_liters} L`, 34, 192);
  ctx.fillStyle = "#94A3B8";
  ctx.font = "11px sans-serif";
  ctx.fillText("Petrol / Fuel Saved", 34, 210);

  // Box 4: Rides Pooled & Tree Equiv
  ctx.fillStyle = "rgba(139, 92, 246, 0.15)";
  ctx.fillRect(245, 164, 210, 58);
  ctx.fillStyle = "#A78BFA";
  ctx.font = "bold 19px sans-serif";
  ctx.fillText(`${s.rides_pooled} Rides Pooled`, 255, 192);
  ctx.fillStyle = "#94A3B8";
  ctx.font = "11px sans-serif";
  ctx.fillText(`≈ ${Math.max(1, Math.round(s.co2_saved_kg / 20))} Trees Planted 🌳`, 255, 210);

  // Footer Branding
  ctx.fillStyle = "#64748B";
  ctx.font = "10px sans-serif";
  ctx.fillText("poolpilot.vercel.app • Chennai Green Mobility Network", 24, 248);
}

function exportSocialShareCard() {
  const canvas = document.getElementById("social-share-canvas");
  if (!canvas) return;
  const link = document.createElement("a");
  link.download = "poolpilot_impact_card.png";
  link.href = canvas.toDataURL("image/png");
  link.click();
  showToast("📥 Impact Share Card downloaded as PNG!");
}

function renderAdminCharts(hourlyData) {
  if (typeof Chart === "undefined") return;

  // Chart 1: Hourly Demand
  const ctxDemand = document.getElementById("chart-demand") || document.getElementById("chart-hourly-demand");
  if (ctxDemand) {
    if (chartDemandInstance) chartDemandInstance.destroy();
    chartDemandInstance = new Chart(ctxDemand, {
      type: "bar",
      data: {
        labels: hourlyData.map(d => d.hour),
        datasets: [{
          label: "Pooled Commute Rides",
          data: hourlyData.map(d => d.rides),
          backgroundColor: "#10B981",
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  // Chart 2: Cumulative CO2 Trend
  const ctxCo2 = document.getElementById("chart-co2-trend");
  if (ctxCo2) {
    if (chartCo2Instance) chartCo2Instance.destroy();
    chartCo2Instance = new Chart(ctxCo2, {
      type: "line",
      data: {
        labels: ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Today"],
        datasets: [{
          label: "Cumulative CO₂ Saved (kg)",
          data: [45, 95, 160, 230, 290, 340, 385],
          borderColor: "#059669",
          backgroundColor: "rgba(16, 185, 129, 0.15)",
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }
}

function renderGreenLeaderboard(leaderboard) {
  const container = document.getElementById("green-leaderboard-container");
  if (!container || !leaderboard) return;

  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Campus / Organization</th>
          <th>Type</th>
          <th>Trips</th>
          <th>CO₂ Saved</th>
        </tr>
      </thead>
      <tbody>
        ${leaderboard.map(item => `
          <tr>
            <td><strong>#${item.rank}</strong></td>
            <td>${item.entity}</td>
            <td><span class="badge badge-info">${item.type}</span></td>
            <td>${item.trips}</td>
            <td><strong class="text-success">${item.co2_saved}</strong></td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderTopRoutes(routes) {
  const container = document.getElementById("top-routes-container");
  if (!container || !routes) return;

  container.innerHTML = routes.map(r => `
    <div class="card mt-2" style="display:flex; justify-content:space-between; align-items:center; background:var(--input-bg); padding:10px 14px;">
      <div>
        <strong>${r.route}</strong>
        <div style="font-size:11px; color:var(--text-muted);">${r.trips} carpools completed</div>
      </div>
      <div style="text-align:right;">
        <span class="badge badge-success">🌱 ${r.co2_kg} kg CO₂</span>
      </div>
    </div>
  `).join("");
}

// -------------------------------------------------------------
// HOME TAB (RECURRING POOLS & HOTSPOTS)
// -------------------------------------------------------------

async function loadHomeData() {
  try {
    // Recurring pools
    const resPools = await fetch("/api/ai/recurring-pools");
    const dataPools = await resPools.json();
    if (dataPools.success) {
      const container = document.getElementById("recurring-pools-container");
      if (container) {
        container.innerHTML = dataPools.groups.map(g => `
          <div class="card mt-2" style="background:var(--input-bg); padding:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong>${g.title}</strong>
              <span class="badge badge-primary">${g.schedule}</span>
            </div>
            <div style="font-size:11px; color:var(--text-muted); margin-top:3px;">🛣️ ${g.corridor}</div>
            <div style="font-size:11px; font-weight:bold; color:var(--primary-dark); margin-top:4px;">
              💰 ${g.savings_monthly} • 🌱 ${g.co2_monthly}
            </div>
          </div>
        `).join("");
      }
    }

    // Demand hotspots with AI model labelling
    const resHotspots = await fetch("/api/ai/demand-hotspots");
    const dataHotspots = await resHotspots.json();
    if (dataHotspots.success) {
      const container = document.getElementById("demand-hotspots-container");
      if (container) {
        container.innerHTML = dataHotspots.hotspots.map(h => `
          <div class="card mt-2" style="background:var(--input-bg); padding:10px 14px; border-left:4px solid var(--warning);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div>
                <strong>${h.zone}</strong>
                <div style="font-size:10px; color:#3B82F6; font-weight:600; margin-top:2px;">
                  🤖 Model: ${h.model_used || "Chronos-Bolt-tiny"}
                </div>
              </div>
              <span class="badge badge-warning">${h.demand_level || 'High'} (${h.predicted_riders} riders)</span>
            </div>
            <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">${h.nudge_text}</div>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Home data error:", err);
  }
}

// -------------------------------------------------------------
// Voice Booking (Browser Web Speech API + Parser)
// -------------------------------------------------------------

let voiceRecognition = null;

function startVoiceBooking() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const banner = document.getElementById("voice-booking-banner");
  const transcriptText = document.getElementById("voice-transcript-text");

  if (!SpeechRecognition) {
    const query = prompt("Web Speech API not supported in this browser.\nPlease type your commute request (e.g. 'Ride to T Nagar at 8 AM'):", "Ride to T Nagar at 8 AM");
    if (query) processVoiceText(query);
    return;
  }

  try {
    voiceRecognition = new SpeechRecognition();
    voiceRecognition.lang = "en-IN";
    voiceRecognition.continuous = false;
    voiceRecognition.interimResults = true;

    banner.style.display = "block";
    transcriptText.textContent = "Listening... speak your destination (e.g. 'Ride to T Nagar at 8 AM')...";

    voiceRecognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      transcriptText.textContent = `"${transcript}"`;
    };

    voiceRecognition.onend = () => {
      const spoken = transcriptText.textContent.replace(/^"|"$/g, "");
      if (spoken && !spoken.includes("Listening")) {
        processVoiceText(spoken);
      }
      setTimeout(() => {
        banner.style.display = "none";
      }, 2000);
    };

    voiceRecognition.onerror = (event) => {
      console.warn("Voice error:", event.error);
      transcriptText.textContent = `Microphone notice: ${event.error}. Please type destination.`;
    };

    voiceRecognition.start();
  } catch (err) {
    console.error("Voice start error:", err);
    banner.style.display = "none";
    const query = prompt("Please type your commute request (e.g. 'Ride to T Nagar at 8 AM'):", "Ride to T Nagar at 8 AM");
    if (query) processVoiceText(query);
  }
}

function stopVoiceBooking() {
  if (voiceRecognition) {
    try { voiceRecognition.stop(); } catch(e){}
  }
  const banner = document.getElementById("voice-booking-banner");
  if (banner) banner.style.display = "none";
}

async function processVoiceText(text) {
  showToast(`Parsing: "${text}"...`);
  try {
    const res = await fetch("/api/ai/parse-voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (data.success && data.drop_place) {
      document.getElementById("find-drop-input").value = data.drop_place.name;
      document.getElementById("find-drop-lat").value = data.drop_place.lat;
      document.getElementById("find-drop-lng").value = data.drop_place.lng;
      setDropMarker(data.drop_place.lat, data.drop_place.lng, data.drop_place.name);

      if (data.origin_place) {
        document.getElementById("find-pickup-input").value = data.origin_place.name;
        document.getElementById("find-pickup-lat").value = data.origin_place.lat;
        document.getElementById("find-pickup-lng").value = data.origin_place.lng;
        setPickupMarker(data.origin_place.lat, data.origin_place.lng, data.origin_place.name);
      }

      if (data.departure_time) {
        document.getElementById("find-dept-time").value = data.departure_time;
      }
      if (data.seats_needed) {
        document.getElementById("find-seats").value = data.seats_needed;
      }

      showToast(`🎙️ Voice parsed: ${data.parsed_summary}`);
    } else {
      showToast("Could not recognize Chennai destination in voice. Please select from search.");
    }
  } catch (err) {
    console.error("Voice parse error:", err);
  }
}

// -------------------------------------------------------------
// AI Models: Active / Fallback Status Dashboard
// -------------------------------------------------------------

async function loadAIModelsStatus() {
  try {
    const res = await fetch("/api/ai/models-status");
    const data = await res.json();
    if (data.success) {
      const container = document.getElementById("ai-models-status-list");
      if (!container) return;

      container.innerHTML = data.subsystems.map(sub => `
        <div class="card mb-2" style="background:var(--input-bg); padding:10px 14px; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:700; font-size:13px;">${sub.feature}</div>
            <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">
              Active Engine: <strong style="color:var(--primary-dark);">${sub.active_engine}</strong>
            </div>
          </div>
          <div style="text-align:right;">
            <span class="badge badge-${sub.status === 'active_pretrained' ? 'success' : (sub.status === 'active_native' ? 'info' : 'secondary')}">
              ${sub.status === 'active_pretrained' ? '⚡ Pretrained Model Active' : (sub.status === 'active_native' ? '🌐 Browser Native' : '🛡️ Deterministic Fallback')}
            </span>
          </div>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Load AI models status error:", err);
  }
}

// -------------------------------------------------------------
// Heatmap Layer Toggle
// -------------------------------------------------------------

let heatmapActive = false;
async function toggleHeatmapLayer() {
  if (heatmapActive && heatmapLayer) {
    map.removeLayer(heatmapLayer);
    heatmapActive = false;
    document.getElementById("btn-heatmap-toggle").textContent = "🔥 Toggle Heatmap";
    return;
  }

  try {
    const res = await fetch("/api/admin/heatmap");
    const data = await res.json();
    if (data.success && data.points.length > 0) {
      if (typeof L.heatLayer === "function") {
        heatmapLayer = L.heatLayer(data.points, { radius: 25, blur: 15, maxZoom: 14 }).addTo(map);
      } else {
        const circles = data.points.map(p => L.circle([p[0], p[1]], {
          color: '#EF4444',
          fillColor: '#F87171',
          fillOpacity: 0.4,
          radius: 1200
        }));
        heatmapLayer = L.layerGroup(circles).addTo(map);
      }
      heatmapActive = true;
      document.getElementById("btn-heatmap-toggle").textContent = "❌ Hide Heatmap";
      showToast("Displaying Chennai peak-hour demand heatmap!");
    }
  } catch (err) {
    console.error("Heatmap error:", err);
  }
}

function fitMapBounds() {
  if (driverRouteLayer) {
    map.fitBounds(driverRouteLayer.getBounds(), { padding: [40, 40] });
  } else {
    map.setView([13.04, 80.20], 11);
  }
}

// -------------------------------------------------------------
// Helpers & Toast
// -------------------------------------------------------------

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.style.display = "none";
}

function showToast(message) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 3500);
}

function addMockWalletCredits() {
  if (!currentUser) return;
  currentUser.wallet_balance += 100.0;
  updateUserUI();
  showToast("₹100 added to your PoolPilot wallet!");
}

function copyReferralCode() {
  const code = document.getElementById("prof-ref-code").textContent;
  navigator.clipboard.writeText(code);
  showToast("Referral code copied!");
}
