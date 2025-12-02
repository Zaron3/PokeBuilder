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
  
  // Cerca bàsica per prefix
  async function fetchPokemons(query) {
    try {
      const res = await fetch(`${API_BASE}/pokemon/search?q=${query}`);
      if (!res.ok) throw new Error("Error de connexió amb l'API");
      return await res.json();
    } catch (err) {
      console.error("Error carregant Pokémon:", err);
      return [];
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
  }

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

  /* ============================================================
     ESTAT GLOBAL
     ============================================================ */
  let savedData = localStorage.getItem("currentTeam");
  let team = savedData ? JSON.parse(savedData) : Array(6).fill(null);
  let editingIndex = null;
  
  // Dades en memòria per a la cerca ràpida
  let mockPokemonData = [];

  /* ============================================================
     ELEMENTS DEL DOM
     ============================================================ */
  // Equip i Carrusel
  const teamGrid       = document.getElementById("team-grid");
  const carouselInner  = document.getElementById("carousel-inner");

  // Modal Cerca
  const searchModal    = document.getElementById("pokemon-modal");
  const searchBar      = document.getElementById("search-bar");
  const searchCloseBtn = searchModal.querySelector(".close-btn");
  const pokemonListUl  = document.getElementById("pokemon-list");
  
  // Controls d'Ordenació (Cerca)
  const sortStatEl     = document.getElementById("sort-stat");
  const sortOrderEl    = document.getElementById("sort-order");
  const applySortBtn   = document.getElementById("apply-sort-btn");

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
     CÀRREGA INICIAL DE DADES
     ============================================================ */
  try {
    mockPokemonData = await fetchAllPokemons();
  } catch (e) {
    console.error("Error critical carregant dades:", e);
  }

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
    renderTeamGrid();
    refreshSearchList(); // Actualitza la llista per desbloquejar el Pokémon eliminat
  };

  const clearTeam = () => {
    team = Array(6).fill(null);
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

    renderTeamGrid();
    refreshSearchList();
  };

  const getSelectedNames = () => team.filter(Boolean).map(p => p.name.toLowerCase());

  /* ============================================================
     GESTIÓ MODAL DE CERCA
     ============================================================ */
  const openSearch = index => {
    editingIndex = index;
    searchBar.value = "";
    // Resetejar els filtres d'ordre visualment
    if (sortStatEl) sortStatEl.value = "";
    if (sortOrderEl) sortOrderEl.value = "desc";
    
    populateList(mockPokemonData);
    searchModal.style.display = "block";
    searchBar.focus();
    document.body.style.overflow = 'hidden';
  };

  const closeSearch = () => {
    searchModal.style.display = "none";
    editingIndex = null;
    document.body.style.overflow = '';
  };

  const refreshSearchList = async () => {
    const query = (searchBar.value || "").toLowerCase().trim();
    const selected = new Set(getSelectedNames());
    let list = [];

    if (query.length >= 2) {
      list = await fetchPokemons(query);
    } else {
      list = mockPokemonData;
    }

    // Filtrem els que ja estan a l'equip
    list = list.filter(p => !selected.has(p.name.toLowerCase()));
    populateList(list);
  };

  const populateList = pokemons => {
    pokemonListUl.innerHTML = "";
    pokemons.forEach(pokemon => {
      const li = document.createElement("li");
      li.innerHTML = `
        <img src="${pokemon.sprite_url}" alt="${pokemon.name}" />
        <span>${padId(pokemon.pokedex_id)} ${pokemon.name}</span>
        <small>${pokemon.types.join(", ")}</small>
      `;
      li.addEventListener("click", () => {
        if (editingIndex !== null) {
          team[editingIndex] = pokemon;
          renderTeamGrid();
          closeSearch();
        }
      });
      pokemonListUl.appendChild(li);
    });
  };

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
  searchBar.addEventListener("input", refreshSearchList);

  // Events Ordenació
  applySortBtn.addEventListener("click", async () => {
    const stat = sortStatEl.value;
    const order = sortOrderEl.value;

    if (!stat) {
      alert("Selecciona una estadística per ordenar.");
      return;
    }

    pokemonListUl.innerHTML = '<li style="justify-content:center;">⏳ Carregant...</li>';
    const sortedList = await fetchSortedPokemons(stat, order);
    searchBar.value = ""; 
    populateList(sortedList);
  });

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
});