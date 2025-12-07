/* ============================================================
   POKEBUILDER — APP PRINCIPAL
   Backend: FastAPI (Elasticsearch + AI)
   Frontend: Vanilla JS
   ============================================================ */

document.addEventListener("DOMContentLoaded", async () => {

  /* ============================================================
     CONFIGURACIÓ BACKEND
     ============================================================ */
  const API_BASE = "http://127.0.0.1:8000/api/v1";

  /* ============================================================
     FUNCIONS DE DADES (API)
     ============================================================ */

    const paginationContainer = document.getElementById("pagination-controls");

    const renderPagination = (totalItems) => {
        paginationContainer.innerHTML = "";

        const totalPages = Math.ceil(totalItems / tableState.limit);

        if (totalPages <= 1) return; // No cal paginació si només hi ha 1 pàgina

        // Funció auxiliar per crear botó
        const createBtn = (text, page, isActive = false, isDisabled = false) => {
            const btn = document.createElement("button");
            btn.className = `page-btn ${isActive ? 'active' : ''}`;
            btn.textContent = text;
            btn.disabled = isDisabled;
            if (!isDisabled && !isActive) {
                btn.addEventListener("click", () => {
                    tableState.currentPage = page;
                    renderTable();
                });
            }
            return btn;
        };

        // 1. Botó ANTERIOR (<)
        paginationContainer.appendChild(createBtn("<", tableState.currentPage - 1, false, tableState.currentPage === 1));

        // 2. Botons de PÀGINA (Lògica de finestra lliscant)
        // Volem mostrar un màxim de botons (ex: 8)
        let startPage, endPage;
        const maxButtons = 8;

        if (totalPages <= maxButtons) {
            // Si hi ha poques pàgines, les mostrem totes
            startPage = 1;
            endPage = totalPages;
        } else {
            // Si n'hi ha moltes, centrem la vista
            const maxPagesBeforeCurrent = Math.floor(maxButtons / 2);
            const maxPagesAfterCurrent = Math.ceil(maxButtons / 2) - 1;

            if (tableState.currentPage <= maxPagesBeforeCurrent) {
                // Estem al principi (ex: Page 1, 2, 3...)
                startPage = 1;
                endPage = maxButtons;
            } else if (tableState.currentPage + maxPagesAfterCurrent >= totalPages) {
                // Estem al final
                startPage = totalPages - maxButtons + 1;
                endPage = totalPages;
            } else {
                // Estem al mig
                startPage = tableState.currentPage - maxPagesBeforeCurrent;
                endPage = tableState.currentPage + maxPagesAfterCurrent;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationContainer.appendChild(createBtn(i, i, i === tableState.currentPage));
        }

        // 3. Botó SEGÜENT (>)
        paginationContainer.appendChild(createBtn(">", tableState.currentPage + 1, false, tableState.currentPage === totalPages));
    };

    // Nova funció de cerca que envia TOTS els filtres al Backend (amb traducció)
    async function fetchPokemons(state) {
        try {
            const params = new URLSearchParams();

            // 1. Text (Nom o ID)
            if (state.filterName) params.append("q", state.filterName);
            else if (state.filterId) params.append("q", state.filterId);

            // 2. Tipus (Llista)
            if (state.filterTypes && state.filterTypes.length > 0) {
                state.filterTypes.forEach(t => params.append("types", t));
            }

            // 3. Stats Mínims
            if (state.minStats) {
                // El backend espera noms en anglès per als filtres de rang (hp_min, speed_min...),
                // així que aquí NO cal traduir, ja que l'API d'en Torrent està ben feta per als filtres.
                if (state.minStats.hp > 0) params.append("hp_min", state.minStats.hp);
                if (state.minStats.attack > 0) params.append("attack_min", state.minStats.attack);
                if (state.minStats.defense > 0) params.append("defense_min", state.minStats.defense);
                if (state.minStats.special_attack > 0) params.append("special_attack_min", state.minStats.special_attack);
                if (state.minStats.special_defense > 0) params.append("special_defense_min", state.minStats.special_defense);
                if (state.minStats.speed > 0) params.append("speed_min", state.minStats.speed);
            }

            // 4. Ordenació (AQUÍ ÉS ON FEM LA MÀGIA DE TRADUCCIÓ)
            if (state.sortKey) {
                let sortField = state.sortKey;

                // Diccionari: "El que tenim al HTML" -> "El que vol el Backend"
                const translationMap = {
                    'speed': 'velocitat',
                    'attack': 'atac',
                    'defense': 'defensa',
                    'special_attack': 'atac_especial',
                    'special_defense': 'defensa_especial'
                    // 'hp' és igual en els dos, 'id' i 'name' també
                };

                // Si la clau està al diccionari, la canviem. Si no, la deixem tal qual.
                if (translationMap[sortField]) {
                    sortField = translationMap[sortField];
                }

                params.append("stat", sortField);
            }

            params.append("order", state.sortAsc ? "asc" : "desc");

            // CÀLCUL DE L'OFFSET
            const offset = (state.currentPage - 1) * state.limit;

            params.append("limit", state.limit);
            params.append("offset", offset); // <--- AFEGIR AIXÒ
            params.append("order", state.sortAsc ? "asc" : "desc");

            const res = await fetch(`${API_BASE}/pokemon/search?${params.toString()}`);
            if (!res.ok) throw new Error("Error de connexió amb l'API");
            return await res.json();

        } catch (err) {
            console.error("Error carregant Pokémon:", err);
            // En cas d'error retornem estructura buida segura
            return { total: 0, results: [] };
        }
    }

  // Nova funció per obtenir Pokémon ordenats per estadística
  async function fetchSortedPokemons(stat, order) {
    try {
      const res = await fetch(`${API_BASE}/pokemon/sort?stat=${stat}&order=${order}`);
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Error ordenant Pokémon");
      }
      return await res.json();
    } catch (err) {
      console.error("Error ordenant:", err);
      alert("Error: " + err.message);
      return [];
    }
  }
/*
  // Carrega inicial de tots els Pokémon
  async function fetchAllPokemons() {
    const letters = "abcdefghijklmnopqrstuvwxyz".split("");
    const all = [];
    const seen = new Set();

    for (const letter of letters) {
      const data = await fetchPokemons(letter);
      for (const p of data) {
        if (!seen.has(p.pokedex_id)) {
          seen.add(p.pokedex_id);
          all.push(p);
        }
      }
    }

    all.sort((a, b) => a.pokedex_id - b.pokedex_id);
    console.log(`Dades carregades: ${all.length} Pokémon.`);
    return all;
  }*/

  /* ============================================================
     UTILITATS I CONSTANTS
     ============================================================ */
  const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();

  const getSpriteUrl = id => `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png`;
  const padId = n => `#${String(n).padStart(3, "0")}`;

  const TYPE_RGB = {
    normal:[168,168,120], fire:[240,128,48], water:[104,144,240],
    electric:[248,208,48], grass:[120,200,80], ice:[152,216,216],
    fighting:[192,48,40], poison:[160,64,160], ground:[224,192,104],
    flying:[168,144,240], psychic:[248,88,136], bug:[168,184,32],
    rock:[184,160,56], ghost:[112,88,152], dragon:[112,56,248],
    dark:[112,88,72], steel:[184,184,208], fairy:[238,153,172]
  };

  const typeToRGB = t => {
    const arr = TYPE_RGB[t] || [200,200,200];
    return `${arr[0]}, ${arr[1]}, ${arr[2]}`;
  };

    // Funció per esperar que l'usuari acabi d'escriure abans de disparar l'acció
    const debounce = (func, delay) => {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(null, args);
            }, delay);
        };
    };

  /* ============================================================
     ESTAT GLOBAL
     ============================================================ */

  let savedData = localStorage.getItem("pokeBuilder_team"); // <-- LA NOVA CLAU UNIFICADA
  let team = savedData ? JSON.parse(savedData) : Array(6).fill(null);
  let editingIndex = null;

    /* ============================================================
       FUNCIONS AUXILIARS
       ============================================================ */

    // NOU: Funció per guardar l'equip al LocalStorage
    const saveTeamToStorage = () => {
        localStorage.setItem("pokeBuilder_team", JSON.stringify(team));
    };

    // 3. Modificar funció d'obrir modal
    const openSearch = (index) => {
        editingIndex = index;

        // Reset inputs visuals...
        filterIdInput.value = "";
        filterNameInput.value = "";
        Object.values(filterStatsInputs).forEach(input => input.value = "");

        // Reset estat...
        tableState = {
            filterId: "",
            filterName: "",
            filterTypes: [],
            minStats: { hp: 0, attack: 0, defense: 0, special_attack: 0, special_defense: 0, speed: 0 },

            // AFEGEIX AIXÒ:
            currentPage: 1,
            limit: 50,

            sortKey: "id",
            sortAsc: true
        };
        updateTypeButtonText();

        // JA NO CAL CARREGAR RES ABANS.
        // Simplement obrim el modal i demanem la primera pàgina.
        searchModal.style.display = "block";
        filterNameInput.focus();
        document.body.style.overflow = 'hidden';

        renderTable(); // Això dispararà la petició al backend
    };

// Funció per tancar (només per referència, ja la tens)
    const closeSearch = () => {
        searchModal.style.display = "none";
        editingIndex = null;
        document.body.style.overflow = '';
    };


  // Dades en memòria per a la cerca ràpida
  let mockPokemonData = [];

  /* ============================================================
     ELEMENTS DEL DOM
     ============================================================ */
  //Loading
  const loadingSpinner = document.getElementById("loading-spinner");
  // Equip i Carrusel
  const teamGrid       = document.getElementById("team-grid");
  const carouselInner  = document.getElementById("carousel-inner");

  // Modal Cerca
  const searchModal    = document.getElementById("pokemon-modal");
  const searchCloseBtn = searchModal.querySelector(".close-btn");
  const pokemonListUl  = document.getElementById("pokemon-list");

  // Controls d'Ordenació (Cerca)
  const sortStatEl     = document.getElementById("sort-stat");
  const sortOrderEl    = document.getElementById("sort-order");

  // Modal Recomanació (IA)
  const recommendModal   = document.getElementById("recommend-modal");
  const recommendBtn     = document.getElementById("recommend-btn");
  const recommendCloseBtn= recommendModal.querySelector(".close-btn");
  const recommendSprite  = document.getElementById("recommend-sprite");
  const recommendStatus  = document.getElementById("recommend-status");
  const recommendResults = document.getElementById("recommend-results");

  // Botons Acció Global
  const randomBtn = document.getElementById("random-btn");
  const clearBtn  = document.getElementById("clear-btn");
  const addBtn    = document.getElementById("add-btn");

  // Holo Stats
  const powerEl = document.getElementById("team-power-val");
  const domEl = document.getElementById("team-dominant-val");
  const weakEl = document.getElementById("team-weak-val");

  /* ============================================================
     FUNCIONS DE RENDERITZAT (UI)
     ============================================================ */

  // Renderitza la graella principal de l'equip
  const renderTeamGrid = () => {
    teamGrid.innerHTML = "";

    team.forEach((poke, idx) => {
      if (!poke) {
        // Targeta buida
        const add = document.createElement("div");
        add.className = "add-card";
        add.innerHTML = `<div class="plus">＋</div><div class="txt">Afegir Pokémon</div>`;
        add.addEventListener("click", () => openSearch(idx));
        teamGrid.appendChild(add);
      } else {
        // Targeta plena
        teamGrid.appendChild(buildTopCard(poke, idx));
      }
    });

    updateRecommendButtonState();
    rebuildCarousel();
    updateHoloStats();
  };

  // Construeix la targeta individual del Pokémon
  const buildTopCard = (poke, idx) => {
    const type = poke.types ? poke.types[0] : "normal";
    const rgb = typeToRGB(type.toLowerCase());

    // Contenidor principal
    const card = document.createElement("div");
    card.className = "poke-card";
    card.style.setProperty("--type-rgb", rgb);

    // Contenidor 3D
    const inner = document.createElement("div");
    inner.className = "card-inner";

    // --- CARA FRONTAL ---
    const front = document.createElement("div");
    front.className = "card-face card-front";

    const head = document.createElement("div");
    head.className = "card-head";
    const img = document.createElement("img");
    img.className = "card-sprite";
    img.src = poke.sprite_url || getSpriteUrl(poke.pokedex_id);
    img.alt = poke.name;
    head.append(img);

    const body = document.createElement("div");
    body.className = "card-body";
    const title = document.createElement("div");
    title.className = "card-title";
    title.innerHTML = `
      <div class="card-name">${capitalize(poke.name)}</div>
      <div class="card-id">${padId(poke.pokedex_id)}</div>
    `;

    const typePillContainer = document.createElement("div");
    typePillContainer.className = "type-pill-container";
    poke.types.forEach(t => {
      const pill = document.createElement("div");
      pill.className = "type-pill";
      pill.textContent = t.toUpperCase();
      pill.style.setProperty("--type-rgb", typeToRGB(t.toLowerCase()));
      typePillContainer.appendChild(pill);
    });

    body.append(title, typePillContainer);
    front.append(head, body);

    // --- CARA POSTERIOR ---
    const back = document.createElement("div");
    back.className = "card-face card-back";

    // Botons d'acció (Eliminar / Editar)
    const actions = document.createElement("div");
    actions.className = "card-actions-back";

    const removeBtn = document.createElement("button");
    removeBtn.className = "action-btn remove";
    removeBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>`;
    removeBtn.addEventListener("click", e => {
      e.stopPropagation();
      removeFromTeam(idx);
    });

    const editBtn = document.createElement("button");
    editBtn.className = "action-btn edit";
    editBtn.innerHTML = `<img src="src/edit-icon.png" style="width:16px; height:16px; filter: invert(1);">`;
    editBtn.addEventListener("click", e => {
      e.stopPropagation();
      localStorage.setItem("currentTeam", JSON.stringify(team));
      localStorage.setItem("editIndex", idx);
      window.location.href = "edit.html";
    });

    actions.append(removeBtn, editBtn);
    back.appendChild(actions);

    // Estadístiques
    const statsContainer = document.createElement("div");
    statsContainer.className = "stats-container";

    const statsList = document.createElement("div");
    statsList.className = "stats-bars-container";

    if (poke.stats) {
        const statsInOrder = [
            ['hp', 'HP'], ['attack', 'ATK'], ['defense', 'DEF'],
            ['special_attack', 'SPA'], ['special_defense', 'SPD'], ['speed', 'SPE']
        ];
        const MAX_STAT = 150;

        statsInOrder.forEach(([key, label]) => {
            const val = poke.stats[key];
            const percent = Math.min((val / MAX_STAT) * 100, 100);

            const row = document.createElement("div");
            row.className = "stat-row-compact";
            row.innerHTML = `
                <div class="stat-label">${label}</div>
                <div class="stat-bar-track">
                    <div class="stat-bar-fill" style="width: ${percent}%; background: rgb(${rgb})"></div>
                </div>
                <div class="stat-val">${val}</div>
            `;
            statsList.appendChild(row);
        });
    }
    statsContainer.appendChild(statsList);
    back.appendChild(statsContainer);

    inner.append(front, back);
    card.appendChild(inner);

    return card;
  };

  /* ============================================================
     LÒGICA DEL CARRUSEL 3D
     ============================================================ */
  const rebuildCarousel = () => {
    const selected = team.filter(Boolean);
    const qty = selected.length || 1;
    carouselInner.style.setProperty("--quantity", qty);
    carouselInner.innerHTML = "";

    selected.forEach((p, index) => {
      const card = document.createElement("div");
      card.className = "card";
      card.style.setProperty("--index", index);
      card.style.setProperty("--color-card", typeToRGB(p.types[0].toLowerCase()));

      const imgWrap = document.createElement("div");
      imgWrap.className = "img";
      imgWrap.innerHTML = `<img src="${p.sprite_url}" alt="${p.name}">`;

      card.appendChild(imgWrap);
      card.addEventListener("click", () => {
        const idx = team.findIndex(t => t && t.name.toLowerCase() === p.name.toLowerCase());
        if (idx !== -1) removeFromTeam(idx);
      });
      carouselInner.appendChild(card);
    });
  };

  /* ============================================================
     HOLO STATS (LÒGICA D'ANÀLISI)
     ============================================================ */
  async function updateHoloStats() {
    const activeTeam = team.filter(Boolean);

    if (!powerEl || !domEl || !weakEl) return;

    // Reset si està buit
    if (activeTeam.length === 0) {
      powerEl.textContent = "0";
      domEl.textContent = "-";
      weakEl.textContent = "-";
      return;
    }

    // 1. Càlcul Local (Poder i Dominància)
    let totalPower = 0;
    const typeCounts = {};

    activeTeam.forEach(p => {
      if(p.stats) {
        totalPower += (p.stats.hp + p.stats.attack + p.stats.defense + p.stats.special_attack + p.stats.special_defense + p.stats.speed);
      }
      p.types.forEach(t => {
        typeCounts[t] = (typeCounts[t] || 0) + 1;
      });
    });

    animateValue(powerEl, parseInt(powerEl.textContent) || 0, totalPower, 800);

    let maxType = "-";
    let maxCount = 0;
    for (const [t, count] of Object.entries(typeCounts)) {
      if (count > maxCount) {
        maxCount = count;
        maxType = t;
      }
    }

    domEl.textContent = maxType.toUpperCase();
    if (maxType !== "-") {
        domEl.style.color = `rgb(${typeToRGB(maxType.toLowerCase())})`;
    } else {
        domEl.style.color = "#fff";
    }

    // 2. Consulta al Backend (Vulnerabilitats)
    weakEl.textContent = "...";
    weakEl.style.color = "rgba(255,255,255,0.5)";

    try {
        const teamIds = activeTeam.map(p => p.pokedex_id);

        const response = await fetch(`${API_BASE}/ai/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team_ids: teamIds })
        });

        if (!response.ok) throw new Error("Backend Error");

        const data = await response.json();

        if (data.success && data.analysis) {
            const realWeakness = data.analysis.major_weakness || "NONE";
            weakEl.textContent = realWeakness.toUpperCase();
            weakEl.style.color = "#ff4d4d";
        } else {
            weakEl.textContent = "N/A";
            weakEl.style.color = "#777";
        }

    } catch (error) {
        console.error("Error connectant amb l'IA:", error);
        weakEl.textContent = "ERR";
        weakEl.style.color = "#ef4444";
    }
  }

  function animateValue(obj, start, end, duration) {
    if (start === end) return;
    let startTimestamp = null;
    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      obj.innerHTML = Math.floor(progress * (end - start) + start);
      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    };
    window.requestAnimationFrame(step);
  }

  /* ============================================================
     GESTIÓ D'EQUIP
     ============================================================ */
  const removeFromTeam = idx => {
    team[idx] = null;
    saveTeamToStorage();
    renderTeamGrid();
    refreshSearchList(); // Actualitza la llista per desbloquejar el Pokémon eliminat
  };

  const clearTeam = () => {
    team = Array(6).fill(null);
    saveTeamToStorage();
    renderTeamGrid();
    refreshSearchList();
  };

  const fillRandomTeam = () => {
    const emptySlots = team.map((v,i) => v ? null : i).filter(v => v !== null);
    const selected = new Set(getSelectedNames());
    // Filtrem els que ja tenim
    const pool = mockPokemonData.filter(p => !selected.has(p.name.toLowerCase()));

    // Algoritme de barreja (Fisher-Yates) parcial
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [pool[i], pool[j]] = [pool[j], pool[i]];
    }

    emptySlots.forEach((slot, k) => {
      if (pool[k]) team[slot] = pool[k];
    });
    saveTeamToStorage();
    renderTeamGrid();
    refreshSearchList();
  };

  const getSelectedNames = () => team.filter(Boolean).map(p => p.name.toLowerCase());

  /* ============================================================
     GESTIÓ MODAL DE CERCA
     ============================================================ */

  /* ============================================================
     RECOMANACIÓ AMB IA (UI NOVA)
     ============================================================ */
  let currentRecommendation = null;

  const openRecommendModal = async () => {
    const teamIds = team.filter(Boolean).map(p => p.pokedex_id);

    if (teamIds.length === 0) {
      alert("Afegeix almenys un Pokémon a l'equip per obtenir recomanacions.");
      return;
    }

    try {
      // Estat de càrrega
      recommendResults.style.display = "none";
      recommendStatus.style.display = "block";
      recommendStatus.innerHTML = "<p style='text-align: center; padding: 40px;'>🔮 Consultant l'Oracle Pokémon...</p>";
      recommendModal.style.display = "block";

      const response = await fetch(`${API_BASE}/ai/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team_ids: teamIds })
      });

      if (!response.ok) throw new Error("Error en la petició d'IA");

      const data = await response.json();

      if (!data.success || !data.recommendations || data.recommendations.length === 0) {
        recommendStatus.innerHTML = "<p style='text-align:center'>No s'han trobat recomanacions.</p>";
        return;
      }

      const topRec = data.recommendations[0];
      currentRecommendation = topRec;

      // Actualitzar UI del modal
      recommendSprite.src = topRec.sprite_url;
      document.getElementById("rec-name").textContent = topRec.name.toUpperCase();
      document.getElementById("rec-id").textContent = padId(topRec.pokedex_id);
      document.getElementById("rec-score").textContent = Math.round(topRec.score);

      const typesContainer = document.getElementById("rec-types");
      typesContainer.innerHTML = "";
      topRec.types.forEach(t => {
        const badge = document.createElement("span");
        badge.className = "rec-pill";
        badge.textContent = t;
        const rgb = TYPE_RGB[t.toLowerCase()] || [100,100,100];
        badge.style.backgroundColor = `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.5)`;
        badge.style.border = `1px solid rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.8)`;
        typesContainer.appendChild(badge);
      });

      const reasoningList = document.getElementById("rec-reasoning");
      reasoningList.innerHTML = topRec.reasoning.slice(0, 5).map(r => `<li>${r}</li>`).join('');

      const warningsContainer = document.getElementById('rec-warnings-container');
      const warningsList = document.getElementById('rec-warnings');
      if (topRec.warnings && topRec.warnings.length > 0) {
          warningsList.innerHTML = topRec.warnings.map(w => `<li>${w}</li>`).join('');
          warningsContainer.style.display = 'block';
      } else {
          warningsContainer.style.display = 'none';
      }

      document.getElementById("bar-def").style.width = `${topRec.scores.defensive}%`;
      document.getElementById("bar-off").style.width = `${topRec.scores.offensive}%`;
      document.getElementById("bar-div").style.width = `${topRec.scores.diversity}%`;

      // Botó Afegir
      const actionContainer = document.getElementById("rec-action-container");
      const acceptBtn = document.getElementById("accept-rec-btn");
      const isTeamFull = teamIds.length >= 6;

      if (isTeamFull) {
        actionContainer.style.display = "none";
      } else {
        actionContainer.style.display = "block";
        const newBtn = acceptBtn.cloneNode(true);
        acceptBtn.parentNode.replaceChild(newBtn, acceptBtn);
        newBtn.addEventListener("click", addRecommendationToTeam);
      }

      recommendStatus.style.display = "none";
      recommendResults.style.display = "block";

    } catch (error) {
      console.error("Error recomanació:", error);
      recommendResults.style.display = "none";
      recommendStatus.style.display = "block";
      recommendStatus.innerHTML = `<p style='text-align: center; color:#ef4444'>Error: ${error.message}</p>`;
    }
  };

  const addRecommendationToTeam = () => {
    if (!currentRecommendation) return;
    const emptyIndex = team.findIndex(slot => slot === null);

    if (emptyIndex !== -1) {
        team[emptyIndex] = currentRecommendation;
        saveTeamToStorage();
        renderTeamGrid();
        closeRecommendModal();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const closeRecommendModal = () => recommendModal.style.display = "none";
  const updateRecommendButtonState = () => {
    const teamSize = team.filter(Boolean).length;
    recommendBtn.disabled = !(teamSize >= 1 && teamSize < 6);
  };

  /* ============================================================
     LISTENERS D'EVENTS
     ============================================================ */

  // Tancar modals en fer clic fora
  document.querySelectorAll(".modal").forEach(modal => {
    modal.addEventListener("click", e => {
      if (e.target === modal) modal.style.display = "none";
    });
  });

  // Events Cerca
  searchCloseBtn.addEventListener("click", closeSearch);



  // Events Recomanació
  recommendBtn.addEventListener("click", openRecommendModal);
  recommendCloseBtn.addEventListener("click", closeRecommendModal);

  // Events Accions
  randomBtn.addEventListener("click", fillRandomTeam);
  clearBtn.addEventListener("click", clearTeam);
  addBtn.addEventListener("click", () => {
    const idx = team.findIndex(v => v === null);
    if (idx !== -1) openSearch(idx);
  });

  /* ============================================================
     INICIALITZACIÓ
     ============================================================ */
  renderTeamGrid();
  console.log("Aplicació inicialitzada.");


/* ============================================================
     GESTIÓ D'USUARIS (FRONTEND MOCK)
     ============================================================ */

// Elements Generals
const loginBtn = document.getElementById("login-btn");
const authModal = document.getElementById("auth-modal");
const authCloseBtn = authModal.querySelector(".close-btn");
const userNameDisplay = document.getElementById("user-name-display");

// Elements de Vistes
const viewLogin = document.getElementById("view-login");
const viewRegister = document.getElementById("view-register");
const goToRegisterBtn = document.getElementById("go-to-register");
const goToLoginBtn = document.getElementById("go-to-login");

// Elements de Formularis
const loginForm = document.getElementById("form-login");
const loginInput = document.getElementById("login-user");

const registerForm = document.getElementById("form-register");
const regInputUser = document.getElementById("reg-user");

// 1. Comprovar si ja estem loguejats
const checkLoginStatus = () => {
    const savedUser = localStorage.getItem("pokeUser");

    if (savedUser) {
        userNameDisplay.textContent = savedUser;
        loginBtn.classList.add("logged-in");
        loginBtn.title = "Tancar Sessió";
    } else {
        userNameDisplay.textContent = "Login";
        loginBtn.classList.remove("logged-in");
        loginBtn.title = "Iniciar Sessió";
    }
};
// --- ELEMENTS DEL MODAL DE PERFIL ---
const profileModal = document.getElementById("profile-modal");
const profileCloseBtn = profileModal.querySelector(".close-btn");
const profileUsername = document.getElementById("profile-username");
const profileLogoutBtn = document.getElementById("profile-logout-btn");
const userTeamsList = document.getElementById("user-teams-list");

// 2. Obrir Modal (MODIFICAT)
loginBtn.addEventListener("click", () => {
    const savedUser = localStorage.getItem("pokeUser");

    if (savedUser) {
        // Si estem loguejats -> OBRIM EL DASHBOARD
        openProfileModal(savedUser);
    } else {
        // Si no -> OBRIM LOGIN
        viewLogin.classList.remove("hidden");
        viewRegister.classList.add("hidden");
        authModal.style.display = "block";
        loginInput.focus();
    }
});

// Funció per obrir i renderitzar el perfil
const openProfileModal = (username) => {
    profileUsername.textContent = username;

    // Aquí simularem la crida al backend per obtenir equips
    // De moment, fem servir una llista buida []
    const userTeams = [];

    renderUserTeams(userTeams);
    profileModal.style.display = "block";
};

// Funció per pintar la llista d'equips
const renderUserTeams = (teams) => {
    userTeamsList.innerHTML = "";

    if (teams.length === 0) {
        // --- ESTAT BUIT (El que demanaves) ---
        userTeamsList.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📂</span>
                <p>Encara no tens cap equip guardat.</p>
                <button id="create-first-team-btn" class="ui-btn primary small">
                    Crear el meu primer equip
                </button>
            </div>
          `;

        // Donem funcionalitat al botó de l'estat buit
        document.getElementById("create-first-team-btn").addEventListener("click", () => {
            profileModal.style.display = "none"; // Tanquem modal
            // Ja estem al builder, així que l'usuari pot començar a editar
        });

    } else {
        // (Aquí aniria el codi per pintar la llista quan tinguem equips)
        userTeamsList.textContent = "Aquí sortiran els teus equips...";
    }
};

// --- LOGOUT DES DEL PERFIL ---
profileLogoutBtn.addEventListener("click", () => {
    if(confirm("Segur que vols sortir?")) {
        localStorage.removeItem("pokeUser");
        checkLoginStatus();
        profileModal.style.display = "none";
    }
});

// Tancar el modal de perfil
profileCloseBtn.addEventListener("click", () => {
    profileModal.style.display = "none";
});

// Tancar si cliquem fora
window.addEventListener("click", (e) => {
    if (e.target === profileModal) profileModal.style.display = "none";
    // ... (els altres modals)
});



// 3. Navegació entre Login i Registre
goToRegisterBtn.addEventListener("click", (e) => {
    e.preventDefault(); // Evita que l'enllaç recarregui la pàgina
    viewLogin.classList.add("hidden");
    viewRegister.classList.remove("hidden");
    regInputUser.focus();
});

goToLoginBtn.addEventListener("click", (e) => {
    e.preventDefault();
    viewRegister.classList.add("hidden");
    viewLogin.classList.remove("hidden");
    loginInput.focus();
});

// 4. Tancar Modal
authCloseBtn.addEventListener("click", () => {
    authModal.style.display = "none";
});

// 5. Processar LOGIN
loginForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const username = loginInput.value.trim();
    // Agafem la contrasenya del nou input
    const password = document.getElementById("login-pass").value.trim();

    // Validem que tots dos camps tinguin text
    if (username && password) {
        localStorage.setItem("pokeUser", username);

        checkLoginStatus();
        authModal.style.display = "none";

        // Netejem el formulari
        loginInput.value = "";
        document.getElementById("login-pass").value = "";
    } else {
        alert("Si us plau, introdueix usuari i contrasenya.");
    }
});

// 6. Processar REGISTRE (Simulat)
registerForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const username = regInputUser.value.trim();
    const password = document.getElementById("reg-pass").value.trim();

    // Validació simple (només comprovem que hi hagi usuari i contrasenya)
    if (username && password) {
        // Simulem que es crea el compte i fem login directe
        localStorage.setItem("pokeUser", username);

        alert("Compte creat correctament! Benvingut/da.");

        checkLoginStatus();
        authModal.style.display = "none";

        // Netejem el formulari (només usuari i pass)
        regInputUser.value = "";
        document.getElementById("reg-pass").value = "";
    }
});

// Executar al principi
checkLoginStatus();

/* ============================================================
     GESTIÓ DE GUARDAR EQUIP (NOU)
     ============================================================ */
const saveTeamBtn = document.getElementById("save-team-btn");
const teamNameInput = document.getElementById("team-name-input");

saveTeamBtn.addEventListener("click", () => {
    // 1. Validacions
    const currentUser = localStorage.getItem("pokeUser");
    if (!currentUser) {
        alert("Has d'iniciar sessió per guardar equips!");
        // Obre el modal de login automàticament
        loginBtn.click();
        return;
    }

    const activePokemons = team.filter(Boolean);
    if (activePokemons.length === 0) {
        alert("L'equip està buit! Afegeix almenys un Pokémon.");
        return;
    }

    const teamName = teamNameInput.value.trim() || "Equip sense nom";

    // 2. Crear l'objecte de l'equip
    const newTeam = {
        id: Date.now(), // ID únic (timestamp)
        name: teamName,
        members: team, // L'array de 6 slots actual
        createdAt: new Date().toISOString()
    };

    // 3. Guardar al LocalStorage (Simulant BBDD)
    // Recuperem els equips existents o creem una llista nova
    let userTeams = JSON.parse(localStorage.getItem(`teams_${currentUser}`)) || [];

    // Afegim el nou equip
    userTeams.push(newTeam);

    // Guardem la llista actualitzada
    localStorage.setItem(`teams_${currentUser}`, JSON.stringify(userTeams));

    // 4. Feedback a l'usuari
    alert(`Equip "${teamName}" guardat correctament!`);

    // Opcional: Netejar l'equip actual després de guardar?
    // clearTeam();
});

/* ============================================================
     DATA GRID (TAULA DE CERCA AMB FILTRES JS)
     ============================================================ */

// Estat intern de la taula
let tableState = {
    filterId: "",
    filterName: "",
    filterTypes: [], // <-- CANVI: Ara és un array buit []
    minStats: { hp: 0, attack: 0, defense: 0, special_attack: 0, special_defense: 0, speed: 0 },
    currentPage: 1,  // <--- NOU: Pàgina actual (comença a 1)
    limit: 50,       // <--- NOU: Límit per pàgina
    sortKey: "id", // Per defecte ordenat per ID
    sortAsc: true
};

    /* ============================================================
         GESTIÓ DEL FILTRE DE TIPUS (POPUP)
         ============================================================ */
    const typeFilterBtn = document.getElementById("type-filter-btn");
    const typePopup = document.getElementById("type-filter-popup");
    const typeGridContainer = document.getElementById("type-grid-container");
    const clearTypesBtn = document.getElementById("clear-types-btn");

    // 1. Generar els botons de tipus
    const renderTypeFilterOptions = () => {
        typeGridContainer.innerHTML = "";

        // Itere sobre tots els tipus disponibles (de la teva constant TYPE_RGB)
        Object.keys(TYPE_RGB).forEach(type => {
            const btn = document.createElement("div");
            btn.className = "type-option";
            btn.textContent = type;

            // Si està seleccionat, li posem la classe active i el color
            if (tableState.filterTypes.includes(type)) {
                btn.classList.add("active");
                const rgb = typeToRGB(type);
                btn.style.backgroundColor = `rgb(${rgb})`;
                btn.style.borderColor = `rgb(${rgb})`;
            }

            // Click per activar/desactivar
            btn.addEventListener("click", (e) => {
                e.stopPropagation(); // Evita tancar el popup
                toggleTypeFilter(type);
            });

            typeGridContainer.appendChild(btn);
        });
    };



    const updateTypeButtonText = () => {
        const count = tableState.filterTypes.length;
        if (count === 0) {
            typeFilterBtn.textContent = "Tots els tipus ▾";
            typeFilterBtn.style.color = "";
        } else {
            typeFilterBtn.textContent = `${count} seleccionats ▾`;
            typeFilterBtn.style.color = "#3b82f6";
        }
    };

    // 3. Obrir/Tancar Popup
    typeFilterBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        typePopup.classList.toggle("hidden");
        renderTypeFilterOptions(); // Renderitzem al obrir per tenir l'estat correcte
    });

    // 4. Netejar Filtres
    clearTypesBtn.addEventListener("click", () => {
        tableState.filterTypes = [];
        updateTypeButtonText();
        renderTypeFilterOptions();
        renderTable();
    });

    // Tancar si cliquem fora
    document.addEventListener("click", (e) => {
        if (!typePopup.contains(e.target) && e.target !== typeFilterBtn) {
            typePopup.classList.add("hidden");
        }
    });

// Elements
const tableBody = document.getElementById("table-body");
const filterIdInput = document.getElementById("filter-id");
const filterNameInput = document.getElementById("filter-name");
// Inputs d'Stats
    const filterStatsInputs = {
        hp: document.getElementById("filter-hp"),
        attack: document.getElementById("filter-atk"),
        defense: document.getElementById("filter-def"),
        special_attack: document.getElementById("filter-spa"),
        special_defense: document.getElementById("filter-spd"),
        speed: document.getElementById("filter-spe")
    };

const resultsCount = document.getElementById("results-count");
const sortHeaders = document.querySelectorAll(".sortable");

// --- FUNCIÓ PRINCIPAL: CONSULTAR API I PINTAR ---
    const renderTable = async () => {
        // 1. Feedback visual (Spinner)
        tableBody.innerHTML = '<tr><td colspan="12" style="text-align:center; padding:20px;">🔄 Carregant dades...</td></tr>';

        try {
            // 2. CONSULTA AL BACKEND
            const data = await fetchPokemons(tableState);

            // 3. EXTRAIEM DADES (Adaptació al nou format)
            // Si el backend retorna { total, results }, fem servir això.
            // Si per algun motiu retorna array (versió antiga), fem fallback.
            const results = Array.isArray(data) ? data : (data.results || []);
            const totalCount = data.total !== undefined ? data.total : results.length;

            // Actualitzem variable local (opcional, per depuració)
            mockPokemonData = results;

            // 4. Netejem taula
            tableBody.innerHTML = "";

            if (results.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="12" style="text-align:center; padding:20px;">No s\'han trobat Pokémon amb aquests filtres.</td></tr>';
                resultsCount.textContent = "0 resultats";
                return;
            }

            // 5. PINTAR FILES (Iterem sobre 'results')
            results.forEach(p => {
                const tr = document.createElement("tr");
                const s = p.stats || { hp:0, attack:0, defense:0, special_attack:0, special_defense:0, speed:0 };

                const typesHtml = p.types.map(t => {
                    const rgb = typeToRGB(t.toLowerCase());
                    return `<span style="background:rgba(${rgb}, 0.3); border:1px solid rgb(${rgb}); color:#fff; padding:2px 6px; border-radius:4px; font-size:10px; margin-right:4px; font-weight:bold; text-transform:uppercase;">${t}</span>`;
                }).join("");

                tr.innerHTML = `
                  <td class="col-img"><img src="${p.sprite_url}" loading="lazy"></td>
                  <td class="col-id">#${padId(p.pokedex_id)}</td>
                  <td class="col-name">${capitalize(p.name)}</td>
                  <td class="col-type">${typesHtml}</td>
                  <td class="col-stat">${s.hp}</td>
                  <td class="col-stat">${s.attack}</td>
                  <td class="col-stat">${s.defense}</td>
                  <td class="col-stat">${s.special_attack}</td>
                  <td class="col-stat">${s.special_defense}</td>
                  <td class="col-stat">${s.speed}</td>
                  <td class="col-action">
                      <button class="add-row-btn" title="Afegir">+</button>
                  </td>
                `;
                tr.addEventListener("click", () => selectPokemonFromTable(p));
                tableBody.appendChild(tr);
            });

            // ACTUALITZAR LA PAGINACIÓ I EL TEXT
            const start = (tableState.currentPage - 1) * tableState.limit + 1;
            const end = Math.min(start + results.length - 1, totalCount);

            if (totalCount > 0) {
                resultsCount.textContent = `Mostrant ${start}-${end} de ${totalCount} Pokémon`;
            } else {
                resultsCount.textContent = "0 resultats";
            }

            renderPagination(totalCount); // <--- AFEGEIX AIXÒ

        } catch (error) {
            console.error("Error al renderTable:", error);
            tableBody.innerHTML = '<tr><td colspan="12" style="color:red; text-align:center;">Error connectant amb el servidor.</td></tr>';
        }
    };

const selectPokemonFromTable = (pokemon) => {
    if (editingIndex !== null) {
        team[editingIndex] = pokemon;
        saveTeamToStorage();
        renderTeamGrid();
        closeSearch();
    }
};

// --- LISTENERS DE LA TAULA (Tots criden al Backend) ---

    // Funció Debounce (per no saturar el servidor)
    const debouncedRender = debounce(() => {
        renderTable();
    }, 400); // Espera 400ms abans de demanar

    // 1. Text Inputs
    filterIdInput.addEventListener("input", (e) => {
        tableState.filterId = e.target.value.trim();
        tableState.currentPage = 1;
        debouncedRender();
    });

    filterNameInput.addEventListener("input", (e) => {
        tableState.filterName = e.target.value.trim();
        tableState.currentPage = 1;
        debouncedRender();
    });

    // 2. Stats Inputs
    Object.keys(filterStatsInputs).forEach(key => {
        filterStatsInputs[key].addEventListener("input", (e) => {
            const val = parseInt(e.target.value) || 0;
            tableState.currentPage = 1;
            tableState.minStats[key] = val;
            debouncedRender();
        });
    });

    // 3. Tipus (Aquí no cal debounce perquè és un clic, volem resposta ràpida)
    const toggleTypeFilter = (type) => {
        if (tableState.filterTypes.includes(type)) {
            tableState.filterTypes = tableState.filterTypes.filter(t => t !== type);
        } else {
            tableState.filterTypes.push(type);
        }

        tableState.currentPage = 1;
        updateTypeButtonText();
        renderTypeFilterOptions();

        renderTable(); // Cridem directe
    };

    // 4. Ordenació
    sortHeaders.forEach(th => {
        th.addEventListener("click", () => {
            const key = th.dataset.key;
            if (tableState.sortKey === key) {
                tableState.sortAsc = !tableState.sortAsc;
            } else {
                tableState.sortKey = key;
                // Si ordenem per stats, per defecte descendent (major a menor)
                const isStat = ['hp','attack','defense','special_attack','special_defense','speed'].includes(key);
                tableState.sortAsc = !isStat;
            }
            // --- AFEGEIX AQUESTA LÍNIA ---
            tableState.currentPage = 1;
            // -----------------------------

            renderTable(); // Cridem directe
        });
    });

});