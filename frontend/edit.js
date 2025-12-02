/* ============================================================
   POKEBUILDER — LÒGICA DE L'EDITOR
   Gestiona l'edició del Pokémon: moviments, habilitats, 
   naturaleses i objectes.
   ============================================================ */

const API_BASE = "http://127.0.0.1:8000/api/v1";

// Llista estàndard de naturaleses
const NATURES = [
  "Adamant", "Bashful", "Bold", "Brave", "Calm", "Careful", "Docile",
  "Gentle", "Hardy", "Hasty", "Impish", "Jolly", "Lax", "Lonely",
  "Mild", "Modest", "Naive", "Naughty", "Quiet", "Quirky", "Rash",
  "Relaxed", "Sassy", "Serious", "Timid"
];

// --- DADES HARDCODED PER PROVES (MOCK) ---
// Aquestes dades es faran servir si l'API falla o si el Pokémon
// no té moviments/habilitats a la base de dades.
const MOCK_DATA = {
  abilities: [
    { ability: { name: "intimidate" } },
    { ability: { name: "levitate" } },
    { ability: { name: "static" } },
    { ability: { name: "pressure" } },
    { ability: { name: "flash-fire" } },
    { ability: { name: "overgrow" } },
    { ability: { name: "blaze" } },
    { ability: { name: "torrent" } }
  ],
  moves: [
    { move: { name: "protect" } },
    { move: { name: "toxic" } },
    { move: { name: "earthquake" } },
    { move: { name: "thunderbolt" } },
    { move: { name: "ice-beam" } },
    { move: { name: "flamethrower" } },
    { move: { name: "surf" } },
    { move: { name: "psychic" } },
    { move: { name: "shadow-ball" } },
    { move: { name: "roost" } },
    { move: { name: "u-turn" } },
    { move: { name: "knock-off" } },
    { move: { name: "close-combat" } },
    { move: { name: "swords-dance" } },
    { move: { name: "stealth-rock" } },
    { move: { name: "hydro-pump" } },
    { move: { name: "fire-blast" } },
    { move: { name: "solar-beam" } }
  ]
};

/* ============================================================
   GESTIÓ DE L'ESTAT
   ============================================================ */
const editIndex = localStorage.getItem("editIndex");
const savedTeam = JSON.parse(localStorage.getItem("currentTeam") || "[]");
const poke      = savedTeam[editIndex];

// Validar que existeixin dades per evitar errors
if (!poke) {
  alert("Error: No s'ha trobat el Pokémon.");
  window.location.href = "index.html";
}

/* ============================================================
   ELEMENTS DEL DOM
   ============================================================ */
const nameEl    = document.getElementById("edit-name");
const idEl      = document.getElementById("edit-id");
const spriteEl  = document.getElementById("edit-sprite");

const saveBtn   = document.getElementById("save-btn");
const cancelBtn = document.getElementById("cancel-btn");

/* ============================================================
   RENDERITZAT INICIAL
   ============================================================ */
nameEl.textContent = poke.name.toUpperCase();
idEl.textContent   = "#" + String(poke.pokedex_id).padStart(3, "0");
spriteEl.src       = poke.sprite_url;

/* ============================================================
   CÀRREGA DE DADES
   ============================================================ */
async function loadDetails() {
  let data = {};

  try {
    // 1. Intentem connectar amb l'API real
    const res = await fetch(`${API_BASE}/pokemon/${poke.pokedex_id}`);
    
    if (res.ok) {
        data = await res.json();
    } else {
        console.warn("⚠️ API retornada amb error (404/500). Usant dades Mock.");
    }

  } catch (err) {
    console.warn("⚠️ API no disponible (Connection Refused). Usant dades Mock.");
  }

  // --- LÒGICA DE FALLBACK (HARDCODED) ---
  // Si l'objecte data no té moviments (o l'API ha fallat), posem els nostres.
  // Això assegura que "tots els pokémon tinguin moviments per provar".
  
  if (!data.moves || data.moves.length === 0) {
      console.log("ℹ️ Injectant moviments de prova.");
      data.moves = MOCK_DATA.moves;
  }

  if (!data.abilities || data.abilities.length === 0) {
      console.log("ℹ️ Injectant habilitats de prova.");
      data.abilities = MOCK_DATA.abilities;
  }

  // --- RENDERITZAT DELS SELECTS ---
  try {
    // 1. Omplir Moviments (Dropdowns)
    const moves = (data.moves || []).sort((a, b) => {
      const nameA = a.move ? a.move.name : a;
      const nameB = b.move ? b.move.name : b;
      return nameA.localeCompare(nameB);
    });

    [1, 2, 3, 4].forEach((num, idx) => {
      const sel = document.getElementById(`move-${num}`);
      sel.innerHTML = '<option value="">- Cap -</option>';
      
      moves.forEach(m => {
        // Suporta tant format API ({move: {name: ...}}) com string directe
        const mName = m.move ? m.move.name : m;
        const opt = document.createElement("option");
        opt.value = mName;
        opt.textContent = mName.charAt(0).toUpperCase() + mName.slice(1);
        sel.appendChild(opt);
      });

      // Restaurar selecció prèvia si n'hi ha
      if (poke.savedMoves && poke.savedMoves[idx]) {
        sel.value = poke.savedMoves[idx];
      }
    });

    // 2. Omplir Habilitats
    const abSel = document.getElementById("edit-ability");
    abSel.innerHTML = ""; // Neteja inicial
    
    (data.abilities || []).forEach(ab => {
      const aName = ab.ability ? ab.ability.name : ab;
      const opt = document.createElement("option");
      opt.value = aName;
      opt.textContent = aName.charAt(0).toUpperCase() + aName.slice(1);
      abSel.appendChild(opt);
    });
    
    if (poke.savedAbility) {
        abSel.value = poke.savedAbility;
    } else if (abSel.options.length > 0) {
        // Selecciona la primera per defecte si no n'hi ha cap guardada
        abSel.selectedIndex = 0; 
    }

    // 3. Omplir Naturaleses (Sempre estàtiques)
    const natSel = document.getElementById("edit-nature");
    if (natSel.options.length === 0) {
        NATURES.forEach(n => {
          const opt = document.createElement("option");
          opt.value = n;
          opt.textContent = n;
          natSel.appendChild(opt);
        });
    }

    if (poke.savedNature) {
        natSel.value = poke.savedNature;
    }

    // 4. Restaurar Objecte
    if (poke.savedItem) {
      document.getElementById("edit-item").value = poke.savedItem;
    }

  } catch (renderErr) {
    console.error("Error pintant la interfície:", renderErr);
  }
}

/* ============================================================
   LISTENERS D'EVENTS
   ============================================================ */
saveBtn.addEventListener("click", () => {
  // Capturar dades del formulari
  poke.savedMoves   = [1, 2, 3, 4].map(i => document.getElementById(`move-${i}`).value);
  poke.savedAbility = document.getElementById("edit-ability").value;
  poke.savedNature  = document.getElementById("edit-nature").value;
  poke.savedItem    = document.getElementById("edit-item").value;

  // Guardar al LocalStorage (persistència)
  savedTeam[editIndex] = poke;
  localStorage.setItem("currentTeam", JSON.stringify(savedTeam));
  
  // Redirigir a la pàgina principal
  window.location.href = "index.html";
});

cancelBtn.addEventListener("click", () => {
  window.location.href = "index.html";
});

/* ============================================================
   INICIALITZACIÓ
   ============================================================ */
loadDetails();