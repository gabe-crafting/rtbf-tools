(function () {
  const data = window.COMPANIES_DATA;
  if (!data?.companies?.length) {
    document.body.innerHTML =
      "<p style='padding:2rem'>No company data found. Run <code>node scripts/build-data.mjs</code> first.</p>";
    return;
  }

  const companies = data.companies.slice().sort((a, b) => a.name.localeCompare(b.name));

  const searchInput = document.getElementById("search-input");
  const clearBtn = document.getElementById("clear-search");
  const employeesMinInput = document.getElementById("employees-min");
  const employeesMaxInput = document.getElementById("employees-max");
  const employeePresets = document.getElementById("employee-presets");
  const nationalityFilters = document.getElementById("nationality-filters");
  const resultsList = document.getElementById("results-list");
  const resultCount = document.getElementById("result-count");
  const profilePlaceholder = document.getElementById("profile-placeholder");
  const profileContent = document.getElementById("profile-content");

  let activeNationality = "";
  let activeEmployeePreset = "";
  let selectedSlug = companies[0]?.slug ?? null;

  const profileNav = document.getElementById("profile-nav");
  const profileBack = document.getElementById("profile-back");
  const profileBreadcrumb = document.getElementById("profile-breadcrumb");

  const parents = (data.parents ?? []).slice();
  const parentBySlug = Object.fromEntries(parents.map((p) => [p.slug, p]));
  const companyBySlug = Object.fromEntries(companies.map((c) => [c.slug, c]));

  let activeView = { type: "company", slug: selectedSlug };
  let returnCompanySlug = selectedSlug;

  const employeeCounts = companies
    .map((c) => c.employees)
    .filter((n) => typeof n === "number");
  const globalEmployeeMax = Math.max(...employeeCounts, 0);

  employeesMaxInput.max = String(globalEmployeeMax);

  marked.setOptions({ gfm: true, breaks: false });

  const allNationalities = [
    ...new Set(companies.flatMap((c) => c.nationalities)),
  ].sort();

  const EMPLOYEE_PRESETS = [
    { id: "", label: "Any size" },
    { id: "micro", label: "Micro (1–10)", min: 1, max: 10 },
    { id: "small", label: "11–50", min: 11, max: 50 },
    { id: "mid", label: "51–100", min: 51, max: 100 },
    { id: "large", label: "100+", min: 101, max: globalEmployeeMax },
  ];

  function formatNationality(n) {
    return n.charAt(0).toUpperCase() + n.slice(1);
  }

  function companySearchText(company) {
    return [
      company.name,
      company.tradingName,
      company.cui,
      company.westernLink,
      company.label,
      company.employeesLabel,
      company.employees,
      ...company.nationalities.map(formatNationality),
    ]
      .join(" ")
      .toLowerCase();
  }

  function parseBound(value) {
    if (value === "" || value == null) return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  function getEmployeeBounds() {
    return {
      min: parseBound(employeesMinInput.value),
      max: parseBound(employeesMaxInput.value),
    };
  }

  function hasActiveFilters() {
    const query = searchInput.value.trim();
    const { min, max } = getEmployeeBounds();
    return Boolean(query || activeNationality || min != null || max != null);
  }

  function matchesQuery(company, query) {
    if (!query) return true;
    const tokens = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const haystack = companySearchText(company);
    return tokens.every((token) => haystack.includes(token));
  }

  function matchesNationality(company) {
    if (!activeNationality) return true;
    return company.nationalities.includes(activeNationality);
  }

  function matchesEmployees(company) {
    const { min, max } = getEmployeeBounds();
    if (min == null && max == null) return true;
    if (typeof company.employees !== "number") return false;

    if (min != null && company.employees < min) return false;
    if (max != null && company.employees > max) return false;
    return true;
  }

  function getFiltered() {
    const query = searchInput.value.trim();
    return companies.filter(
      (c) =>
        matchesQuery(c, query) &&
        matchesNationality(c) &&
        matchesEmployees(c)
    );
  }

  function syncPresetFromInputs() {
    const { min, max } = getEmployeeBounds();
    const match = EMPLOYEE_PRESETS.find(
      (preset) =>
        preset.id &&
        preset.min === min &&
        preset.max === max
    );
    activeEmployeePreset = match?.id ?? "";
    renderEmployeePresets();
  }

  function renderEmployeePresets() {
    employeePresets.innerHTML = "";

    for (const preset of EMPLOYEE_PRESETS) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = `chip${activeEmployeePreset === preset.id ? " active" : ""}`;
      chip.textContent = preset.label;
      chip.addEventListener("click", () => {
        if (activeEmployeePreset === preset.id && preset.id) {
          activeEmployeePreset = "";
          employeesMinInput.value = "";
          employeesMaxInput.value = "";
        } else {
          activeEmployeePreset = preset.id;
          if (preset.id) {
            employeesMinInput.value = String(preset.min);
            employeesMaxInput.value = String(preset.max);
          } else {
            employeesMinInput.value = "";
            employeesMaxInput.value = "";
          }
        }
        renderEmployeePresets();
        renderResults();
      });
      employeePresets.appendChild(chip);
    }
  }

  function renderNationalityChips() {
    nationalityFilters.innerHTML = "";

    const allChip = document.createElement("button");
    allChip.type = "button";
    allChip.className = `chip${activeNationality === "" ? " active" : ""}`;
    allChip.textContent = "All";
    allChip.addEventListener("click", () => {
      activeNationality = "";
      renderNationalityChips();
      renderResults();
    });
    nationalityFilters.appendChild(allChip);

    for (const nationality of allNationalities) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = `chip${activeNationality === nationality ? " active" : ""}`;
      chip.textContent = formatNationality(nationality);
      chip.addEventListener("click", () => {
        activeNationality = activeNationality === nationality ? "" : nationality;
        renderNationalityChips();
        renderResults();
      });
      nationalityFilters.appendChild(chip);
    }
  }

  function parseInternalHref(href) {
    if (!href) return null;
    const parentMatch = href.match(/(?:\.\.\/)?parents\/([^#?]+\.md)/);
    if (parentMatch) return { type: "parent", slug: parentMatch[1].replace(".md", "") };
    const companyMatch = href.match(/(?:\.\.\/)?companies\/([^#?]+\.md)/);
    if (companyMatch) return { type: "company", slug: companyMatch[1].replace(".md", "") };
    return null;
  }

  function updateProfileNav() {
    if (activeView.type === "parent") {
      const company = companyBySlug[returnCompanySlug];
      profileNav.hidden = false;
      profileBreadcrumb.textContent = company
        ? `Parent company · from ${company.name}`
        : "Parent company";
      profileBack.textContent = "← Back to company";
      return;
    }
    profileNav.hidden = true;
    profileBreadcrumb.textContent = "";
  }

  function wireInternalLinks() {
    profileContent.querySelectorAll("a[href]").forEach((anchor) => {
      const target = parseInternalHref(anchor.getAttribute("href"));
      if (!target) return;
      anchor.classList.add("profile-internal");
      anchor.addEventListener("click", (event) => {
        event.preventDefault();
        if (target.type === "parent" && parentBySlug[target.slug]) {
          showParent(target.slug);
        } else if (target.type === "company" && companyBySlug[target.slug]) {
          selectCompany(target.slug);
        }
      });
    });
  }

  function showParent(slug) {
    const parent = parentBySlug[slug];
    if (!parent) return;
    if (activeView.type === "company") {
      returnCompanySlug = activeView.slug ?? selectedSlug;
    }
    activeView = { type: "parent", slug };
    profilePlaceholder.hidden = true;
    profileContent.hidden = false;
    profileContent.innerHTML = marked.parse(parent.markdown);
    wireInternalLinks();
    updateProfileNav();
  }

  function renderProfile(company) {
    if (!company) {
      activeView = { type: "empty", slug: null };
      profilePlaceholder.hidden = false;
      profileContent.hidden = true;
      profileContent.innerHTML = "";
      updateProfileNav();
      return;
    }

    activeView = { type: "company", slug: company.slug };
    profilePlaceholder.hidden = true;
    profileContent.hidden = false;
    profileContent.innerHTML = marked.parse(company.markdown);
    wireInternalLinks();
    updateProfileNav();
  }

  function selectCompany(slug) {
    selectedSlug = slug;
    returnCompanySlug = slug;
    const company = companies.find((c) => c.slug === slug);
    renderProfile(company);
    [...resultsList.querySelectorAll(".result-item")].forEach((btn) => {
      btn.classList.toggle("selected", btn.dataset.slug === slug);
    });
  }

  profileBack.addEventListener("click", () => {
    if (returnCompanySlug && companyBySlug[returnCompanySlug]) {
      selectCompany(returnCompanySlug);
    }
  });

  function formatEmployeeMeta(company) {
    if (typeof company.employees === "number") {
      return `${company.employees} emp`;
    }
    return "emp. n/a";
  }

  function renderResults() {
    const filtered = getFiltered();

    clearBtn.hidden = !hasActiveFilters();

    resultCount.textContent = hasActiveFilters()
      ? `${filtered.length} of ${companies.length} companies`
      : `Showing all ${companies.length} companies`;

    resultsList.innerHTML = "";

    if (!filtered.length) {
      const empty = document.createElement("li");
      empty.className = "empty-state";
      empty.textContent = "No companies match your search.";
      resultsList.appendChild(empty);
      renderProfile(null);
      return;
    }

    if (!filtered.some((c) => c.slug === selectedSlug)) {
      selectedSlug = filtered[0].slug;
    }

    for (const company of filtered) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `result-item${company.slug === selectedSlug ? " selected" : ""}`;
      btn.dataset.slug = company.slug;
      btn.setAttribute("role", "option");
      btn.setAttribute("aria-selected", company.slug === selectedSlug ? "true" : "false");

      const title = document.createElement("span");
      title.className = "result-title";
      title.textContent = company.name;

      const meta = document.createElement("span");
      meta.className = "result-meta";
      const flags = company.nationalities.map(formatNationality).join(", ") || "Nationality unclear";
      meta.textContent = `${flags} · ${formatEmployeeMeta(company)} · ${company.label}`;

      btn.append(title, meta);
      btn.addEventListener("click", () => selectCompany(company.slug));
      li.appendChild(btn);
      resultsList.appendChild(li);
    }

    const selected = companies.find((c) => c.slug === selectedSlug);
    renderProfile(selected);
  }

  searchInput.addEventListener("input", renderResults);

  employeesMinInput.addEventListener("input", () => {
    syncPresetFromInputs();
    renderResults();
  });

  employeesMaxInput.addEventListener("input", () => {
    syncPresetFromInputs();
    renderResults();
  });

  clearBtn.addEventListener("click", () => {
    searchInput.value = "";
    employeesMinInput.value = "";
    employeesMaxInput.value = "";
    activeNationality = "";
    activeEmployeePreset = "";
    renderEmployeePresets();
    renderNationalityChips();
    searchInput.focus();
    renderResults();
  });

  renderEmployeePresets();
  renderNationalityChips();
  renderResults();
})();
