document.addEventListener("DOMContentLoaded", () => {

    const mockPokemonData = [
        { id: 1, name: "Bulbasaur" },
        { id: 4, name: "Charmander" },
        { id: 7, name: "Squirtle" },
        { id: 25, name: "Pikachu" },
        { id: 94, name: "Gengar" },
        { id: 143, name: "Snorlax" },
        { id: 6, name: "Charizard" },
        { id: 130, name: "Gyarados" }
    ];

    const getSpriteUrl = (id) => {
        return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png`;
    };

    // --- Seleccionar elements (MODALS) ---
    const searchModal = document.getElementById("pokemon-modal");
    const searchCloseBtn = searchModal.querySelector(".close-btn");

    const recommendModal = document.getElementById("recommend-modal");
    const recommendCloseBtn = recommendModal.querySelector(".close-btn");
    const recommendBtn = document.getElementById("recommend-btn");
    const recommendSprite = document.getElementById("recommend-sprite");
    const recommendText = document.getElementById("recommend-text");

    // --- Seleccionar altres elements ---
    const teamSlots = document.querySelectorAll(".team-slot");
    const searchBar = document.getElementById("search-bar");
    const pokemonListUl = document.getElementById("pokemon-list");

    let currentSlotBeingEdited = null;

    const updateRecommendButtonState = () => {
        const filledSlots = document.querySelectorAll(".team-slot.slot-filled").length;

        if (filledSlots === 5) {
            recommendBtn.disabled = false;
        } else {
            recommendBtn.disabled = true;
        }
    };

    const resetSlot = (slotElement) => {
        slotElement.innerHTML = "<span>+</span>";
        slotElement.classList.remove("slot-filled");
        updateRecommendButtonState();
    };

    const openSearchModal = (slotElement) => {
        currentSlotBeingEdited = slotElement;
        searchModal.style.display = "block";
        searchBar.value = "";
        populateList(mockPokemonData);
        searchBar.focus();
    };

    const closeSearchModal = () => {
        searchModal.style.display = "none";
        currentSlotBeingEdited = null;
    };

    // --- CLAU: LÒGICA DE RECOMANACIÓ ACTUALITZADA ---
    const openRecommendModal = () => {

        // 1. Obtenim els noms dels Pokémon que ja tenim a l'equip
        const filledSlots = document.querySelectorAll(".team-slot.slot-filled span");
        // (Convertim a Array, agafem el text, i el passem a minúscules)
        const teamNames = Array.from(filledSlots).map(span => span.textContent.toLowerCase());

        // 2. Definim la nostra recomanació principal (Pikachu)
        const pikachu = { id: 25, name: "Pikachu" };
        let recommendedPokemon; // Aquesta serà la nostra recomanació final

        // 3. Comprovem si Pikachu ja és a l'equip
        if (!teamNames.includes(pikachu.name.toLowerCase())) {

            // Si NO hi és, el recomanem
            recommendedPokemon = pikachu;

        } else {

            // Si SÍ hi és, busquem a la llista general (mockPokemonData)
            // el PRIMER Pokémon que NO estigui a la llista 'teamNames'.
            recommendedPokemon = mockPokemonData.find(pokemon => {
                return !teamNames.includes(pokemon.name.toLowerCase());
            });

            // (Si no en troba cap (cas estrany), tornem a posar Pikachu per defecte)
            if (!recommendedPokemon) {
                recommendedPokemon = pikachu;
            }
        }

        // 4. Omplim el modal amb la recomanació que hem triat
        recommendSprite.src = getSpriteUrl(recommendedPokemon.id);
        recommendSprite.alt = recommendedPokemon.name;
        recommendText.textContent = `Et recomanem afegir un ${recommendedPokemon.name}!`;

        // 5. Obrim el modal
        recommendModal.style.display = "block";
    };

    const closeRecommendModal = () => {
        recommendModal.style.display = "none";
    };

    const populateList = (pokemons) => {
        pokemonListUl.innerHTML = "";

        pokemons.forEach(pokemon => {
            const li = document.createElement("li");

            const spriteImg = document.createElement("img");
            spriteImg.src = getSpriteUrl(pokemon.id);
            spriteImg.alt = pokemon.name;
            li.appendChild(spriteImg);

            const nameSpan = document.createElement("span");
            nameSpan.textContent = pokemon.name;
            li.appendChild(nameSpan);

            li.addEventListener("click", () => {
                if (currentSlotBeingEdited) {
                    const slot = currentSlotBeingEdited;
                    const spriteUrl = getSpriteUrl(pokemon.id);

                    slot.innerHTML = `
                        <img src="${spriteUrl}" alt="${pokemon.name}" class="slot-sprite">
                        <span>${pokemon.name}</span>
                        <div class="remove-btn">×</div> 
                    `;

                    slot.classList.add("slot-filled");

                    const removeBtn = slot.querySelector(".remove-btn");
                    removeBtn.addEventListener("click", (e) => {
                        e.stopPropagation();
                        resetSlot(slot);
                    });

                    updateRecommendButtonState();
                }
                closeSearchModal();
            });

            pokemonListUl.appendChild(li);
        });
    };

    searchBar.addEventListener("keyup", (e) => {
        const query = e.target.value.toLowerCase();
        const filteredPokemons = mockPokemonData.filter(pokemon =>
            pokemon.name.toLowerCase().includes(query)
        );
        populateList(filteredPokemons);
    });

    teamSlots.forEach(slot => {
        slot.addEventListener("click", (e) => {
            openSearchModal(e.currentTarget);
        });
    });

    // Listeners del Modal de Cerca
    searchCloseBtn.addEventListener("click", closeSearchModal);

    // Listeners del Modal de Recomanació
    recommendBtn.addEventListener("click", openRecommendModal);
    recommendCloseBtn.addEventListener("click", closeRecommendModal);

    // Listeners de la finestra (per tancar clicant fora)
    window.addEventListener("click", (e) => {
        if (e.target === searchModal) {
            closeSearchModal();
        }
        if (e.target === recommendModal) {
            closeRecommendModal();
        }
    });

    // Estat inicial del botó
    updateRecommendButtonState();
});