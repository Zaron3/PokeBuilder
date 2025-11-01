/* ============================================================
   ⚡️ POKEBUILDER — APP PRINCIPAL (mode fosc fix + backend real)
   ============================================================ */
document.addEventListener("DOMContentLoaded", async () => {

  /* ============================================================
     ⚙️ CONFIGURACIÓ BACKEND
     ============================================================ */
  const API_BASE = "http://127.0.0.1:8000/api/v1";

  /* ============================================================
     📦 FUNCIONS BACKEND
     ============================================================ */
  async function fetchPokemons(query) {
    try {
      const res = await fetch(`${API_BASE}/pokemon/search?q=${query}`);
      if (!res.ok) throw new Error("Error de connexió amb l'API");
      return await res.json();
    } catch (err) {
      console.error("❌ Error carregant Pokémon:", err);
      return [];
    }
  }

  // 🔄 Carrega tots els Pokémon (reals, fent servir la mateixa API)
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
    console.log(`✅ Carregats ${all.length} Pokémon reals des del backend`);
    return all;
  }

  /* ============================================================
     🎨 COLORS PER TIPUS
     ============================================================ */
  const TYPE_RGB = {
    normal:[168,168,120], fire:[240,128,48], water:[104,144,240],
    electric:[248,208,48], grass:[120,200,80], ice:[152,216,216],
    fighting:[192,48,40], poison:[160,64,160], ground:[224,192,104],
    flying:[168,144,240], psychic:[248,88,136], bug:[168,184,32],
    rock:[184,160,56], ghost:[112,88,152], dragon:[112,56,248],
    dark:[112,88,72], steel:[184,184,208], fairy:[238,153,172]
  };

  const getSpriteUrl = id =>
    `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png`;

  const padId = n => `#${String(n).padStart(3, "0")}`;
  const typeToRGB = t => {
    const arr = TYPE_RGB[t] || [200,200,200];
    return `${arr[0]}, ${arr[1]}, ${arr[2]}`;
  };

  /* ============================================================
     ⚙️ ESTAT GLOBAL
     ============================================================ */
  const team = Array(6).fill(null);
  let editingIndex = null;

  /* ============================================================
     🧭 DOM ELEMENTS
     ============================================================ */
  const teamGrid       = document.getElementById("team-grid");
  const carouselInner  = document.getElementById("carousel-inner");

  const searchModal    = document.getElementById("pokemon-modal");
  const searchBar      = document.getElementById("search-bar");
  const searchCloseBtn = searchModal.querySelector(".close-btn");
  const pokemonListUl  = document.getElementById("pokemon-list");

  const recommendModal   = document.getElementById("recommend-modal");
  const recommendBtn     = document.getElementById("recommend-btn");
  const recommendCloseBtn= recommendModal.querySelector(".close-btn");
  const recommendSprite  = document.getElementById("recommend-sprite");
  const recommendText    = document.getElementById("recommend-text");

  const randomBtn = document.getElementById("random-btn");
  const clearBtn  = document.getElementById("clear-btn");
  const addBtn    = document.getElementById("add-btn");

  /* ============================================================
     🧩 DADES DEL BACKEND REAL
     ============================================================ */
  let mockPokemonData = [];
  try {
    mockPokemonData = await fetchAllPokemons();
  } catch (e) {
    console.error("Error carregant Pokémon des de FastAPI:", e);
  }

  if (mockPokemonData.length === 0) {
    console.warn("⚠️ No s'han carregat Pokémon. Comprova el backend.");
  }

  /* ============================================================
     🧱 RENDER DE L’EQUIP
     ============================================================ */
  const renderTeamGrid = () => {
    teamGrid.innerHTML = "";

    team.forEach((poke, idx) => {
      if (!poke) {
        const add = document.createElement("div");
        add.className = "add-card";
        add.innerHTML = `<div class="plus">＋</div><div class="txt">Afegir Pokémon</div>`;
        add.addEventListener("click", () => openSearch(idx));
        teamGrid.appendChild(add);
      } else {
        teamGrid.appendChild(buildTopCard(poke, idx));
      }
    });

    updateRecommendState();
    rebuildCarousel();
  };

  const buildTopCard = (poke, idx) => {
    const STAT_NAMES = {
      hp: "HP",
      attack: "Attack",
      defense: "Defense",
      special_attack: "Sp. Atk",
      special_defense: "Sp. Def",
      speed: "Speed"
    };


    const type = poke.types ? poke.types[0] : "normal";
    const rgb = typeToRGB(type.toLowerCase());
    const card = document.createElement("div");
    card.className = "poke-card";
    card.style.setProperty("--type-rgb", rgb);

    const inner = document.createElement("div");
    inner.className = "card-inner"; // Mantenim inner per si volem altres efectes

    const front = document.createElement("div");
    front.className = "card-face card-front";

    // --- NOU: CONTENIDOR DELS BOTONS D'ACCIÓ ---
    const actions = document.createElement("div");
    actions.className = "card-actions";

    // Botó d'ELIMINAR
    // Botó d'ELIMINAR
    const removeBtn = document.createElement("button");
    removeBtn.className = "action-btn remove";
    removeBtn.title = `Eliminar ${poke.name}`;
    // Afegim una icona SVG de "creu"
    removeBtn.innerHTML = `
      <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
        <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
      </svg>
    `;
    removeBtn.addEventListener("click", e => {
      e.stopPropagation(); // Evita que el clic es propagui a la targeta
      removeFromTeam(idx);
    });

    // Botó d'EDITAR
    const editBtn = document.createElement("button");
    editBtn.className = "action-btn edit";
    editBtn.title = `Editar ${poke.name}`;
    // Afegim la teva imatge PNG
    editBtn.innerHTML = `
      <img src="src/edit-icon.png" alt="Editar" class="action-icon-img">
    `;
    editBtn.addEventListener("click", e => {
      e.stopPropagation(); // Evita que el clic es propagui
      // Aquí hauríem d'obrir un modal d'edició detallada
      // De moment, farem que obri el modal de cerca com un "canvi ràpid"
      openSearch(idx);
    });

    actions.append(removeBtn, editBtn); // Afegim els botons al contenidor d'accions
    front.appendChild(actions); // Afegim el contenidor d'accions a la cara frontal
    // --- FI NOU ---


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

    const name = document.createElement("div");
    name.className = "card-name";
    name.textContent = poke.name;

    const id = document.createElement("div");
    id.className = "card-id";
    id.textContent = padId(poke.pokedex_id);

    title.append(name, id);

    // --- NOU BLOC PER A PÍNDOLES MÚLTIPLES ---
    // 1. Creem un contenidor per a les píndoles
    const typePillContainer = document.createElement("div");
    typePillContainer.className = "type-pill-container";

    // 2. Fem un bucle per cada tipus que tingui el Pokémon
    poke.types.forEach(type => {
      const pill = document.createElement("div");
      pill.className = "type-pill";
      pill.textContent = type.toUpperCase();

      // 3. Calculem i establim el color PER A CADA PÍNDOLA
      //    Això sobreescriu el color de la targeta (que només tenia el primer tipus)
      const rgb = typeToRGB(type.toLowerCase());
      pill.style.setProperty("--type-rgb", rgb);

      typePillContainer.appendChild(pill); // Afegim la píndola al contenidor
    });
    // --- FI DEL NOU BLOC ---

    body.append(title, typePillContainer); // Afegim el contenidor (amb les píndoles a dins) al body
    front.append(head, body);

    // Eliminem la 'card-back' i el seu contingut, ja no la necessitem
    // const back = document.createElement("div");
    // back.className = "card-face card-back";
    // back.innerHTML = `<div class="back-body">Clica per eliminar</div>`;

    // --- NOU: CARA POSTERIOR (Estadístiques) ---
    const back = document.createElement("div");
    back.className = "card-face card-back";

    // Títol
    const statsTitle = document.createElement("h4");
    statsTitle.className = "stats-title";
    statsTitle.textContent = "Base Stats";
    back.appendChild(statsTitle);

    // Llista d'Stats
    const statsList = document.createElement("ul");
    statsList.className = "stats-list";

    // Assegura't que el teu 'poke.stats' del backend tingui aquest format
    if (poke.stats) {
      const statsInOrder = [
        ['hp', poke.stats.hp],
        ['attack', poke.stats.attack],
        ['defense', poke.stats.defense],
        ['special_attack', poke.stats.special_attack],
        ['special_defense', poke.stats.special_defense],
        ['speed', poke.stats.speed]
      ];

      for (const [statName, statValue] of statsInOrder) {
        const li = document.createElement("li");
        li.innerHTML = `
          <span class="stat-name">${STAT_NAMES[statName] || statName}</span>
          <span class="stat-value">${statValue}</span>
        `;
        statsList.appendChild(li);
      }
    }
    back.appendChild(statsList);

    inner.append(front, back); // Només afegim la cara frontal
    card.appendChild(inner);

    // Eliminem l'event listener de clic a la targeta, ja que els botons ja ho gestionen
    // card.addEventListener("click", () => removeFromTeam(idx));
    return card;
  };

  /* ============================================================
     ❌ GESTIÓ D’EQUIP
     ============================================================ */
  const removeFromTeam = idx => {
    team[idx] = null;
    renderTeamGrid();
    refreshSearchList();
  };

  const clearTeam = () => {
    for (let i = 0; i < team.length; i++) team[i] = null;
    renderTeamGrid();
    refreshSearchList();
  };

  const fillRandomTeam = () => {
    const emptySlots = team.map((v,i)=>v?null:i).filter(v=>v!==null);
    const selected = new Set(getSelectedNames());
    const pool = mockPokemonData.filter(p=>!selected.has(p.name.toLowerCase()));

    for (let i=pool.length-1;i>0;i--){
      const j=Math.floor(Math.random()*(i+1));
      [pool[i],pool[j]]=[pool[j],pool[i]];
    }

    emptySlots.forEach((slot,k)=>{
      if(pool[k]) team[slot]=pool[k];
    });

    renderTeamGrid();
    refreshSearchList();
  };

  /* ============================================================
     🔍 MODAL DE CERCA
     ============================================================ */
  const openSearch = index => {
    editingIndex = index;
    searchBar.value = "";
    populateList(mockPokemonData);
    searchModal.style.display = "block";
    searchBar.focus();
  };
  const closeSearch = () => {
    searchModal.style.display = "none";
    editingIndex = null;
  };

  const getSelectedNames = () => team.filter(Boolean).map(p=>p.name.toLowerCase());

  const refreshSearchList = async () => {
    const query = (searchBar.value || "").toLowerCase().trim();
    const selected = new Set(getSelectedNames());
    let list = [];

    if (query.length >= 2) {
      list = await fetchPokemons(query);
    } else {
      list = mockPokemonData;
    }

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
     💡 RECOMANACIÓ
     ============================================================ */
  const openRecommendModal = () => {
    const selected = new Set(getSelectedNames());
    const candidates = mockPokemonData.filter(p => !selected.has(p.name.toLowerCase()));
    if (candidates.length === 0) return alert("No hi ha Pokémon per recomanar.");
    const recommended = candidates[Math.floor(Math.random() * candidates.length)];

    recommendSprite.src = recommended.sprite_url;
    recommendSprite.alt = recommended.name;
    recommendText.textContent = `Et recomanem afegir ${recommended.name} (${padId(recommended.pokedex_id)}).`;
    recommendModal.style.display = "block";
  };
  const closeRecommendModal = () => recommendModal.style.display = "none";
  const updateRecommendState = () => recommendBtn.disabled = !(team.filter(Boolean).length >= 5);

  /* ============================================================
     🌀 CARRUSEL 3D
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
     🔗 EVENTS
     ============================================================ */
  document.querySelectorAll(".modal").forEach(modal => {
    modal.addEventListener("click", e => {
      if (e.target === modal) modal.style.display = "none";
    });
  });

  searchCloseBtn.addEventListener("click", closeSearch);
  searchBar.addEventListener("input", refreshSearchList);
  recommendBtn.addEventListener("click", openRecommendModal);
  recommendCloseBtn.addEventListener("click", closeRecommendModal);
  randomBtn.addEventListener("click", fillRandomTeam);
  clearBtn.addEventListener("click", clearTeam);
  addBtn.addEventListener("click", () => {
    const idx = team.findIndex(v => v === null);
    if (idx !== -1) openSearch(idx);
  });

  /* ============================================================
     🚀 INICIALITZACIÓ
     ============================================================ */
  renderTeamGrid();
  console.log("✅ PokeBuilder connectat i mostrant resultats reals de FastAPI!");
});
