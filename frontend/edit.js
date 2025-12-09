/* ============================================================
   POKEBUILDER — EDITOR (MODALS UNIFICATS)
   ============================================================ */

const API_BASE = "http://127.0.0.1:8000/api/v1";

const NATURES = [
    "Adamant", "Bashful", "Bold", "Brave", "Calm", "Careful", "Docile",
    "Gentle", "Hardy", "Hasty", "Impish", "Jolly", "Lax", "Lonely",
    "Mild", "Modest", "Naive", "Naughty", "Quiet", "Quirky", "Rash",
    "Relaxed", "Sassy", "Serious", "Timid"
];

// ESTAT GLOBAL
const editIndex = parseInt(localStorage.getItem("editIndex"), 10);
const savedData = localStorage.getItem("pokeBuilder_team");
const savedTeam = savedData ? JSON.parse(savedData) : [];
const poke      = savedTeam[editIndex];

// Variables per als Modals
let availableMoves = [];
let currentMoveSlot = null;

if (!poke) {
    alert("Error: No s'ha trobat el Pokémon.");
    window.location.href = "index.html";
}

// --- DOM ELEMENTS ---
const nicknameInput = document.getElementById("edit-nickname");
const speciesEl     = document.getElementById("edit-species");
const idEl      = document.getElementById("edit-id");
const spriteEl  = document.getElementById("edit-sprite");
const saveBtn   = document.getElementById("save-btn");
const cancelBtn = document.getElementById("cancel-btn");
const genderCircle = document.getElementById("gender-circle");

// Inputs Formuari
const abilitySelect = document.getElementById("edit-ability");
const natureSelect  = document.getElementById("edit-nature");
const itemInput     = document.getElementById("edit-item"); // Ara és readonly
const moveInputs    = [1, 2, 3, 4].map(i => document.getElementById(`move-${i}`));

// Modal Moviments
const moveModal = document.getElementById("move-picker-modal");
const moveSearchInput = document.getElementById("move-search-input");
const movesListContainer = document.getElementById("moves-list-container");
const closeMoveModalBtn = document.getElementById("close-move-modal");

// Modal Objectes (NOU)
const itemModal = document.getElementById("item-picker-modal");
const itemSearchInput = document.getElementById("item-search-input");
const itemsListContainer = document.getElementById("items-list-container");
const closeItemModalBtn = document.getElementById("close-item-modal");

// Navegació
const navPrev = document.getElementById('nav-prev');
const navNext = document.getElementById('nav-next');

const GENDER_STATES = [null, 'male', 'female']; // null=gris, male=blau, female=rosa
let currentGenderIndex = 0; // Per defecte 0 (gris)

/* ============================================================
   RENDERITZAT INICIAL
   ============================================================ */
// Omplim l'input amb el nickname (si en té) o el nom de l'espècie
nicknameInput.value = poke.nickname || poke.name.toUpperCase();

// Omplim l'etiqueta petita de sota amb el nom real
speciesEl.textContent = poke.name.toUpperCase();
idEl.textContent   = "#" + String(poke.pokedex_id).padStart(3, "0");
spriteEl.src       = poke.sprite_url;

/* ============================================================
   FUNCIONS DE DADES
   ============================================================ */
async function fetchAbilities(id) {
    try {
        const res = await fetch(`${API_BASE}/pokemon/${id}/abilities`);
        return res.ok ? await res.json() : [];
    } catch (e) { return []; }
}

async function fetchMoves(id) {
    try {
        const res = await fetch(`${API_BASE}/pokemon/${id}/moves`);
        return res.ok ? await res.json() : [];
    } catch (e) { return []; }
}

async function searchItems(query) {
    if (!query || query.length < 2) return [];
    try {
        const res = await fetch(`${API_BASE}/items/search?q=${query}`);
        return res.ok ? await res.json() : [];
    } catch (e) { return []; }
}

// --- Funció auxiliar per actualitzar el color del cercle ---
const updateGenderUI = (index) => {
    // 1. Traiem totes les classes de color antigues
    genderCircle.classList.remove('none', 'male', 'female');

    // 2. Apliquem lògica segons l'índex
    if (index === 0) {
        // ESTAT: GRIS (Sense gènere)
        genderCircle.classList.add('none');
        genderCircle.textContent = "";  // Buidem el símbol (o pots posar "-")
        genderCircle.title = "Sense gènere / Desconegut";
    }
    else if (index === 1) {
        // ESTAT: BLAU (Masculí)
        genderCircle.classList.add('male');
        genderCircle.textContent = "♂"; // Símbol Mart
        genderCircle.title = "Masculí";
    }
    else if (index === 2) {
        // ESTAT: ROSA (Femení)
        genderCircle.classList.add('female');
        genderCircle.textContent = "♀"; // Símbol Venus
        genderCircle.title = "Femení";
    }
};
/* ============================================================
   LÒGICA MODAL MOVIMENTS
   ============================================================ */
const openMovePicker = (slotIndex) => {
    currentMoveSlot = slotIndex;
    moveSearchInput.value = "";
    renderMoveList(availableMoves);
    moveModal.style.display = "block";
    moveSearchInput.focus();
};

const closeMovePicker = () => {
    moveModal.style.display = "none";
    currentMoveSlot = null;
};

const renderMoveList = (moves) => {
    movesListContainer.innerHTML = "";
    // Opció buida
    const empty = document.createElement("div");
    empty.className = "move-option";
    empty.style.color = "#ef4444";
    empty.textContent = "- Treure Moviment -";
    empty.onclick = () => selectMove("");
    movesListContainer.appendChild(empty);

    moves.forEach(m => {
        const div = document.createElement("div");
        div.className = "move-option";
        div.textContent = m.name.charAt(0).toUpperCase() + m.name.slice(1);
        div.onclick = () => selectMove(m.name);
        movesListContainer.appendChild(div);
    });
};

const selectMove = (moveName) => {
    if (currentMoveSlot !== null) {
        const displayValue = moveName ? moveName.charAt(0).toUpperCase() + moveName.slice(1) : "";
        moveInputs[currentMoveSlot].value = displayValue;
        moveInputs[currentMoveSlot].dataset.value = moveName;
    }
    closeMovePicker();
};

moveSearchInput.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = availableMoves.filter(m => m.name.toLowerCase().includes(term));
    renderMoveList(filtered);
});

moveInputs.forEach((inp, idx) => inp.addEventListener("click", () => openMovePicker(idx)));
closeMoveModalBtn.addEventListener("click", closeMovePicker);


/* ============================================================
   LÒGICA MODAL OBJECTES (ITEMS)
   ============================================================ */
const debounce = (func, delay) => {
    let t; return (...args) => { clearTimeout(t); t = setTimeout(() => func(...args), delay); };
};

// 1. Obrir Modal Item
const openItemPicker = () => {
    itemModal.style.display = "block";
    itemSearchInput.value = "";
    itemsListContainer.innerHTML = '<div style="padding:20px; text-align:center; color:#aaa;">Escriu per cercar objectes...</div>';
    itemSearchInput.focus();
};

// 2. Tancar Modal Item
const closeItemPicker = () => {
    itemModal.style.display = "none";
};

// 3. Pintar Llista Items
const renderItemList = (items) => {
    itemsListContainer.innerHTML = "";

    // Opció buida
    const empty = document.createElement("div");
    empty.className = "move-option"; // Reutilitzem estil
    empty.style.color = "#ef4444";
    empty.textContent = "- Treure Objecte -";
    empty.onclick = () => selectItem("");
    itemsListContainer.appendChild(empty);

    if (items.length === 0) {
        itemsListContainer.innerHTML += '<div style="padding:20px; text-align:center;">No s\'han trobat resultats</div>';
        return;
    }

    items.forEach(item => {
        const div = document.createElement("div");
        div.className = "move-option"; // Reutilitzem estil CSS
        div.innerHTML = `
            <span>${item.name}</span>
            <span style="font-size:10px; color:#aaa; margin-left:10px;">${item.category || ''}</span>
        `;
        div.onclick = () => selectItem(item.name);
        itemsListContainer.appendChild(div);
    });
};

// 4. Seleccionar Item
const selectItem = (itemName) => {
    itemInput.value = itemName; // Actualitzem l'input principal
    closeItemPicker();
};

// 5. Listener cerca Item (amb debounce)
itemSearchInput.addEventListener("input", debounce(async (e) => {
    const q = e.target.value.trim();
    if (q.length < 2) return;

    // Mostrem spinner o loading...
    itemsListContainer.innerHTML = '<div style="padding:20px; text-align:center;">Cercant...</div>';

    const items = await searchItems(q);
    renderItemList(items);
}, 300));

// Connectar Input i Botó Tancar
itemInput.addEventListener("click", openItemPicker);
closeItemModalBtn.addEventListener("click", closeItemPicker);


/* ============================================================
   CÀRREGA DE DADES (INICIALITZACIÓ)
   ============================================================ */
async function loadDetails() {

    // --- CLEAR INPUTS (Fix: Ensure fields are reset before loading) ---
    itemInput.value = "";
    // ------------------------------------------------------------------

    // Habilitats
    const abs = await fetchAbilities(poke.pokedex_id);
    abilitySelect.innerHTML = "";
    abs.forEach(a => {
        const name = a.ability ? a.ability.name : a.name;
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name.charAt(0).toUpperCase() + name.slice(1);
        abilitySelect.appendChild(opt);
    });
    if (poke.ability) abilitySelect.value = poke.ability;

    // Moviments (Pre-carregats per filtrar en local)
    const movesData = await fetchMoves(poke.pokedex_id);
    availableMoves = movesData.sort((a, b) => a.name.localeCompare(b.name));

    // Restaurar Inputs Moviments
    moveInputs.forEach((inp, idx) => {
        if (poke.moves && poke.moves[idx]) {
            const mName = poke.moves[idx];
            inp.value = mName.charAt(0).toUpperCase() + mName.slice(1);
            inp.dataset.value = mName;
        } else {
            inp.value = "";
        }
    });

    // Naturaleses
    natureSelect.innerHTML = "";
    NATURES.forEach(n => {
        const opt = document.createElement("option");
        opt.value = n; opt.textContent = n;
        natureSelect.appendChild(opt);
    });
    if (poke.nature) natureSelect.value = poke.nature;

    // Restaurar Objecte
    if (poke.item) itemInput.value = poke.item;

    // Comprovem si ja té gènere guardat
        if (poke.gender === 'male') {
            currentGenderIndex = 1;
        } else if (poke.gender === 'female') {
            currentGenderIndex = 2;
        } else {
            currentGenderIndex = 0; // Si és null o no existeix
        }
        // Actualitzem el cercle visualment
        updateGenderUI(currentGenderIndex);
}

/* ============================================================
   NAVEGACIÓ I GUARDAR
   ============================================================ */
const setupNavCard = (el, idx) => {
    if (idx >= 0 && idx < 6 && savedTeam[idx]) {
        el.classList.remove('hidden');
        el.querySelector('.nav-sprite').src = savedTeam[idx].sprite_url;
        el.querySelector('.nav-name').textContent = savedTeam[idx].name.toUpperCase();
        el.onclick = () => { localStorage.setItem("editIndex", idx); window.location.reload(); };
    } else { el.classList.add('hidden'); }
};
setupNavCard(navPrev, editIndex - 1);
setupNavCard(navNext, editIndex + 1);

saveBtn.addEventListener("click", () => {
    // 1. Guardem el Nickname
    // Si l'usuari ho deixa buit, fem servir el nom original
    poke.nickname = nicknameInput.value.trim() || poke.name;

    poke.ability = abilitySelect.value;
    poke.nature  = natureSelect.value;
    poke.item    = itemInput.value.trim();
    poke.moves   = moveInputs.map(i => i.dataset.value || i.value.toLowerCase()).filter(v => v !== "");
    poke.gender = GENDER_STATES[currentGenderIndex];

    savedTeam[editIndex] = poke;
    localStorage.setItem("pokeBuilder_team", JSON.stringify(savedTeam));
    window.location.href = "index.html";
});

cancelBtn.addEventListener("click", () => window.location.href = "index.html");

genderCircle.addEventListener("click", () => {
    // Màgia matemàtica per ciclar: (0 + 1) % 3 = 1; (1 + 1) % 3 = 2; (2 + 1) % 3 = 0
    currentGenderIndex = (currentGenderIndex + 1) % 3;
    updateGenderUI(currentGenderIndex);
});

loadDetails();